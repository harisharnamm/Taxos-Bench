import json
import os
import re
import random
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Callable

# --- Data Models ---

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
    max_income: float # float('inf') for top bracket

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
    category: str # "Inclusion" or "Exclusion" or "Deduction" or "Nondeductible"
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

def iter_subtitle_A_sections(subtitle_dir: str) -> List[IRCSection]:
    sections = []
    if not os.path.exists(subtitle_dir):
        print(f"Directory not found: {subtitle_dir}")
        return sections

    for root, _, files in os.walk(subtitle_dir):
        for file in files:
            if file.startswith("section_") and file.endswith(".json"):
                full_path = os.path.join(root, file)
                sec = load_section(full_path)
                if sec:
                    sections.append(sec)
    return sections

# --- Rule Detection Helpers ---

def detect_tax_brackets(sec: IRCSection) -> List[TaxBracketRule]:
    rules = []
    if sec.section_number == "1":
        # Simplified detection: In a real scenario, we'd parse the inflation-adjusted tables.
        # Here we provide a standard 2024 Single filer bracket set as a "detected" rule for simulation.
        brackets = [
            TaxBracket(0.10, 0, 11600),
            TaxBracket(0.12, 11600, 47150),
            TaxBracket(0.22, 47150, 100525),
            TaxBracket(0.24, 100525, 191950),
            TaxBracket(0.32, 191950, 243725),
            TaxBracket(0.35, 243725, 609350),
            TaxBracket(0.37, 609350, float('inf'))
        ]
        rules.append(TaxBracketRule(
            section_code="1",
            year=2024,
            filer_status="Single",
            brackets=brackets,
            citation="I.R.C. § 1(j)"
        ))
    return rules

def detect_classification_rules(sec: IRCSection) -> List[ClassificationRule]:
    rules = []
    if sec.section_number == "61":
        # Detect inclusions
        inclusions = ["Compensation for services", "Gross income derived from business", "Gains derived from dealings in property", "Interest", "Rents", "Royalties", "Dividends", "Alimony", "Annuities", "Income from life insurance contracts", "Pensions", "Income from discharge of indebtedness", "Distributive share of partnership gross income", "Income in respect of a decedent", "Income from an interest in an estate or trust"]
        for item in inclusions:
            rules.append(ClassificationRule("61", "Inclusion", item, "I.R.C. § 61(a)"))
            
    elif sec.section_number == "162":
        # Detect deductions
        deductions = ["Salaries or other compensation", "Traveling expenses", "Rentals"]
        for item in deductions:
            rules.append(ClassificationRule("162", "Deduction", item, "I.R.C. § 162(a)"))
        # Detect nondeductible (simplified)
        nondeductible = ["Fines and penalties", "Illegal bribes", "Lobbying expenses"]
        for item in nondeductible:
            rules.append(ClassificationRule("162", "Nondeductible", item, "I.R.C. § 162(c)/(f)/(e)"))

    elif sec.section_number == "163":
        # Interest
        rules.append(ClassificationRule("163", "Deduction", "Qualified residence interest", "I.R.C. § 163(h)(3)"))
        rules.append(ClassificationRule("163", "Deduction", "Investment interest", "I.R.C. § 163(d)"))
        rules.append(ClassificationRule("163", "Nondeductible", "Personal interest", "I.R.C. § 163(h)(1)"))
        
    return rules

def detect_exclusion_rules_121(sec: IRCSection) -> List[ExclusionRule]:
    rules = []
    if sec.section_number == "121":
        rules.append(ExclusionRule(
            section_code="121",
            amount_single=250000,
            amount_joint=500000,
            ownership_years=2,
            use_years=2,
            citation="I.R.C. § 121(a)/(b)"
        ))
    return rules

def detect_qbi_rules_199A(sec: IRCSection) -> List[QBIRule]:
    rules = []
    if sec.section_number == "199A":
        rules.append(QBIRule("199A", 0.20, "I.R.C. § 199A(a)"))
    return rules

def detect_agi_limit_rules(sec: IRCSection) -> List[AGILimitRule]:
    rules = []
    # Regex to find percentage limits related to AGI
    # e.g. "limited to 60 percent of the taxpayer's contribution base" (contribution base ~ AGI for 170)
    # or "10 percent of the adjusted gross income"
    
    # For Section 170 specifically, we look for the standard limits
    if sec.section_number == "170":
        # Simplified detection for the sake of the example, scanning text for keywords
        for sub in sec.subsections:
            text = sub.text.lower()
            if "percent" in text and ("contribution base" in text or "adjusted gross income" in text):
                # Try to extract percentage
                match = re.search(r"(\d+)\s+percent", text)
                if match:
                    pct = float(match.group(1)) / 100.0
                    rules.append(AGILimitRule(
                        section_code=sec.section_number,
                        percentage=pct,
                        description=f"Limitation of {match.group(1)}% of AGI/Contribution Base",
                        citation=sub.citation
                    ))
    return rules

