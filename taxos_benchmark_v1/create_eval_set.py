import json
import os
import random
import glob
from collections import defaultdict

def create_eval_set(source_dir, output_file, total_questions=50):
    print(f"Scanning {source_dir}...")
    all_files = glob.glob(os.path.join(source_dir, "*.json"))
    
    questions_by_type = defaultdict(list)
    
    for fpath in all_files:
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            q_type = data.get('type', 'Unknown')
            questions_by_type[q_type].append(data)
                
        except Exception as e:
            print(f"Error reading {fpath}: {e}")

    print("Found questions by type:")
    for q_type, qs in questions_by_type.items():
        print(f"  - {q_type}: {len(qs)}")
    
    final_set = []
    
    # Strategy: Prioritize non-recall questions to ensure variety
    # There are roughly 9 non-recall types. Let's try to get ~3 from each.
    # Then fill the rest with Recall questions.
    
    non_recall_types = [t for t in questions_by_type.keys() if "Recall" not in t]
    recall_types = [t for t in questions_by_type.keys() if "Recall" in t]
    
    # 1. Select non-recall questions (Target: 3 per type)
    target_per_non_recall = 3
    for q_type in non_recall_types:
        available = questions_by_type[q_type]
        count = min(len(available), target_per_non_recall)
        selected = random.sample(available, count)
        final_set.extend(selected)
        print(f"Selected {len(selected)} from {q_type}")
        
    # 2. Fill the rest with Recall questions
    remaining_slots = total_questions - len(final_set)
    if remaining_slots > 0 and recall_types:
        # Split remaining slots among recall types
        slots_per_recall = remaining_slots // len(recall_types)
        
        for i, q_type in enumerate(recall_types):
            available = questions_by_type[q_type]
            
            # If it's the last type, take all remaining slots to ensure we hit total
            if i == len(recall_types) - 1:
                count = min(len(available), total_questions - len(final_set))
            else:
                count = min(len(available), slots_per_recall)
            
            selected = random.sample(available, count)
            final_set.extend(selected)
            print(f"Selected {len(selected)} from {q_type}")
            
    random.shuffle(final_set)
    
    print(f"Selected {len(final_set)} questions for evaluation.")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for q in final_set:
            f.write(json.dumps(q) + '\n')
            
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    SOURCE_DIR = "./taxos_questions"
    OUTPUT_FILE = "./taxos_benchmark_v1/eval_set.jsonl"
    
    create_eval_set(SOURCE_DIR, OUTPUT_FILE, total_questions=50)
