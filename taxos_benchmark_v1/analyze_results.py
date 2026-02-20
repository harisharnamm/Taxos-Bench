import json
import os
from collections import defaultdict, Counter

RESULTS_PATH = "./taxos_benchmark_v1/results.jsonl"
REPORT_PATH = "./taxos_benchmark_v1/report.md"

def analyze_results():
    if not os.path.exists(RESULTS_PATH):
        print("No results file found.")
        return

    results = []
    with open(RESULTS_PATH, 'r') as f:
        for line in f:
            try:
                results.append(json.loads(line))
            except: pass

    if not results:
        print("No results to analyze.")
        return

    # 1. Overall Accuracy per Model
    model_stats = defaultdict(lambda: {"correct": 0, "total": 0, "errors": 0})
    
    # 2. Section Accuracy per Model
    # model -> section -> {correct, total}
    section_stats = defaultdict(lambda: defaultdict(lambda: {"correct": 0, "total": 0}))
    
    # 3. Type Accuracy per Model
    type_stats = defaultdict(lambda: defaultdict(lambda: {"correct": 0, "total": 0}))
    
    # 4. Difficulty Accuracy per Model
    diff_stats = defaultdict(lambda: defaultdict(lambda: {"correct": 0, "total": 0}))
    
    # 5. Question Difficulty (across all models)
    # question_id -> {correct, total}
    q_stats = defaultdict(lambda: {"correct": 0, "total": 0, "section": "", "type": ""})

    for r in results:
        model = r['model']
        is_correct = r['is_correct']
        
        # Overall
        model_stats[model]['total'] += 1
        if is_correct:
            model_stats[model]['correct'] += 1
        if r.get('error'):
            model_stats[model]['errors'] += 1
            
        # Section
        sec = r.get('section', 'Unknown')
        section_stats[model][sec]['total'] += 1
        if is_correct:
            section_stats[model][sec]['correct'] += 1
            
        # Type
        q_type = r.get('type', 'Unknown')
        type_stats[model][q_type]['total'] += 1
        if is_correct:
            type_stats[model][q_type]['correct'] += 1
            
        # Difficulty
        diff = r.get('difficulty', 0)
        diff_stats[model][diff]['total'] += 1
        if is_correct:
            diff_stats[model][diff]['correct'] += 1
            
        # Question Stats
        qid = r['question_id']
        q_stats[qid]['total'] += 1
        q_stats[qid]['section'] = sec
        q_stats[qid]['type'] = q_type
        if is_correct:
            q_stats[qid]['correct'] += 1

    # Generate Report
    with open(REPORT_PATH, 'w') as f:
        f.write("# TaxOS Benchmark Evaluation Report\n\n")
        
        # Leaderboard
        f.write("## 1. Model Leaderboard\n\n")
        f.write("| Model | Accuracy | Total Questions | Errors |\n")
        f.write("|---|---|---|---|\n")
        
        sorted_models = sorted(model_stats.items(), key=lambda x: x[1]['correct']/x[1]['total'] if x[1]['total'] > 0 else 0, reverse=True)
        
        for model, stats in sorted_models:
            acc = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
            f.write(f"| {model} | {acc:.2f}% | {stats['total']} | {stats['errors']} |\n")
        
        f.write("\n")
        
        # Weakest Sections (Model Agnostic)
        f.write("## 2. Hardest Sections (Average Accuracy < 50%)\n\n")
        f.write("| Section | Avg Accuracy | Questions Evaluated |\n")
        f.write("|---|---|---|\n")
        
        # Aggregate section stats across all models
        agg_section_stats = defaultdict(lambda: {"correct": 0, "total": 0})
        for model in section_stats:
            for sec, stats in section_stats[model].items():
                agg_section_stats[sec]['correct'] += stats['correct']
                agg_section_stats[sec]['total'] += stats['total']
                
        sorted_sections = sorted(agg_section_stats.items(), key=lambda x: x[1]['correct']/x[1]['total'] if x[1]['total'] > 0 else 0)
        
        for sec, stats in sorted_sections:
            acc = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
            if acc < 50:
                f.write(f"| {sec} | {acc:.2f}% | {stats['total']} |\n")
                
        f.write("\n")
        
        # Performance by Question Type
        f.write("## 3. Performance by Question Type\n\n")
        f.write("| Model | Type | Accuracy |\n")
        f.write("|---|---|---|\n")
        
        for model in type_stats:
            for q_type, stats in type_stats[model].items():
                acc = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
                f.write(f"| {model} | {q_type} | {acc:.2f}% |\n")
                
        f.write("\n")
        
        # Hardest Questions
        f.write("## 4. Hardest Individual Questions (0% Accuracy)\n\n")
        f.write("| Question ID | Section | Type |\n")
        f.write("|---|---|---|\n")
        
        for qid, stats in q_stats.items():
            if stats['correct'] == 0 and stats['total'] > 0:
                f.write(f"| {qid} | {stats['section']} | {stats['type']} |\n")

    print(f"Report generated at {REPORT_PATH}")

if __name__ == "__main__":
    analyze_results()