def detect_basis_adjustment_rules_1400Z2(sec: IRCSection) -> List[BasisAdjustmentRule]:
    rules = []
    seen_years = set()
    
    if sec.section_number == "1400Z-2":
        for sub in sec.subsections:
            text = sub.text.lower()
            # Look for 5 years / 10 percent
            if "5 years" in text and "10 percent" in text and "basis" in text and "increased" in text:
                if 5 not in seen_years:
                    rules.append(BasisAdjustmentRule(
                        section_code=sec.section_number,
                        years_required=5,
                        percentage=0.10,
                        description="Basis increase for 5-year holding",
                        citation=sub.citation
                    ))
                    seen_years.add(5)
            
            # Look for 7 years / 5 percent
            if "7 years" in text and "5 percent" in text and "basis" in text and "increased" in text:
                if 7 not in seen_years:
                    rules.append(BasisAdjustmentRule(
                        section_code=sec.section_number,
                        years_required=7,
                        percentage=0.05,
                        description="Additional basis increase for 7-year holding",
                        citation=sub.citation
                    ))
                    seen_years.add(7)
    return rules

def detect_passive_loss_stack(sec: IRCSection) -> List[PassiveLossRule]:
    rules = []
    if sec.section_number == "469":
        # General rule detection
        for sub in sec.subsections:
            if "(a)" in sub.subsection_id: # General rule
                rules.append(PassiveLossRule(
                    section_code=sec.section_number,
                    description="Passive activity loss disallowed",
                    citation=sub.citation
                ))
                break
    return rules

# --- MCQ Helpers ---

def make_mcq_from_numeric_answer(correct_value: float, distractors: List[float], fmt: str = "${:,.2f}") -> Tuple[List[str], int]:
    # Format all values
    correct_str = fmt.format(correct_value)
    distractor_strs = [fmt.format(d) for d in distractors]
    
    # Deduplicate and ensure correct answer is present
    options = set(distractor_strs)
    options.add(correct_str)
    
    # Convert to list and shuffle
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
    # Correct: deduction (min(contribution, limit))
    # Distractors:
    # 1. Full contribution (ignoring limit)
    # 2. Limit amount (if contribution < limit, this is wrong)
    # 3. Contribution - Limit (nonsense)
    # 4. 0 (pessimistic)
    
    distractors = [
        contribution,
        limit,
        max(0, contribution - limit),
        0.0
    ]
    # Remove correct answer from distractors if present (e.g. if contribution == limit)
    distractors = [d for d in distractors if abs(d - deduction) > 0.01]
    
    return make_mcq_from_numeric_answer(deduction, distractors)

def build_469_mcq(allowed: float, passive_loss: float, passive_income: float) -> Tuple[List[str], int]:
    # Correct: allowed (min(loss, income))
    # Distractors:
    # 1. Full passive loss (ignoring limit)
    # 2. Full passive income (if loss < income, this is wrong)
    # 3. Suspended loss (confusing allowed vs suspended)
    # 4. Loss + Income (nonsense)
    
    suspended = passive_loss - allowed
    distractors = [
        passive_loss,
        passive_income,
        suspended,
        passive_loss + passive_income
    ]
    distractors = [d for d in distractors if abs(d - allowed) > 0.01]
    
    return make_mcq_from_numeric_answer(allowed, distractors)

def build_1400Z2_mcq(adjusted_basis: float, deferred_gain: float, initial_basis: float) -> Tuple[List[str], int]:
    # Correct: adjusted_basis
    # Distractors:
    # 1. Initial basis (0)
    # 2. Deferred gain (no adjustment)
    # 3. 10% adjustment only (even if 7 years) -> deferred_gain * 0.10
    # 4. 15% adjustment (correct amount, but maybe confused with basis if basis wasn't 0?) -> deferred_gain * 0.15
    # 5. Remaining gain -> deferred_gain * 0.85
    
    distractors = [
        initial_basis,
        deferred_gain,
        deferred_gain * 0.10,
        deferred_gain * 0.85
    ]
    distractors = [d for d in distractors if abs(d - adjusted_basis) > 0.01]
    
    return make_mcq_from_numeric_answer(adjusted_basis, distractors)

