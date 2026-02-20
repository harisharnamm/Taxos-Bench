# TaxOS Benchmark: Comprehensive Report

## Executive Summary
The benchmark evaluated **5 models** on a dataset of **50 tax law questions**.
The top-performing model is **mistral-large-latest** with an accuracy of **62.00%**.

## 1. Leaderboard
| specific_model | Accuracy | Avg_Latency | Total_Questions | Successful_Responses |
| --- | --- | --- | --- | --- |
| mistral-large-latest | 62.00% | 2.28s | 50 | 44 |
| gemini-2.0-flash | 50.00% | 2.41s | 50 | 39 |
| gpt-4o | 48.00% | 2.07s | 50 | 37 |
| claude-3-5-haiku-latest | 42.00% | 2.53s | 50 | 42 |
| llama3-1-70b-instruct-v1:0 | 32.00% | 2.46s | 50 | 40 |


## 2. Performance by Category
Breakdown of accuracy by question type (Recall vs. Calculation vs. Complex).

| specific_model | Calculation | Complex | Recall |
| --- | --- | --- | --- |
| claude-3-5-haiku-latest | 44.44% | 11.11% | 52.17% |
| gemini-2.0-flash | 44.44% | 66.67% | 47.83% |
| gpt-4o | 50.00% | 55.56% | 43.48% |
| llama3-1-70b-instruct-v1:0 | 33.33% | 33.33% | 30.43% |
| mistral-large-latest | 72.22% | 77.78% | 47.83% |


## 3. Performance by Difficulty
Accuracy breakdown by difficulty level (1 = Easiest, 4 = Hardest).

| specific_model | 1 | 2 | 3 | 4 |
| --- | --- | --- | --- | --- |
| claude-3-5-haiku-latest | 52.17% | 25.00% | 50.00% | 0.00% |
| gemini-2.0-flash | 47.83% | 33.33% | 83.33% | 0.00% |
| gpt-4o | 43.48% | 50.00% | 58.33% | 33.33% |
| llama3-1-70b-instruct-v1:0 | 30.43% | 33.33% | 41.67% | 0.00% |
| mistral-large-latest | 47.83% | 58.33% | 100.00% | 33.33% |


## 4. Hardest Questions
Questions with the lowest average accuracy across all models.

| Section | Type | Avg Accuracy | Question ID |
|---|---|---|---|
| 1 | Calculation - Tax Liability | 0.00% | 93c60b9fdc89 |
| 1400Z-2 | Complex - Opportunity Zone Basis Adjustment | 0.00% | 083011381661 |
| 503 | Recall - Percentage | 0.00% | 77aecba93c91 |
| 457A | Recall - Percentage | 0.00% | 242b46e6680f |
| 45 | Recall - Numeric | 0.00% | 398fd5d829e4 |


## 5. Error Analysis
Analysis of API errors vs. Incorrect answers.

| specific_model | API_Errors | Incorrect_Answers | Total |
| --- | --- | --- | --- |
| claude-3-5-haiku-latest | 8 | 29 | 50 |
| gemini-2.0-flash | 11 | 25 | 50 |
| gpt-4o | 13 | 26 | 50 |
| llama3-1-70b-instruct-v1:0 | 10 | 34 | 50 |
| mistral-large-latest | 6 | 19 | 50 |


