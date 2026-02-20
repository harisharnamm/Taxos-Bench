import json
import os
import re
import random
import hashlib
import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Callable
from prolog_manager import PrologManager

# --- Configuration ---
SARA_CONFIG_FILE = "sara_sections.yaml"

# --- Data Models (Reused) ---

@dataclass
class Subsection:
    subsection_id: str
    citation: str
    text: str
    html: str

@dataclass
class IRCSection:
    title: str
    subtitle: str
    chapter: str
    section_number: str
    citation: str
    heading: str
    subsections: List[Subsection]

@dataclass
class TaxBracket:
    rate: float
    min_income: float
    max_income: float

@dataclass
class TaxBracketRule:
    section_code: str
    year: int
    filer_status: str
    brackets: List[TaxBracket]
    citation: str

@dataclass
class ClassificationRule:
    section_code: str
    category: str
    item_name: str
    citation: str

@dataclass
class AGILimitRule:
    section_code: str
    percentage: float
    description: str
    citation: str

@dataclass
class BasisAdjustmentRule:
    section_code: str
    years_required: int
    percentage: float
    description: str
    citation: str

@dataclass
class PassiveLossRule:
    section_code: str
    description: str
    citation: str

@dataclass
class ExclusionRule:
    section_code: str
    amount_single: float
    amount_joint: float
    ownership_years: int
    use_years: int
    citation: str

@dataclass
class QBIRule:
    section_code: str
    percentage: float
    citation: str

# --- Loader Functions ---

def load_section(path: str) -> Optional[IRCSection]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            return None

        subsections = []
        for sub in data.get("subsections", []):
            subsections.append(Subsection(
                subsection_id=sub.get("subsection_id", ""),
                citation=sub.get("citation", ""),
                text=sub.get("text", ""),
                html=sub.get("html", "")
            ))

        return IRCSection(
            title=data.get("title", ""),
            subtitle=data.get("subtitle", ""),
            chapter=data.get("chapter", ""),
            section_number=data.get("section_number", ""),
            citation=data.get("citation", ""),
            heading=data.get("heading", ""),
            subsections=subsections
        )
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None

def iter_sections_in_dir(directory: str) -> List[IRCSection]:
    sections = []
    if not os.path.exists(directory):
        return sections

    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("section_") and file.endswith(".json"):
                full_path = os.path.join(root, file)
                sec = load_section(full_path)
                if sec:
                    sections.append(sec)
    return sections

# --- Rule Detection Helpers (Reused) ---

def detect_tax_brackets(sec: IRCSection) -> List[TaxBracketRule]:
    rules = []
    if sec.section_number == "1":
        brackets = [
            TaxBracket(0.10, 0, 11600),
            TaxBracket(0.12, 11600, 47150),
            TaxBracket(0.22, 47150, 100525),
            TaxBracket(0.24, 100525, 191950),
            TaxBracket(0.32, 191950, 243725),
            TaxBracket(0.35, 243725, 609350),
            TaxBracket(0.37, 609350, float('inf'))
        ]
        rules.append(TaxBracketRule("1", 2024, "Single", brackets, "I.R.C. § 1(j)"))
    return rules

def detect_classification_rules(sec: IRCSection) -> List[ClassificationRule]:
    rules = []
    if sec.section_number == "61":
        inclusions = ["Compensation for services", "Gross income derived from business", "Gains derived from dealings in property", "Interest", "Rents", "Royalties", "Dividends", "Alimony", "Annuities", "Income from life insurance contracts", "Pensions", "Income from discharge of indebtedness", "Distributive share of partnership gross income", "Income in respect of a decedent", "Income from an interest in an estate or trust"]
        for item in inclusions:
            rules.append(ClassificationRule("61", "Inclusion", item, "I.R.C. § 61(a)"))
    elif sec.section_number == "162":
        deductions = ["Salaries or other compensation", "Traveling expenses", "Rentals"]
        for item in deductions:
            rules.append(ClassificationRule("162", "Deduction", item, "I.R.C. § 162(a)"))
        nondeductible = ["Fines and penalties", "Illegal bribes", "Lobbying expenses"]
        for item in nondeductible:
            rules.append(ClassificationRule("162", "Nondeductible", item, "I.R.C. § 162(c)/(f)/(e)"))
    elif sec.section_number == "163":
        rules.append(ClassificationRule("163", "Deduction", "Qualified residence interest", "I.R.C. § 163(h)(3)"))
        rules.append(ClassificationRule("163", "Deduction", "Investment interest", "I.R.C. § 163(d)"))
        rules.append(ClassificationRule("163", "Nondeductible", "Personal interest", "I.R.C. § 163(h)(1)"))
    return rules

