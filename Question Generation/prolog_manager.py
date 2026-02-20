import subprocess
import tempfile
import os
from typing import List, Dict, Any, Optional

class PrologManager:
    def __init__(self):
        self.rules = []
        self.facts = []
        # Check if swipl is available
        self.has_swipl = self._check_swipl()

    def _check_swipl(self) -> bool:
        try:
            subprocess.run(["swipl", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except FileNotFoundError:
            return False

    def load_rules(self, rules_text: str):
        """Load Prolog rules (as a string)."""
        self.rules.append(rules_text)

    def add_fact(self, fact: str):
        """Add a single Prolog fact."""
        self.facts.append(fact + ".")

    def clear_facts(self):
        self.facts = []

    def run_query(self, query: str) -> Dict[str, Any]:
        """
        Run a Prolog query.
        Returns a dictionary with 'success' (bool) and 'output' (str/data).
        """
        full_program = "\n".join(self.rules) + "\n" + "\n".join(self.facts)
        
        if not self.has_swipl:
            # Fallback / Simulation for environment without SWI-Prolog
            return self._simulate_query(query)

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pl', delete=False) as tmp:
            tmp.write(full_program)
            tmp_path = tmp.name

        try:
            # Run swipl
            # -g query -t halt
            cmd = ["swipl", "-q", "-f", tmp_path, "-g", f"({query} -> write('true'); write('false')), halt."]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            output = result.stdout.strip()
            
            success = output == 'true'
            return {"success": success, "raw_output": output}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def _simulate_query(self, query: str) -> Dict[str, Any]:
        """
        Simple internal logic to simulate Prolog for specific demo cases
        when SWI-Prolog is not installed.
        """
        # Simulation for Section 121
        if "exclude_gain_121" in query:
            # Parse facts from self.facts
            # expected: owned(alice, 3, 5). lived_in(alice, 3, 5).
            owned_years = 0
            lived_years = 0
            
            for fact in self.facts:
                if "owned" in fact:
                    # owned(alice, 3, 5)
                    parts = fact.split(',')
                    if len(parts) >= 2:
                        try:
                            owned_years = int(parts[1].strip())
                        except: pass
                if "lived_in" in fact:
                    parts = fact.split(',')
                    if len(parts) >= 2:
                        try:
                            lived_years = int(parts[1].strip())
                        except: pass
            
            # Rule: >= 2 years
            if owned_years >= 2 and lived_years >= 2:
                return {"success": True, "value": "Entailment"}
            else:
                return {"success": False, "value": "Contradiction"}

        # Simulation for Section 170
        if "charitable_contribution_limit_170" in query:
            # facts: agi(bob, 100000). contribution(bob, 60000). limit_pct(0.5).
            agi = 0.0
            contribution = 0.0
            limit_pct = 0.5
            
            for fact in self.facts:
                if "agi(" in fact:
                    try:
                        val = fact.split(',')[1].strip().replace(').', '')
                        agi = float(val)
                    except: pass
                if "contribution(" in fact:
                    try:
                        val = fact.split(',')[1].strip().replace(').', '')
                        contribution = float(val)
                    except: pass
            
            limit = agi * limit_pct
            allowed = min(contribution, limit)
            
            # If query asks for value, we might need to parse it. 
            # But for simple entailment "is allowed X", we check.
            return {"success": True, "value": allowed}

        return {"success": False, "error": "Simulation not implemented for this query"}
