import json
import re
import os
from pathlib import Path
import glob

class TaxosRuleExtractor:
    def __init__(self, source_dir, output_dir):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def clean_text_content(self, text):
        if not text: return ""
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'^I\.R\.C\.\s*§?\s*[\w\(\)\-]+', '', text).strip()
        match = re.match(r'^([^—\-]{1,100})[—\-](.*)', text)
        if match:
            pre_dash = match.group(1).strip()
            post_dash = match.group(2).strip()
            if not re.search(r'\b(means|includes|defined)\b', pre_dash, re.IGNORECASE):
                text = post_dash
        text = re.sub(r'^[—\-:;,\.]+\s*', '', text).strip()
        return text

    def clean_text_final(self, text):
        if not text: return ""
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'^I\.R\.C\.\s*§?\s*[\w\(\)\-]+', '', text).strip()
        text = re.sub(r'I\.R\.C\.\s*§\s*[\w\(\)\-]+', '', text)
        match = re.match(r'^([^—\-]{1,100})[—\-](.*)', text)
        if match:
            pre_dash = match.group(1).strip()
            if not re.search(r'\b(means|includes|defined)\b', pre_dash, re.IGNORECASE):
                text = match.group(2).strip()
        text = re.sub(r'^[—\-:;,\.]+\s*', '', text).strip()
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def extract_title(self, text):
        text = re.sub(r'^I\.R\.C\.\s*§?\s*[\w\(\)\-]+', '', text).strip()
        match = re.match(r'^([^—\-]{1,100})[—\-]', text)
        if match:
            return match.group(1).strip()
        return None

    def classify_rule_type(self, text):
        text_lower = text.lower()
        if re.search(r'\bmeans\b|\bdefined\b|\bdefinition\b|\bterm\b', text_lower):
            return "definition"
        if re.search(r'\bif\b|\bunless\b|\bprovided\b|\bwhere\b|\bwhen\b', text_lower):
            return "condition"
        if re.search(r'\bexcept\b|\bexception\b|\bnotwithstanding\b', text_lower):
            return "exception"
        if re.search(r'\blimitation\b|\bnot exceed\b|\bmaximum\b|\bminimum\b|\bceiling\b|\bfloor\b', text_lower):
            return "limitation"
        if re.search(r'\bpercent\b|\bsum of\b|\bproduct of\b|\bexcess of\b|\bequal to\b|\blesser of\b|\bgreater of\b', text_lower):
            return "computation"
        if re.search(r'^see section', text_lower):
            return "cross_reference"
        return "condition"

    def extract_thresholds(self, text):
        thresholds = []
        matches = re.finditer(r'\$([\d,]+)', text)
        for m in matches:
            val_str = m.group(1).replace(',', '')
            try:
                val = int(val_str)
                thresholds.append({"label": "amount", "value": val, "text": m.group(0)})
            except:
                pass
        return thresholds

    def extract_percentages(self, text):
        percentages = []
        matches = re.finditer(r'(\d+(?:\.\d+)?)\s*(?:%|percent)', text, re.IGNORECASE)
        for m in matches:
            val_str = m.group(1)
            try:
                val = float(val_str)
                percentages.append({"label": "rate", "value": val / 100.0, "text": m.group(0)})
            except:
                pass
        return percentages

    def extract_computations(self, text):
        computations = []
        text_lower = text.lower()
        if "lesser of" in text_lower:
            computations.append({"operation": "min", "inputs": ["parsed_from_text"]})
        if "greater of" in text_lower:
            computations.append({"operation": "max", "inputs": ["parsed_from_text"]})
        if "excess of" in text_lower or "excess over" in text_lower:
             computations.append({"operation": "subtraction", "inputs": ["parsed_from_text"]})
        if "sum of" in text_lower:
             computations.append({"operation": "sum", "inputs": ["parsed_from_text"]})
        if "product of" in text_lower or "multiplied by" in text_lower or "percent of" in text_lower:
             computations.append({"operation": "multiply", "inputs": ["parsed_from_text"]})
        return computations

    def extract_logic_structure(self, text):
        structure = {"if": [], "and": [], "or": [], "unless": [], "except": [], "result": ""}
        parts = re.split(r'\b(if|unless|except|provided that|where|when)\b', text, flags=re.IGNORECASE)
        if parts[0].strip():
             structure["result"] = parts[0].strip()
        for i in range(1, len(parts), 2):
            sep = parts[i].lower()
            clause = parts[i+1].strip() if i+1 < len(parts) else ""
            if sep in ["if", "provided that", "where", "when"]:
                structure["if"].append(clause)
            elif sep == "unless":
                structure["unless"].append(clause)
            elif sep in ["except", "exception"]:
                structure["except"].append(clause)
        return structure

    def extract_definitions_v3(self, text):
        match = re.search(r'The term [“"](.+?)[”"] means (.+)', text, re.IGNORECASE | re.DOTALL)
        if match:
            return {
                "term": match.group(1),
                "requirements": [match.group(2).strip()]
            }
        return None

    def extract_exceptions_v3(self, text):
        exceptions = []
        matches = re.finditer(r'Except as provided in (.+?)(?:,|$)', text, re.IGNORECASE)
        for m in matches:
            exceptions.append({"applies_when": m.group(1), "effect": "See referenced section"})
        return exceptions

    def extract_cross_references_v3(self, text):
        refs = []
        matches = re.finditer(r'(.{0,30})\bsection\s*(\d+[A-Z]?(?:\([a-z0-9]+\))*)', text, re.IGNORECASE)
        for m in matches:
            refs.append({
                "section": m.group(2),
                "reason": m.group(1).strip() + "..."
            })
        return refs

    def is_fragment(self, sub_id, text):
        depth = sub_id.count('(')
        if depth >= 5: return True
        if not text: return False
        if text[0].islower(): return True
        if re.match(r'^(and|or)\b', text, re.IGNORECASE): return True
        return False

    def process_section(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []
        
        section_id = data.get("section_number", Path(file_path).stem.replace("section_", ""))
        subsections = data.get("subsections", [])
        
        sub_map = {s["subsection_id"]: s for s in subsections}
        sorted_ids = sorted(sub_map.keys())
        
        children_map = {sid: [] for sid in sorted_ids}
        for sid in sorted_ids:
            if '(' in sid:
                parent_id = sid[:sid.rfind('(')]
                if parent_id in children_map:
                    children_map[parent_id].append(sid)
        
        consumed_ids = set()
        final_rules = []
        
        for sid in sorted_ids:
            if sid in consumed_ids:
                continue
            
            my_children = children_map[sid]
            if not my_children:
                pass
            else:
                first_child_id = my_children[0]
                first_child_text = self.clean_text_content(sub_map[first_child_id].get("text", ""))
                
                if self.is_fragment(first_child_id, first_child_text):
                    for child in my_children:
                        consumed_ids.add(child)
                        stack = [child]
                        while stack:
                            curr = stack.pop()
                            consumed_ids.add(curr)
                            stack.extend(children_map[curr])
                else:
                    my_text = self.clean_text_content(sub_map[sid].get("text", ""))
                    if my_text.startswith(first_child_text[:20]):
                        consumed_ids.add(sid)
                    else:
                        if sub_map[sid].get("text", "").strip().endswith(':'):
                             for child in my_children:
                                consumed_ids.add(child)
                                stack = [child]
                                while stack:
                                    curr = stack.pop()
                                    consumed_ids.add(curr)
                                    stack.extend(children_map[curr])
                        else:
                             consumed_ids.add(sid)

        for sid in sorted_ids:
            if sid in consumed_ids:
                continue
                
            source_subs = [sid]
            stack = list(children_map[sid])
            while stack:
                child = stack.pop()
                if child in consumed_ids:
                    source_subs.append(child)
                    stack.extend(children_map[child])
            source_subs.sort()
            
            raw_text = sub_map[sid].get("text", "")
            final_text = self.clean_text_final(raw_text)
            
            rule_type = self.classify_rule_type(final_text)
            
            rule = {
                "section": section_id,
                "subsection": sid,
                "source_subsections": source_subs,
                "rule_type": rule_type,
                "title": self.extract_title(raw_text),
                "text": final_text,
                "conditions": [],
                "computations": self.extract_computations(final_text),
                "thresholds": self.extract_thresholds(final_text),
                "percentages": self.extract_percentages(final_text),
                "variables": [],
                "exceptions": self.extract_exceptions_v3(final_text),
                "logical_structure": self.extract_logic_structure(final_text),
                "cross_references": self.extract_cross_references_v3(final_text),
                "effective_dates": [],
                "raw_text": raw_text,
                "definitions": self.extract_definitions_v3(final_text) if rule_type == "definition" else None
            }
            
            rule["conditions"] = rule["logical_structure"]["if"] + rule["logical_structure"]["unless"]
            
            final_rules.append(rule)
            
        return final_rules

    def is_target_section(self, filename):
        match = re.search(r'section_(\d+)([A-Z]*)\.json', filename)
        if not match: return False
        num = int(match.group(1))
        return num < 60

    def run_batch(self):
        print(f"Scanning {self.source_dir}...")
        files = sorted(glob.glob(str(self.source_dir / "section_*.json")))
        
        count = 0
        for file_path in files:
            filename = Path(file_path).name
            if self.is_target_section(filename):
                print(f"Processing {filename}...")
                rules = self.process_section(file_path)
                
                section_id = filename.replace(".json", "").replace("section_", "")
                output_file = self.output_dir / f"section_{section_id}_rules.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(rules, f, indent=2)
                count += 1
        
        print(f"Extraction complete. Processed {count} sections.")

if __name__ == "__main__":
    SOURCE_DIR = "/Users/mypro16/Desktop/Tax Benchmarking/Data Corpus/irc_data/Subtitle_A__INCOME_TAXES_Sections_1_to_1564/Chapter_1__Normal_taxes_and_surtaxes_Sections_1_to"
    OUTPUT_DIR = "/Users/mypro16/Desktop/Tax Benchmarking/rule_library/SubchapterA"
    
    extractor = TaxosRuleExtractor(SOURCE_DIR, OUTPUT_DIR)
    extractor.run_batch()