def detect_exclusion_rules_121(sec: IRCSection) -> List[ExclusionRule]:
    rules = []
    if sec.section_number == "121":
        rules.append(ExclusionRule("121", 250000, 500000, 2, 2, "I.R.C. § 121(a)/(b)"))
    return rules

def detect_qbi_rules_199A(sec: IRCSection) -> List[QBIRule]:
    rules = []
    if sec.section_number == "199A":
        rules.append(QBIRule("199A", 0.20, "I.R.C. § 199A(a)"))
    return rules

def detect_agi_limit_rules(sec: IRCSection) -> List[AGILimitRule]:
    rules = []
    if sec.section_number == "170":
        for sub in sec.subsections:
            text = sub.text.lower()
            if "percent" in text and ("contribution base" in text or "adjusted gross income" in text):
                match = re.search(r"(\d+)\s+percent", text)
                if match:
                    pct = float(match.group(1)) / 100.0
                    rules.append(AGILimitRule(sec.section_number, pct, f"Limitation of {match.group(1)}% of AGI", sub.citation))
    return rules

def detect_basis_adjustment_rules_1400Z2(sec: IRCSection) -> List[BasisAdjustmentRule]:
    rules = []
    seen_years = set()
    if sec.section_number == "1400Z-2":
        for sub in sec.subsections:
            text = sub.text.lower()
            if "5 years" in text and "10 percent" in text and "basis" in text and "increased" in text:
                if 5 not in seen_years:
                    rules.append(BasisAdjustmentRule(sec.section_number, 5, 0.10, "Basis increase for 5-year holding", sub.citation))
                    seen_years.add(5)
            if "7 years" in text and "5 percent" in text and "basis" in text and "increased" in text:
                if 7 not in seen_years:
                    rules.append(BasisAdjustmentRule(sec.section_number, 7, 0.05, "Additional basis increase for 7-year holding", sub.citation))
                    seen_years.add(7)
    return rules

def detect_passive_loss_stack(sec: IRCSection) -> List[PassiveLossRule]:
    rules = []
    if sec.section_number == "469":
        for sub in sec.subsections:
            if "(a)" in sub.subsection_id:
                rules.append(PassiveLossRule(sec.section_number, "Passive activity loss disallowed", sub.citation))
                break
    return rules

# --- MCQ Helpers (Reused) ---

def make_mcq_from_numeric_answer(correct_value: float, distractors: List[float], fmt: str = "${:,.2f}") -> Tuple[List[str], int]:
    correct_str = fmt.format(correct_value)
    distractor_strs = [fmt.format(d) for d in distractors]
    options = set(distractor_strs)
    options.add(correct_str)
    choices = list(options)
    random.shuffle(choices)
    correct_index = choices.index(correct_str)
    return choices, correct_index

def calculate_tax(income: float, brackets: List[TaxBracket]) -> float:
    tax = 0.0
    for b in brackets:
        if income > b.min_income:
            taxable_in_bracket = min(income, b.max_income) - b.min_income
            tax += taxable_in_bracket * b.rate
        else:
            break
    return tax

def build_170_mcq(deduction: float, contribution: float, limit: float) -> Tuple[List[str], int]:
    distractors = [contribution, limit, max(0, contribution - limit), 0.0]
    distractors = [d for d in distractors if abs(d - deduction) > 0.01]
    return make_mcq_from_numeric_answer(deduction, distractors)

def build_469_mcq(allowed: float, passive_loss: float, passive_income: float) -> Tuple[List[str], int]:
    suspended = passive_loss - allowed
    distractors = [passive_loss, passive_income, suspended, passive_loss + passive_income]
    distractors = [d for d in distractors if abs(d - allowed) > 0.01]
    return make_mcq_from_numeric_answer(allowed, distractors)

def build_1400Z2_mcq(adjusted_basis: float, deferred_gain: float, initial_basis: float) -> Tuple[List[str], int]:
    distractors = [initial_basis, deferred_gain, deferred_gain * 0.10, deferred_gain * 0.85]
    distractors = [d for d in distractors if abs(d - adjusted_basis) > 0.01]
    return make_mcq_from_numeric_answer(adjusted_basis, distractors)

# --- Specific Section Generators (Reused) ---

