# validate_taxos_questions.py
import json, os, glob, sys

MCQ_DIR = "./taxos_questions"   # adjust if needed
SARA_DIR = "./taxos_sara"      # adjust if needed
EXPECTED_CHOICES = 4

errors = []
def check_mcq_file(path):
    try:
        j = json.load(open(path, 'r', encoding='utf-8'))
    except Exception as e:
        errors.append((path, f"JSON parse error: {e}"))
        return
    # basic fields
    for k in ("id","section","citation","type","scenario","question","choices","correct_choice_index","answer_explanation","reasoning","source_rules"):
        if k not in j:
            errors.append((path, f"Missing field: {k}"))
    # choices length
    choices = j.get("choices", [])
    if not isinstance(choices, list) or len(choices) != EXPECTED_CHOICES:
        errors.append((path, f"Choices should be list of length {EXPECTED_CHOICES}, got {len(choices)}"))
    # correct index
    idx = j.get("correct_choice_index")
    if not isinstance(idx, int) or not (0 <= idx < len(choices)):
        errors.append((path, f"Invalid correct_choice_index: {idx}"))
    # citation
    if not j.get("citation"):
        errors.append((path, "Empty citation"))
    # reasoning
    if not j.get("reasoning"):
        errors.append((path, "Empty reasoning"))

def check_sara_file(path):
    try:
        j = json.load(open(path, 'r', encoding='utf-8'))
    except Exception as e:
        errors.append((path, f"JSON parse error: {e}"))
        return
    for k in ("text","question","facts","query","answer","gold_truth_subsection"):
        if k not in j:
            errors.append((path, f"SARA missing field: {k}"))

# Walk MCQ dir
for path in glob.glob(os.path.join(MCQ_DIR, "**", "question_*.json"), recursive=True):
    check_mcq_file(path)

# Walk SARA dir
for path in glob.glob(os.path.join(SARA_DIR, "**", "sara_*.json"), recursive=True):
    check_sara_file(path)

if errors:
    print("Validation FAILED — summary:")
    for p, msg in errors[:200]:
        print(p, ":", msg)
    sys.exit(2)
else:
    print("All checks passed ✅")
