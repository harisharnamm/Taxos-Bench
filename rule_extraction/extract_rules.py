import json
import re
import os

def parse_currency(value_str):
    return float(value_str.replace('$', '').replace(',', ''))

def parse_rate_table(text):
    brackets = []
    # Normalize text: remove newlines and extra spaces
    normalized_text = re.sub(r'\s+', ' ', text)
    
    # Regex patterns
    first_row_pattern = re.compile(r"Not over \$([\d,]+)\.?\s+(\d+(?:\.\d+)?)%")
    middle_row_pattern = re.compile(r"Over \$([\d,]+) but not over \$([\d,]+)\.?\s+\$([\d,]+(?:\.\d+)?), plus (\d+(?:\.\d+)?)% of the excess over \$([\d,]+)")
    last_row_pattern = re.compile(r"Over \$([\d,]+)\.?\s+\$([\d,]+(?:\.\d+)?), plus (\d+(?:\.\d+)?)% of the excess over \$([\d,]+)")
    scrambled_row_pattern = re.compile(r"Over \$([\d,]+) but not over \$([\d,]+(?:\.\d+)?), plus (\d+(?:\.\d+)?)% of the \$([\d,]+)\.? excess over \$([\d,]+)")

    # Find first row
    match1 = first_row_pattern.search(normalized_text)
    if match1:
        max_val = parse_currency(match1.group(1))
        rate = float(match1.group(2)) / 100
        brackets.append({
            "min": 0,
            "max": max_val,
            "rate": rate,
            "base_tax": 0
        })
    
    # Find middle rows (standard)
    for match in middle_row_pattern.finditer(normalized_text):
        min_val = parse_currency(match.group(1))
        max_val = parse_currency(match.group(2))
        base_tax = parse_currency(match.group(3))
        rate = float(match.group(4)) / 100
        excess_over = parse_currency(match.group(5))
        
        brackets.append({
            "min": min_val,
            "max": max_val,
            "rate": rate,
            "base_tax": base_tax
        })

    # Find middle rows (scrambled)
    for match in scrambled_row_pattern.finditer(normalized_text):
        min_val = parse_currency(match.group(1))
        base_tax = parse_currency(match.group(2))
        rate = float(match.group(3)) / 100
        max_val = parse_currency(match.group(4))
        excess_over = parse_currency(match.group(5))
        
        brackets.append({
            "min": min_val,
            "max": max_val,
            "rate": rate,
            "base_tax": base_tax
        })
        
    # Find last row
    match_last = last_row_pattern.search(normalized_text)
    if match_last:
        min_val = parse_currency(match_last.group(1))
        base_tax = parse_currency(match_last.group(2))
        rate = float(match_last.group(3)) / 100
        excess_over = parse_currency(match_last.group(4))
        
        brackets.append({
            "min": min_val,
            "max": float('inf'),
            "rate": rate,
            "base_tax": base_tax
        })
            
    return brackets

def extract_definitions(subsections):
    definitions = {}
    # Regex to find "The term 'X' means Y"
    # Handling smart quotes and normal quotes
    # Stop before "I.R.C." or end of string
    def_pattern = re.compile(r'The term [“"](.+?)[”"] means (.+?)(?=\s*I\.R\.C\.|$)', re.IGNORECASE)
    
    for sub in subsections:
        text = sub.get('text', '')
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        matches = def_pattern.findall(text)
        for term, definition in matches:
            if term not in definitions:
                definitions[term] = {
                    "term": term,
                    "definition": definition.strip(),
                    "source": sub.get('citation')
                }
    return list(definitions.values())

def extract_special_rules(subsections):
    target_prefixes = ["(f)", "(g)", "(h)", "(i)", "(j)"]
    
    root_rules = []
    rule_map = {} # id -> rule object
    
    for sub in subsections:
        sub_id = sub.get('subsection_id')
        if not sub_id:
            continue
            
        # Check if it belongs to one of the target sections
        is_target = False
        for prefix in target_prefixes:
            if sub_id.startswith(prefix):
                is_target = True
                break
        
        if not is_target:
            continue
            
        # Create rule object
        rule = {
            "id": sub_id,
            "citation": sub.get('citation'),
            "text": sub.get('text'),
            "subrules": []
        }
        rule_map[sub_id] = rule
        
        # Find parent
        # Logic: (f)(1) parent is (f)
        # (f)(1)(A) parent is (f)(1)
        # (f)(1)(A)(i) parent is (f)(1)(A)
        
        # We can try to strip the last parenthesized group
        # Regex to find the last group: \(\w+\)$
        parent_id = re.sub(r'\([a-zA-Z0-9]+\)$', '', sub_id)
        
        if parent_id in rule_map:
            rule_map[parent_id]['subrules'].append(rule)
        elif sub_id in target_prefixes:
            # Top level special rule
            root_rules.append(rule)
            
    return root_rules

def extract_rules():
    input_path = '/Users/mypro16/Desktop/Tax Benchmarking/Data Corpus/irc_data/Subtitle_A__INCOME_TAXES_Sections_1_to_1564/Chapter_1__Normal_taxes_and_surtaxes_Sections_1_to/section_1.json'
    output_path = '/Users/mypro16/Desktop/Tax Benchmarking/rule_extraction/rule_library.json'
    
    with open(input_path, 'r') as f:
        data = json.load(f)
        
    rule_library = {
        "rate_structures": [],
        "definitions": [],
        "special_rules": [],
        "computational_formulae": [],
        "edge_cases_and_exceptions": []
    }
    
    subsections = data.get('subsections', [])
    
    # 1. Extract Rate Structures
    target_subsections = {
        "(a)": "Married Individuals Filing Joint Returns And Surviving Spouses",
        "(b)": "Heads Of Households",
        "(c)": "Unmarried Individuals (Other Than Surviving Spouses And Heads Of Households)",
        "(d)": "Married Individuals Filing Separate Returns",
        "(e)": "Estates And Trusts"
    }
    
    for sub in subsections:
        sub_id = sub.get('subsection_id')
        if sub_id in target_subsections:
            brackets = parse_rate_table(sub.get('text', ''))
            if brackets:
                rule_library["rate_structures"].append({
                    "id": sub_id,
                    "name": target_subsections[sub_id],
                    "citation": sub.get('citation'),
                    "brackets": brackets
                })

    # 2. Extract Definitions
    rule_library["definitions"] = extract_definitions(subsections)
    
    # 3. Extract Special Rules
    rule_library["special_rules"] = extract_special_rules(subsections)
    
    # 4. Computational Formulae
    rule_library["computational_formulae"].append({
        "type": "standard_bracket_calculation",
        "description": "Tax = Base Tax + (Rate * (Taxable Income - Bracket Min))",
        "variables": ["Taxable Income", "Bracket Min", "Base Tax", "Rate"]
    })
    
    with open(output_path, 'w') as f:
        json.dump(rule_library, f, indent=2)
    
    print(f"Extraction complete. Rules saved to {output_path}")

if __name__ == "__main__":
    extract_rules()