def generate_section_1_questions(sec: IRCSection, num_variations: int) -> List[Dict]:
    questions = []
    rules = detect_tax_brackets(sec)
    if not rules: return []
    rule = rules[0]
    entities = ["Alice", "Bob", "Charlie", "Diana"]
    for _ in range(num_variations):
        entity = random.choice(entities)
        income = round(random.uniform(30000, 300000), 2)
        tax = calculate_tax(income, rule.brackets)
        scenario = f"In {rule.year}, {entity}, a single filer, has a taxable income of ${income:,.2f}."
        question = f"Calculate {entity}'s tax liability using the standard progressive tax brackets under {rule.citation}."
        marginal_rate = 0.0
        for b in rule.brackets:
            if income > b.min_income: marginal_rate = b.rate
        distractors = [income * marginal_rate, income * 0.22, tax * 0.8, tax * 1.2]
        distractors = [d for d in distractors if abs(d - tax) > 1.0]
        choices, correct_index = make_mcq_from_numeric_answer(tax, distractors)
        questions.append({
            "id": hashlib.md5((scenario + question).encode()).hexdigest()[:12],
            "section": sec.section_number,
            "citation": rule.citation,
            "type": "Calculation - Tax Liability",
            "scenario": scenario,
            "question": question,
            "difficulty": 2,
            "choices": choices,
            "correct_choice_index": correct_index,
            "answer_explanation": f"Tax is calculated progressively. For income ${income:,.2f}, the tax is ${tax:,.2f}.",
            "reasoning": "Applied progressive tax brackets.",
            "source_rules": [rule.citation]
        })
    return questions

def generate_section_61_questions(sec: IRCSection, num_variations: int) -> List[Dict]:
    questions = []
    items_pool = [("Wages", True), ("Interest on Bank Account", True), ("Dividends", True), ("Gift from Parents", False), ("Loan Proceeds", False), ("Return of Capital", False), ("Gambling Winnings", True), ("Life Insurance Proceeds (Death)", False)]
    entities = ["Alice", "Bob", "Charlie"]
    for _ in range(num_variations):
        entity = random.choice(entities)
        selected_items = random.sample(items_pool, k=random.randint(3, 5))
        scenario_parts = []
        gross_income = 0.0
        all_receipts = 0.0
        for name, is_included in selected_items:
            amount = round(random.uniform(1000, 50000), 2)
            scenario_parts.append(f"{name}: ${amount:,.2f}")
            all_receipts += amount
            if is_included: gross_income += amount
        scenario = f"{entity} received the following amounts during the year: " + ", ".join(scenario_parts) + "."
        question = f"Calculate {entity}'s gross income under I.R.C. § 61."
        distractors = [all_receipts, 0.0, gross_income * 0.5, all_receipts - gross_income]
        distractors = [d for d in distractors if abs(d - gross_income) > 0.01]
        choices, correct_index = make_mcq_from_numeric_answer(gross_income, distractors)
        questions.append({
            "id": hashlib.md5((scenario + question).encode()).hexdigest()[:12],
            "section": sec.section_number,
            "citation": "I.R.C. § 61(a)",
            "type": "Calculation - Gross Income",
            "scenario": scenario,
            "question": question,
            "difficulty": 2,
            "choices": choices,
            "correct_choice_index": correct_index,
            "answer_explanation": f"Gross income includes all income from whatever source derived, unless excluded. Total: ${gross_income:,.2f}.",
            "reasoning": "Summed included items, ignored excluded items.",
            "source_rules": ["I.R.C. § 61(a)"]
        })
    return questions

