import json
import pandas as pd
import os
from collections import defaultdict

RESULTS_FILE = "taxos_benchmark_v1/results.jsonl"
REPORT_FILE = "taxos_benchmark_v1/comprehensive_report.md"

def load_results():
    data = []
    if not os.path.exists(RESULTS_FILE):
        return []
    
    with open(RESULTS_FILE, 'r') as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except:
                continue
    return data

def generate_report():
    raw_data = load_results()
    if not raw_data:
        print("No results found.")
        return

    df = pd.DataFrame(raw_data)
    
    # Deduplicate: Keep the latest run for each (specific_model, question_id)
    # Sort by timestamp descending first
    if 'timestamp' in df.columns:
        df = df.sort_values('timestamp', ascending=False)
    
    # We want to analyze the *latest* full run for each model.
    # However, since we ran models in batches, we should just group by specific_model and question_id and take the latest.
    df_latest = df.drop_duplicates(subset=['specific_model', 'question_id'], keep='first')
    
    # Filter out models with very few results (incomplete runs) or high error rates (failed configs)
    # Calculate error rate per model
    model_stats = df_latest.groupby('specific_model').agg(
        total_questions=('question_id', 'count'),
        errors=('error', lambda x: x.notnull().sum())
    )
    
    # Filter out models where error rate is > 80% (likely invalid model string)
    valid_models = model_stats[model_stats['errors'] / model_stats['total_questions'] < 0.8].index.tolist()
    df_clean = df_latest[df_latest['specific_model'].isin(valid_models)].copy()
    
    def df_to_markdown(df):
        if df.empty:
            return "No data available."
        # Add index as a column if it's not a range index
        if not isinstance(df.index, pd.RangeIndex):
            df = df.reset_index()
        
        columns = [str(c) for c in df.columns.tolist()]
        # Header
        md = "| " + " | ".join(columns) + " |\n"
        # Separator
        md += "| " + " | ".join(["---"] * len(columns)) + " |\n"
        # Rows
        for _, row in df.iterrows():
            md += "| " + " | ".join(str(row[col]) for col in df.columns) + " |\n"
        return md

    # --- Metrics Calculation ---
    
    # 1. Overall Leaderboard
    leaderboard = df_clean.groupby('specific_model').agg(
        Accuracy=('is_correct', 'mean'),
        Avg_Latency=('latency', 'mean'),
        Total_Questions=('question_id', 'count'),
        Successful_Responses=('error', lambda x: x.isnull().sum())
    ).sort_values('Accuracy', ascending=False)
    
    # Format
    leaderboard['Accuracy'] = leaderboard['Accuracy'].apply(lambda x: f"{x:.2%}")
    leaderboard['Avg_Latency'] = leaderboard['Avg_Latency'].apply(lambda x: f"{x:.2f}s")
    
    # 2. Category Analysis (Type)
    # Extract broad category (Recall, Calculation, Complex)
    df_clean['Category'] = df_clean['type'].apply(lambda x: x.split(' - ')[0] if ' - ' in x else x)
    
    category_perf = df_clean.groupby(['specific_model', 'Category'])['is_correct'].mean().unstack()
    # Use map instead of applymap for newer pandas, or applymap for older. 
    # To be safe, let's just iterate or use apply.
    category_perf = category_perf.apply(lambda x: x.map(lambda y: f"{y:.2%}" if pd.notnull(y) else "-"))
    
    # 3. Difficulty Analysis
    difficulty_perf = df_clean.groupby(['specific_model', 'difficulty'])['is_correct'].mean().unstack()
    difficulty_perf = difficulty_perf.apply(lambda x: x.map(lambda y: f"{y:.2%}" if pd.notnull(y) else "-"))
    
    # 4. Hardest Questions (Low accuracy across all models)
    question_perf = df_clean.groupby(['question_id', 'section', 'type'])['is_correct'].mean().reset_index()
    hardest_questions = question_perf.sort_values('is_correct').head(5)
    
    # --- Report Generation ---
    
    with open(REPORT_FILE, 'w') as f:
        f.write("# TaxOS Benchmark: Comprehensive Report\n\n")
        
        f.write("## Executive Summary\n")
        if not leaderboard.empty:
            top_model = leaderboard.index[0]
            top_acc = leaderboard.iloc[0]['Accuracy']
            f.write(f"The benchmark evaluated **{len(valid_models)} models** on a dataset of **50 tax law questions**.\n")
            f.write(f"The top-performing model is **{top_model}** with an accuracy of **{top_acc}**.\n\n")
        else:
            f.write("No valid model results found.\n\n")
        
        f.write("## 1. Leaderboard\n")
        f.write(df_to_markdown(leaderboard))
        f.write("\n\n")
        
        f.write("## 2. Performance by Category\n")
        f.write("Breakdown of accuracy by question type (Recall vs. Calculation vs. Complex).\n\n")
        f.write(df_to_markdown(category_perf))
        f.write("\n\n")
        
        f.write("## 3. Performance by Difficulty\n")
        f.write("Accuracy breakdown by difficulty level (1 = Easiest, 4 = Hardest).\n\n")
        f.write(df_to_markdown(difficulty_perf))
        f.write("\n\n")
        
        f.write("## 4. Hardest Questions\n")
        f.write("Questions with the lowest average accuracy across all models.\n\n")
        f.write("| Section | Type | Avg Accuracy | Question ID |\n")
        f.write("|---|---|---|---|\n")
        for _, row in hardest_questions.iterrows():
            f.write(f"| {row['section']} | {row['type']} | {row['is_correct']:.2%} | {row['question_id']} |\n")
        f.write("\n\n")
        
        f.write("## 5. Error Analysis\n")
        f.write("Analysis of API errors vs. Incorrect answers.\n\n")
        error_stats = df_clean.groupby('specific_model').agg(
            API_Errors=('error', lambda x: x.notnull().sum()),
            Incorrect_Answers=('is_correct', lambda x: (~x & x.notnull()).sum()), # False and not null (null is error)
            Total=('question_id', 'count')
        )
        f.write(df_to_markdown(error_stats))
        f.write("\n\n")

    print(f"Comprehensive report generated at {REPORT_FILE}")

if __name__ == "__main__":
    generate_report()