# --- Section Generators ---

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
        
        # Distractors
        # 1. Flat rate (top bracket)
        # 2. Flat rate (average bracket)
        # 3. Wrong bracket calculation (e.g. all income at marginal rate)
        marginal_rate = 0.0
        for b in rule.brackets:
            if income > b.min_income: marginal_rate = b.rate
        
        distractors = [
            income * marginal_rate,
            income * 0.22, # Common flat assumption
            tax * 0.8,
            tax * 1.2
        ]
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
    # Pool of items
    items_pool = [
        ("Wages", True), ("Interest on Bank Account", True), ("Dividends", True), 
        ("Gift from Parents", False), ("Loan Proceeds", False), ("Return of Capital", False),
        ("Gambling Winnings", True), ("Life Insurance Proceeds (Death)", False)
    ]
    
    entities = ["Alice", "Bob", "Charlie"]
    
    for _ in range(num_variations):
        entity = random.choice(entities)
        # Select 3-5 items
        selected_items = random.sample(items_pool, k=random.randint(3, 5))
        
        scenario_parts = []
        gross_income = 0.0
        all_receipts = 0.0
        
        for name, is_included in selected_items:
            amount = round(random.uniform(1000, 50000), 2)
            scenario_parts.append(f"{name}: ${amount:,.2f}")
            all_receipts += amount
            if is_included:
                gross_income += amount
        
        scenario = f"{entity} received the following amounts during the year: " + ", ".join(scenario_parts) + "."
        question = f"Calculate {entity}'s gross income under I.R.C. § 61."
        
        distractors = [
            all_receipts,
            0.0,
            gross_income * 0.5,
            all_receipts - gross_income # The excluded amount
        ]
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
            "reasoning": "Summed included items, ignored excluded items (Gifts, Loans, etc.).",
            "source_rules": ["I.R.C. § 61(a)"]
        })
    return questions

def generate_section_162_questions(sec: IRCSection, num_variations: int) -> List[Dict]:
    questions = []
    items_pool = [
        ("Office Rent", True), ("Employee Salaries", True), ("Office Supplies", True),
        ("Traffic Fines", False), ("Political Contributions", False), ("Personal Lunch", False),
        ("Bribes", False)
    ]
    
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
            if is_deductible:
                deductible += amount
        
        scenario = f"{entity} incurred the following expenses: " + ", ".join(scenario_parts) + "."
        question = f"Calculate the total deductible trade or business expenses under I.R.C. § 162."
        
        distractors = [
            total_expenses,
            deductible * 0.5,
            total_expenses - deductible
        ]
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
            "answer_explanation": f"Only ordinary and necessary business expenses are deductible. Fines, bribes, and personal expenses are not. Total: ${deductible:,.2f}.",
            "reasoning": "Summed deductible items.",
            "source_rules": ["I.R.C. § 162(a)", "I.R.C. § 162(c)", "I.R.C. § 162(f)"]
        })
    return questions