def generate_section_162_questions(sec: IRCSection, num_variations: int) -> List[Dict]:
    questions = []
    items_pool = [("Office Rent", True), ("Employee Salaries", True), ("Office Supplies", True), ("Traffic Fines", False), ("Political Contributions", False), ("Personal Lunch", False), ("Bribes", False)]
    entities = ["XYZ Corp", "ABC LLC"]
    for _ in range(num_variations):
        entity = random.choice(entities)
        selected_items = random.sample(items_pool, k=random.randint(3, 5))
        scenario_parts = []
        deductible = 0.0
        total_expenses = 0.0
        for name, is_deductible in selected_items:
            amount = round(random.uniform(500, 10000), 2)
            scenario_parts.append(f"{name}: ${amount:,.2f}")
            total_expenses += amount
            if is_deductible: deductible += amount
        scenario = f"{entity} incurred the following expenses: " + ", ".join(scenario_parts) + "."
        question = f"Calculate the total deductible trade or business expenses under I.R.C. § 162."
        distractors = [total_expenses, deductible * 0.5, total_expenses - deductible]
        distractors = [d for d in distractors if abs(d - deductible) > 0.01]
        choices, correct_index = make_mcq_from_numeric_answer(deductible, distractors)
        questions.append({
            "id": hashlib.md5((scenario + question).encode()).hexdigest()[:12],
            "section": sec.section_number,
            "citation": "I.R.C. § 162(a)",
            "type": "Calculation - Business Expenses",
            "scenario": scenario,
            "question": question,
            "difficulty": 2,
            "choices": choices,
            "correct_choice_index": correct_index,
            "answer_explanation": f"Only ordinary and necessary business expenses are deductible. Total: ${deductible:,.2f}.",
            "reasoning": "Summed deductible items.",
            "source_rules": ["I.R.C. § 162(a)"]
        })
    return questions

def generate_section_163_questions(sec: IRCSection, num_variations: int) -> List[Dict]:
    questions = []
    items_pool = [("Mortgage Interest on Main Home", True), ("Investment Interest (within limits)", True), ("Credit Card Interest", False), ("Car Loan Interest (Personal)", False), ("Student Loan Interest (assume deductible)", True)]
    entities = ["Alice", "Bob"]
    for _ in range(num_variations):
        entity = random.choice(entities)
        selected_items = random.sample(items_pool, k=random.randint(3, 4))
        scenario_parts = []
        deductible = 0.0
        total = 0.0
        for name, is_deductible in selected_items:
            amount = round(random.uniform(100, 5000), 2)
            scenario_parts.append(f"{name}: ${amount:,.2f}")
            total += amount
            if is_deductible: deductible += amount
        scenario = f"{entity} paid the following interest amounts: " + ", ".join(scenario_parts) + "."
        question = f"Calculate the total deductible interest under I.R.C. § 163."
        distractors = [total, 0.0, total - deductible]
        distractors = [d for d in distractors if abs(d - deductible) > 0.01]
        choices, correct_index = make_mcq_from_numeric_answer(deductible, distractors)
        questions.append({
            "id": hashlib.md5((scenario + question).encode()).hexdigest()[:12],
            "section": sec.section_number,
            "citation": "I.R.C. § 163(h)",
            "type": "Calculation - Interest Deduction",
            "scenario": scenario,
            "question": question,
            "difficulty": 2,
            "choices": choices,
            "correct_choice_index": correct_index,
            "answer_explanation": f"Personal interest is generally not deductible. Total: ${deductible:,.2f}.",
            "reasoning": "Summed deductible interest types.",
            "source_rules": ["I.R.C. § 163(h)"]
        })
    return questions

def generate_section_121_questions(sec: IRCSection, num_variations: int) -> List[Dict]:
    questions = []
    rules = detect_exclusion_rules_121(sec)
    if not rules: return []
    rule = rules[0]
    entities = ["Alice", "Bob"]
    for _ in range(num_variations):
        entity = random.choice(entities)
        purchase_price = round(random.uniform(100000, 300000), 2)
        sale_price = round(purchase_price * random.uniform(1.2, 2.5), 2)
        gain = sale_price - purchase_price
        years_lived = 3
        exclusion = rule.amount_single
        taxable_gain = max(0, gain - exclusion)
        scenario = f"{entity} sold their principal residence for ${sale_price:,.2f}. They purchased it for ${purchase_price:,.2f} and lived in it for {years_lived} years out of the last 5 years."
        question = f"Calculate the taxable gain recognized on the sale under I.R.C. § 121."
        distractors = [gain, 0.0, gain - (exclusion / 2)]
        distractors = [d for d in distractors if abs(d - taxable_gain) > 0.01]
        choices, correct_index = make_mcq_from_numeric_answer(taxable_gain, distractors)
        questions.append({
            "id": hashlib.md5((scenario + question).encode()).hexdigest()[:12],
            "section": sec.section_number,
            "citation": rule.citation,
            "type": "Calculation - Residence Exclusion",
            "scenario": scenario,
            "question": question,
            "difficulty": 3,
            "choices": choices,
            "correct_choice_index": correct_index,
            "answer_explanation": f"Gain is ${gain:,.2f}. Exclusion is ${exclusion:,.2f}. Taxable: ${taxable_gain:,.2f}.",
            "reasoning": "Applied Section 121 exclusion.",
            "source_rules": [rule.citation]
        })
    return questions

def generate_section_199A_questions(sec: IRCSection, num_variations: int) -> List[Dict]:
    questions = []
    rules = detect_qbi_rules_199A(sec)
    if not rules: return []
    rule = rules[0]
    entities = ["Evan", "Frank"]
    for _ in range(num_variations):
        entity = random.choice(entities)
        qbi = round(random.uniform(50000, 150000), 2)
        deduction = qbi * rule.percentage
        scenario = f"{entity} has Qualified Business Income (QBI) of ${qbi:,.2f} from a sole proprietorship. {entity}'s taxable income is below the threshold amount."
        question = f"Calculate the QBI deduction under I.R.C. § 199A."
        distractors = [qbi, qbi * 0.5, 0.0, qbi * 0.1]
        distractors = [d for d in distractors if abs(d - deduction) > 0.01]
        choices, correct_index = make_mcq_from_numeric_answer(deduction, distractors)
        questions.append({
            "id": hashlib.md5((scenario + question).encode()).hexdigest()[:12],
            "section": sec.section_number,
            "citation": rule.citation,
            "type": "Calculation - QBI Deduction",
            "scenario": scenario,
            "question": question,
            "difficulty": 3,
            "choices": choices,
            "correct_choice_index": correct_index,
            "answer_explanation": f"The deduction is generally 20% of QBI. Deduction: ${deduction:,.2f}.",
            "reasoning": "Applied 20% rate to QBI.",
            "source_rules": [rule.citation]
        })
    return questions

def generate_section_170_questions(sec: IRCSection, num_variations: int) -> List[Dict]:
    questions = []
    entities = ["Alice", "Bob", "Charlie", "Diana", "Evan", "Frank", "Grace", "Heidi"]
    years = [2023, 2024, 2025]
    rules = detect_agi_limit_rules(sec)
    if not rules: return []
    valid_rules = [r for r in rules if r.percentage in [0.5, 0.6]]
    if not valid_rules: valid_rules = rules
    for _ in range(num_variations):
        rule = random.choice(valid_rules)
        entity = random.choice(entities)
        year = random.choice(years)
        agi = round(random.uniform(50000, 200000), 2)
        limit_amount = agi * rule.percentage
        contribution = round(limit_amount * random.uniform(0.8, 1.5), 2)
        allowed = min(contribution, limit_amount)
        scenario = f"In {year}, {entity} has an Adjusted Gross Income (AGI) of ${agi:,.2f}. {entity} makes a charitable contribution of ${contribution:,.2f} in cash to a public charity. Under {rule.citation}, the deduction is limited to {int(rule.percentage*100)}% of the contribution base."
        question = f"Calculate the allowable charitable deduction for {year}."
        choices, correct_index = build_170_mcq(allowed, contribution, limit_amount)
        questions.append({
            "id": hashlib.md5((scenario + question).encode()).hexdigest()[:12],
            "section": sec.section_number,
            "citation": rule.citation,
            "type": "Complex - Charitable Contribution Limit",
            "scenario": scenario,
            "question": question,
            "difficulty": 3,
            "choices": choices,
            "correct_choice_index": correct_index,
            "answer_explanation": f"The deduction is limited to {int(rule.percentage*100)}% of AGI (${limit_amount:,.2f}). Allowable: ${allowed:,.2f}.",
            "reasoning": "Calculated limit and compared to contribution.",
            "source_rules": [rule.citation]
        })
    return questions

def generate_section_469_questions(sec: IRCSection, num_variations: int) -> List[Dict]:
    questions = []
    entities = ["Alice", "Bob", "Charlie", "Diana"]
    years = [2023, 2024, 2025]
    rules = detect_passive_loss_stack(sec)
    if not rules: return []
    rule = rules[0]
    for _ in range(num_variations):
        entity = random.choice(entities)
        year = random.choice(years)
        passive_activity_loss = round(random.uniform(20000, 50000), 2)
        passive_activity_income = round(random.uniform(0, 30000), 2)
        wages = round(random.uniform(60000, 120000), 2)
        allowed_loss = min(passive_activity_loss, passive_activity_income)
        scenario = f"In {year}, {entity} has wages of ${wages:,.2f}. {entity} also has an interest in a passive activity which generated a loss of ${passive_activity_loss:,.2f} for the year. {entity} has passive income from another source of ${passive_activity_income:,.2f}."
        question = f"Calculate the amount of the passive activity loss that is deductible in {year} under {rule.citation}."
        choices, correct_index = build_469_mcq(allowed_loss, passive_activity_loss, passive_activity_income)
        questions.append({
            "id": hashlib.md5((scenario + question).encode()).hexdigest()[:12],
            "section": sec.section_number,
            "citation": rule.citation,
            "type": "Complex - Passive Activity Loss",
            "scenario": scenario,
            "question": question,
            "difficulty": 3,
            "choices": choices,
            "correct_choice_index": correct_index,
            "answer_explanation": f"Passive losses are limited to passive income. Deductible: ${allowed_loss:,.2f}.",
            "reasoning": "Limited passive loss to passive income.",
            "source_rules": [rule.citation]
        })
    return questions