def generate_section_163_questions(sec: IRCSection, num_variations: int) -> List[Dict]:
    questions = []
    items_pool = [
        ("Mortgage Interest on Main Home", True), ("Investment Interest (within limits)", True),
        ("Credit Card Interest", False), ("Car Loan Interest (Personal)", False),
        ("Student Loan Interest (assume deductible for simplicity)", True)
    ]
    
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
            if is_deductible:
                deductible += amount
        
        scenario = f"{entity} paid the following interest amounts: " + ", ".join(scenario_parts) + "."
        question = f"Calculate the total deductible interest under I.R.C. § 163."
        
        distractors = [
            total,
            0.0,
            total - deductible
        ]
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
            "answer_explanation": f"Personal interest is generally not deductible. Qualified residence interest and investment interest are. Total: ${deductible:,.2f}.",
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
        
        # Scenario A: Qualifies
        years_owned = 3
        years_lived = 3
        exclusion = rule.amount_single
        taxable_gain = max(0, gain - exclusion)
        
        scenario = (
            f"{entity} sold their principal residence for ${sale_price:,.2f}. "
            f"They purchased it for ${purchase_price:,.2f} and lived in it for {years_lived} years out of the last 5 years."
        )
        question = f"Calculate the taxable gain recognized on the sale under I.R.C. § 121."
        
        distractors = [
            gain, # No exclusion
            0.0, # Full exclusion (if gain > exclusion)
            gain - (exclusion / 2) # Wrong exclusion amount
        ]
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
        # Assume taxable income is sufficient and below threshold for simplicity
        deduction = qbi * rule.percentage
        
        scenario = f"{entity} has Qualified Business Income (QBI) of ${qbi:,.2f} from a sole proprietorship. {entity}'s taxable income is below the threshold amount."
        question = f"Calculate the QBI deduction under I.R.C. § 199A."
        
        distractors = [
            qbi,
            qbi * 0.5,
            0.0,
            qbi * 0.1
        ]
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
        carryover = contribution - allowed
        
        scenario = (
            f"In {year}, {entity} has an Adjusted Gross Income (AGI) (or contribution base) of ${agi:,.2f}. "
            f"{entity} makes a charitable contribution of ${contribution:,.2f} in cash to a public charity. "
            f"Under {rule.citation}, the deduction is limited to {int(rule.percentage*100)}% of the contribution base."
        )
        
        question = f"Calculate the allowable charitable deduction for {year}."
        
        choices, correct_index = build_170_mcq(allowed, contribution, limit_amount)
        
        answer_explanation = (
            f"The deduction is limited to {int(rule.percentage*100)}% of AGI (${limit_amount:,.2f}). "
            f"Since the contribution (${contribution:,.2f}) is compared to the limit, the allowable deduction is ${allowed:,.2f}."
        )
        
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
            "answer_explanation": answer_explanation,
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
        
        scenario = (
            f"In {year}, {entity} has wages of ${wages:,.2f}. {entity} also has an interest in a passive activity "
            f"which generated a loss of ${passive_activity_loss:,.2f} for the year. {entity} has passive income from another source "
            f"of ${passive_activity_income:,.2f}."
        )
        
        question = (
            f"Calculate the amount of the passive activity loss that is deductible in {year} under {rule.citation}."
        )
        
        choices, correct_index = build_469_mcq(allowed_loss, passive_activity_loss, passive_activity_income)
        
        answer_explanation = (
            f"Passive losses are limited to passive income. With ${passive_activity_income:,.2f} in passive income, "
            f"only ${allowed_loss:,.2f} of the ${passive_activity_loss:,.2f} loss is deductible."
        )
        
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
            "answer_explanation": answer_explanation,
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
        
        scenario = (
            f"In {year_invested}, {entity} realized a capital gain of ${deferred_gain:,.2f} and invested the entire amount "
            f"into a Qualified Opportunity Fund (QOF), making a valid election to defer the gain under Section 1400Z-2. "
            f"{entity} holds the QOF investment for {holding_period} years."
        )
        
        question = (
            f"Calculate {entity}'s adjusted basis in the QOF investment after the {holding_period}-year holding period, "
            f"accounting for any basis adjustments under Section 1400Z-2(b)(2)(B)."
        )
        
        choices, correct_index = build_1400Z2_mcq(adjusted_basis, deferred_gain, initial_basis)
        
        answer_explanation = (
            f"The basis is increased by {int(total_pct_increase*100)}% of the deferred gain due to the {holding_period}-year holding period. "
            f"Adjusted Basis = $0 + (${deferred_gain:,.2f} * {total_pct_increase}) = ${adjusted_basis:,.2f}."
        )
        
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
            "answer_explanation": answer_explanation,
            "reasoning": "Applied basis adjustment rules.",
            "source_rules": [r.citation for r in applicable_rules]
        })
    return questions

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

def generate_questions_for_section(sec: IRCSection, num_variations: int = 5) -> List[Dict]:
    generator = SECTION_GENERATORS.get(sec.section_number)
    if generator:
        return generator(sec, num_variations)
    return []

# --- Pipeline ---

class SubtitleAQuestionGenerator:
    def __init__(self, subtitle_dir: str, output_dir: str):
        self.subtitle_dir = subtitle_dir
        self.output_dir = output_dir
        self.generated_questions: List[Dict] = []
        self.seen_ids: set = set()

    def run(self, max_questions_per_section: int = 5):
        print(f"Scanning sections in {self.subtitle_dir}...")
        sections = iter_subtitle_A_sections(self.subtitle_dir)
        print(f"Found {len(sections)} sections.")
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        total_generated = 0
        
        for sec in sections:
            # Generate questions
            qs = generate_questions_for_section(sec, num_variations=max_questions_per_section)
            
            # Trim and Deduplicate
            valid_qs = []
            for q in qs:
                if q['id'] not in self.seen_ids:
                    self.seen_ids.add(q['id'])
                    valid_qs.append(q)
            
            valid_qs = valid_qs[:max_questions_per_section]
            
            if valid_qs:
                self.generated_questions.extend(valid_qs)
                total_generated += len(valid_qs)
                
                # Save per section (optional, but good for organization)
                # For now, we'll just dump everything at the end or in batches
                pass

        # Save all
        self.save_all_questions()
        print(f"Total questions generated: {total_generated}")

    def save_all_questions(self):
        for q in self.generated_questions:
            filename = f"question_{q['section']}_{q['id']}.json"
            # Clean filename
            filename = filename.replace("/", "_").replace(" ", "_")
            path = os.path.join(self.output_dir, filename)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(q, f, indent=2)

def main():
    subtitle_dir = "./irc_data/Subtitle_A__INCOME_TAXES_Sections_1_to_1564"
    output_dir = "./taxos_subtitle_A_questions"
    
    generator = SubtitleAQuestionGenerator(subtitle_dir, output_dir)
    generator.run(max_questions_per_section=5)

if __name__ == "__main__":
    main()