def generate_section_1400Z2_questions(sec: IRCSection, num_variations: int) -> List[Dict]:
    questions = []
    entities = ["Grace", "Heidi"]
    rules = detect_basis_adjustment_rules_1400Z2(sec)
    if not rules: return []
    rules.sort(key=lambda x: x.years_required)
    for _ in range(num_variations):
        entity = random.choice(entities)
        year_invested = 2019
        deferred_gain = round(random.uniform(100000, 500000), 2)
        holding_period = 7
        applicable_rules = [r for r in rules if r.years_required <= holding_period]
        total_pct_increase = sum(r.percentage for r in applicable_rules)
        basis_increase = deferred_gain * total_pct_increase
        initial_basis = 0
        adjusted_basis = initial_basis + basis_increase
        scenario = f"In {year_invested}, {entity} realized a capital gain of ${deferred_gain:,.2f} and invested the entire amount into a Qualified Opportunity Fund (QOF). {entity} holds the QOF investment for {holding_period} years."
        question = f"Calculate {entity}'s adjusted basis in the QOF investment after the {holding_period}-year holding period."
        choices, correct_index = build_1400Z2_mcq(adjusted_basis, deferred_gain, initial_basis)
        questions.append({
            "id": hashlib.md5((scenario + question).encode()).hexdigest()[:12],
            "section": sec.section_number,
            "citation": applicable_rules[-1].citation if applicable_rules else sec.citation,
            "type": "Complex - Opportunity Zone Basis Adjustment",
            "scenario": scenario,
            "question": question,
            "difficulty": 4,
            "choices": choices,
            "correct_choice_index": correct_index,
            "answer_explanation": f"The basis is increased by {int(total_pct_increase*100)}% of the deferred gain. Adjusted Basis: ${adjusted_basis:,.2f}.",
            "reasoning": "Applied basis adjustment rules.",
            "source_rules": [r.citation for r in applicable_rules]
        })
    return questions

# --- Generic Generator ---

def generate_generic_numeric_questions_from_section(sec: IRCSection, num_variations: int) -> List[Dict]:
    questions = []
    # Look for dollar amounts or percentages in text
    # Regex for "$X,XXX" or "X percent"
    
    dollar_pattern = re.compile(r'\$(\d{1,3}(?:,\d{3})*)')
    percent_pattern = re.compile(r'(\d+(?:\.\d+)?)\s+percent')
    
    potential_facts = []
    
    for sub in sec.subsections:
        text = sub.text
        dollars = dollar_pattern.findall(text)
        percents = percent_pattern.findall(text)
        
        if dollars:
            for d in dollars:
                val = float(d.replace(',', ''))
                if val > 0:
                    potential_facts.append({
                        "type": "dollar",
                        "value": val,
                        "citation": sub.citation,
                        "context": text[:100] + "..."
                    })
        
        if percents:
            for p in percents:
                val = float(p)
                if val > 0 and val <= 100:
                    potential_facts.append({
                        "type": "percent",
                        "value": val,
                        "citation": sub.citation,
                        "context": text[:100] + "..."
                    })

    if not potential_facts:
        return []

    for _ in range(num_variations):
        fact = random.choice(potential_facts)
        
        if fact['type'] == 'dollar':
            scenario = f"A specific limitation or amount in {fact['citation']} is discussed as follows: '{fact['context']}'."
            question = f"What is the dollar amount specified in {fact['citation']}?"
            
            distractors = [
                fact['value'] * 1.1,
                fact['value'] * 0.9,
                fact['value'] * 0.5,
                fact['value'] * 2.0
            ]
            choices, correct_index = make_mcq_from_numeric_answer(fact['value'], distractors)
            
            questions.append({
                "id": hashlib.md5((scenario + question).encode()).hexdigest()[:12],
                "section": sec.section_number,
                "citation": fact['citation'],
                "type": "Recall - Numeric",
                "scenario": scenario,
                "question": question,
                "difficulty": 1,
                "choices": choices,
                "correct_choice_index": correct_index,
                "answer_explanation": f"The text specifies ${fact['value']:,.2f}.",
                "reasoning": "Direct recall from statute text.",
                "source_rules": [fact['citation']]
            })
            
        elif fact['type'] == 'percent':
            scenario = f"A percentage limitation or rate in {fact['citation']} is discussed as follows: '{fact['context']}'."
            question = f"What is the percentage specified in {fact['citation']}?"
            
            distractors = [
                fact['value'] + 10,
                max(0, fact['value'] - 10),
                100 - fact['value'],
                fact['value'] * 1.5
            ]
            choices, correct_index = make_mcq_from_numeric_answer(fact['value'], distractors, fmt="{:.1f}%")
            
            questions.append({
                "id": hashlib.md5((scenario + question).encode()).hexdigest()[:12],
                "section": sec.section_number,
                "citation": fact['citation'],
                "type": "Recall - Percentage",
                "scenario": scenario,
                "question": question,
                "difficulty": 1,
                "choices": choices,
                "correct_choice_index": correct_index,
                "answer_explanation": f"The text specifies {fact['value']}%.",
                "reasoning": "Direct recall from statute text.",
                "source_rules": [fact['citation']]
            })

    return questions

# --- SARA Generator ---

def generate_sara_cases_for_section(sec: IRCSection, config: Dict, num_cases: int = 3) -> List[Dict]:
    cases = []
    section_id = sec.section_number
    
    if section_id not in config['sections'] or not config['sections'][section_id]['enabled']:
        return []
        
    predicate = config['sections'][section_id]['predicate']
    pm = PrologManager()
    
    # Logic for specific supported SARA sections
    if section_id == "121":
        # Generate cases for Principal Residence Exclusion
        for _ in range(num_cases):
            pm.clear_facts()
            
            # Randomize facts
            owned_years = random.randint(1, 5)
            lived_years = random.randint(1, 5)
            
            pm.add_fact(f"owned(alice, {owned_years}, 5)")
            pm.add_fact(f"lived_in(alice, {lived_years}, 5)")
            
            # Query
            query = f"{predicate}(alice)"
            result = pm.run_query(query)
            
            scenario = f"Alice sold her home. She owned it for {owned_years} years and lived in it for {lived_years} years out of the last 5 years."
            question = "Does Alice qualify for the Section 121 exclusion?"
            
            answer = "Entailment" if result['success'] else "Contradiction"
            
            cases.append({
                "id": hashlib.md5((scenario + question).encode()).hexdigest()[:12],
                "text": scenario,
                "question": question,
                "facts": "\n".join(pm.facts),
                "query": query,
                "answer": answer,
                "gold_truth_subsection": "I.R.C. § 121(a)",
                "source_rules": ["I.R.C. § 121(a)"]
            })
            
    elif section_id == "170":
        # Generate cases for Charitable Contribution
        for _ in range(num_cases):
            pm.clear_facts()
            
            agi = 100000
            limit_pct = 0.5
            contribution = random.choice([40000, 60000]) # Under or Over limit
            
            pm.add_fact(f"agi(bob, {agi})")
            pm.add_fact(f"contribution(bob, {contribution})")
            pm.add_fact(f"limit_pct({limit_pct})")
            
            # Query
            query = f"{predicate}(bob, Allowed)"
            result = pm.run_query(query)
            
            allowed = result.get('value', 0)
            
            scenario = f"Bob has AGI of ${agi}. He contributed ${contribution} to a public charity (50% limit)."
            question = "What is the allowed deduction?"
            
            cases.append({
                "id": hashlib.md5((scenario + question).encode()).hexdigest()[:12],
                "text": scenario,
                "question": question,
                "facts": "\n".join(pm.facts),
                "query": query,
                "answer": allowed,
                "gold_truth_subsection": "I.R.C. § 170(b)",
                "source_rules": ["I.R.C. § 170(b)"]
            })

    return cases

# --- Dispatch Table ---

SECTION_GENERATORS: Dict[str, Callable[[IRCSection, int], List[Dict]]] = {
    "1": generate_section_1_questions,
    "61": generate_section_61_questions,
    "162": generate_section_162_questions,
    "163": generate_section_163_questions,
    "121": generate_section_121_questions,
    "199A": generate_section_199A_questions,
    "170": generate_section_170_questions,
    "469": generate_section_469_questions,
    "1400Z-2": generate_section_1400Z2_questions,
}

# --- Main Generator Class ---

class SubtitleMultiGenerator:
    def __init__(self, irc_data_root: str, output_dir_mcq: str, output_dir_sara: str, sara_config_path: str):
        self.irc_data_root = irc_data_root
        self.output_dir_mcq = output_dir_mcq
        self.output_dir_sara = output_dir_sara
        self.generated_mcqs: List[Dict] = []
        self.generated_sara_cases: List[Dict] = []
        self.seen_ids: set = set()
        
        # Load SARA config
        with open(sara_config_path, 'r') as f:
            self.sara_config = yaml.safe_load(f)

    def run(self, seed: int = 42, per_subtitle_sample: int = 2):
        random.seed(seed)
        print(f"Starting generation with seed {seed}...")
        
        # 1. Identify Subtitle Directories
        subtitles = sorted([d for d in os.listdir(self.irc_data_root) if d.startswith("Subtitle_")])
        
        for sub_dir_name in subtitles:
            full_path = os.path.join(self.irc_data_root, sub_dir_name)
            if not os.path.isdir(full_path): continue
            
            print(f"Processing {sub_dir_name}...")
            all_sections = iter_sections_in_dir(full_path)
            
            # Sampling Logic
            if "Subtitle_A" in sub_dir_name:
                # Process ALL sections for Subtitle A (or at least the ones we have generators for + some generic)
                # For efficiency, let's process all that have specific generators, plus a sample of others
                sections_to_process = all_sections # Process all for A
            else:
                # Random sample for B-K
                if len(all_sections) > per_subtitle_sample:
                    sections_to_process = random.sample(all_sections, per_subtitle_sample)
                else:
                    sections_to_process = all_sections
            
            print(f"  Selected {len(sections_to_process)} sections.")
            
            for sec in sections_to_process:
                # A. Generate MCQs
                mcqs = []
                specific_gen = SECTION_GENERATORS.get(sec.section_number)
                
                if specific_gen:
                    mcqs = specific_gen(sec, 5)
                else:
                    # Fallback to generic
                    mcqs = generate_generic_numeric_questions_from_section(sec, 2)
                
                # Deduplicate and Store MCQs
                for q in mcqs:
                    if q['id'] not in self.seen_ids:
                        self.seen_ids.add(q['id'])
                        self.generated_mcqs.append(q)
                
                # B. Generate SARA Cases (if enabled)
                sara_cases = generate_sara_cases_for_section(sec, self.sara_config, 3)
                self.generated_sara_cases.extend(sara_cases)

        self.save_outputs()

    def save_outputs(self):
        # Save MCQs
        if not os.path.exists(self.output_dir_mcq):
            os.makedirs(self.output_dir_mcq)
            
        print(f"Saving {len(self.generated_mcqs)} MCQs to {self.output_dir_mcq}...")
        for q in self.generated_mcqs:
            filename = f"question_{q['section']}_{q['id']}.json".replace("/", "_")
            with open(os.path.join(self.output_dir_mcq, filename), 'w') as f:
                json.dump(q, f, indent=2)

        # Save SARA Cases
        if not os.path.exists(self.output_dir_sara):
            os.makedirs(self.output_dir_sara)
            
        print(f"Saving {len(self.generated_sara_cases)} SARA cases to {self.output_dir_sara}...")
        for c in self.generated_sara_cases:
            # Extract section from gold truth or id
            sec_num = "unknown"
            if "I.R.C. § " in c.get("gold_truth_subsection", ""):
                # Try to parse section number
                try:
                    sec_num = c["gold_truth_subsection"].split("§")[1].strip().split("(")[0]
                except: pass
            
            filename = f"sara_case_{sec_num}_{c['id']}.json".replace("/", "_")
            with open(os.path.join(self.output_dir_sara, filename), 'w') as f:
                json.dump(c, f, indent=2)

if __name__ == "__main__":
    generator = SubtitleMultiGenerator(
        irc_data_root="./irc_data",
        output_dir_mcq="./taxos_questions",
        output_dir_sara="./taxos_sara",
        sara_config_path=SARA_CONFIG_FILE
    )
    generator.run(seed=123, per_subtitle_sample=3)
