# TaxOS Benchmark Evaluation Report

## 1. Model Leaderboard

| Model | Accuracy | Total Questions | Errors |
|---|---|---|---|
| mistral/mistral-large-latest | 62.00% | 50 | 6 |
| google/gemini-2.0-flash | 50.00% | 50 | 11 |
| openai/gpt-4o | 48.00% | 50 | 13 |
| anthropic/claude-3-5-haiku-latest | 42.00% | 50 | 8 |
| meta/llama3-1-70b-instruct-v1:0 | 32.00% | 50 | 10 |
| google/gemini-1.5-flash | 0.00% | 50 | 50 |
| anthropic/claude-3.5-sonnet | 0.00% | 50 | 50 |
| meta/llama-3.1-70b-instruct | 0.00% | 50 | 50 |
| google/gemini-1.5-pro | 0.00% | 50 | 50 |
| anthropic/claude-3-5-sonnet-20240620 | 0.00% | 50 | 50 |

## 2. Hardest Sections (Average Accuracy < 50%)

| Section | Avg Accuracy | Questions Evaluated |
|---|---|---|
| 457A | 0.00% | 10 |
| 45 | 0.00% | 10 |
| 503 | 0.00% | 10 |
| 1400Z-2 | 6.67% | 30 |
| 1 | 6.67% | 30 |
| 403 | 10.00% | 10 |
| 953 | 10.00% | 10 |
| 147 | 10.00% | 10 |
| 1235 | 10.00% | 10 |
| 863 | 10.00% | 10 |
| 30C | 10.00% | 10 |
| 51 | 10.00% | 10 |
| 61 | 13.33% | 30 |
| 512 | 20.00% | 10 |
| 409 | 20.00% | 10 |
| 664 | 20.00% | 10 |
| 448 | 20.00% | 10 |
| 199A | 26.67% | 30 |
| 163 | 26.67% | 30 |
| 469 | 30.00% | 30 |
| 507 | 30.00% | 10 |
| 144 | 30.00% | 10 |
| 162 | 33.33% | 30 |
| 170 | 36.67% | 30 |
| 25C | 40.00% | 10 |
| 941 | 40.00% | 10 |
| 121 | 40.00% | 30 |
| 1202 | 40.00% | 10 |
| 467 | 40.00% | 10 |
| 47 | 40.00% | 10 |

## 3. Performance by Question Type

| Model | Type | Accuracy |
|---|---|---|
| openai/gpt-4o | Calculation - Gross Income | 33.33% |
| openai/gpt-4o | Complex - Opportunity Zone Basis Adjustment | 33.33% |
| openai/gpt-4o | Calculation - Business Expenses | 100.00% |
| openai/gpt-4o | Recall - Numeric | 50.00% |
| openai/gpt-4o | Complex - Charitable Contribution Limit | 66.67% |
| openai/gpt-4o | Recall - Percentage | 36.36% |
| openai/gpt-4o | Complex - Passive Activity Loss | 66.67% |
| openai/gpt-4o | Calculation - QBI Deduction | 33.33% |
| openai/gpt-4o | Calculation - Interest Deduction | 66.67% |
| openai/gpt-4o | Calculation - Residence Exclusion | 66.67% |
| openai/gpt-4o | Calculation - Tax Liability | 0.00% |
| google/gemini-1.5-flash | Calculation - Gross Income | 0.00% |
| google/gemini-1.5-flash | Complex - Opportunity Zone Basis Adjustment | 0.00% |
| google/gemini-1.5-flash | Calculation - Business Expenses | 0.00% |
| google/gemini-1.5-flash | Recall - Numeric | 0.00% |
| google/gemini-1.5-flash | Complex - Charitable Contribution Limit | 0.00% |
| google/gemini-1.5-flash | Recall - Percentage | 0.00% |
| google/gemini-1.5-flash | Complex - Passive Activity Loss | 0.00% |
| google/gemini-1.5-flash | Calculation - QBI Deduction | 0.00% |
| google/gemini-1.5-flash | Calculation - Interest Deduction | 0.00% |
| google/gemini-1.5-flash | Calculation - Residence Exclusion | 0.00% |
| google/gemini-1.5-flash | Calculation - Tax Liability | 0.00% |
| anthropic/claude-3.5-sonnet | Calculation - Gross Income | 0.00% |
| anthropic/claude-3.5-sonnet | Complex - Opportunity Zone Basis Adjustment | 0.00% |
| anthropic/claude-3.5-sonnet | Calculation - Business Expenses | 0.00% |
| anthropic/claude-3.5-sonnet | Recall - Numeric | 0.00% |
| anthropic/claude-3.5-sonnet | Complex - Charitable Contribution Limit | 0.00% |
| anthropic/claude-3.5-sonnet | Recall - Percentage | 0.00% |
| anthropic/claude-3.5-sonnet | Complex - Passive Activity Loss | 0.00% |
| anthropic/claude-3.5-sonnet | Calculation - QBI Deduction | 0.00% |
| anthropic/claude-3.5-sonnet | Calculation - Interest Deduction | 0.00% |
| anthropic/claude-3.5-sonnet | Calculation - Residence Exclusion | 0.00% |
| anthropic/claude-3.5-sonnet | Calculation - Tax Liability | 0.00% |
| mistral/mistral-large-latest | Calculation - Gross Income | 66.67% |
| mistral/mistral-large-latest | Complex - Opportunity Zone Basis Adjustment | 33.33% |
| mistral/mistral-large-latest | Calculation - Business Expenses | 66.67% |
| mistral/mistral-large-latest | Recall - Numeric | 41.67% |
| mistral/mistral-large-latest | Complex - Charitable Contribution Limit | 100.00% |
| mistral/mistral-large-latest | Recall - Percentage | 54.55% |
| mistral/mistral-large-latest | Complex - Passive Activity Loss | 100.00% |
| mistral/mistral-large-latest | Calculation - QBI Deduction | 100.00% |
| mistral/mistral-large-latest | Calculation - Interest Deduction | 66.67% |
| mistral/mistral-large-latest | Calculation - Residence Exclusion | 100.00% |
| mistral/mistral-large-latest | Calculation - Tax Liability | 33.33% |
| meta/llama-3.1-70b-instruct | Calculation - Gross Income | 0.00% |
| meta/llama-3.1-70b-instruct | Complex - Opportunity Zone Basis Adjustment | 0.00% |
| meta/llama-3.1-70b-instruct | Calculation - Business Expenses | 0.00% |
| meta/llama-3.1-70b-instruct | Recall - Numeric | 0.00% |
| meta/llama-3.1-70b-instruct | Complex - Charitable Contribution Limit | 0.00% |
| meta/llama-3.1-70b-instruct | Recall - Percentage | 0.00% |
| meta/llama-3.1-70b-instruct | Complex - Passive Activity Loss | 0.00% |
| meta/llama-3.1-70b-instruct | Calculation - QBI Deduction | 0.00% |
| meta/llama-3.1-70b-instruct | Calculation - Interest Deduction | 0.00% |
| meta/llama-3.1-70b-instruct | Calculation - Residence Exclusion | 0.00% |
| meta/llama-3.1-70b-instruct | Calculation - Tax Liability | 0.00% |
| google/gemini-1.5-pro | Calculation - Gross Income | 0.00% |
| google/gemini-1.5-pro | Complex - Opportunity Zone Basis Adjustment | 0.00% |
| google/gemini-1.5-pro | Calculation - Business Expenses | 0.00% |
| google/gemini-1.5-pro | Recall - Numeric | 0.00% |
| google/gemini-1.5-pro | Complex - Charitable Contribution Limit | 0.00% |
| google/gemini-1.5-pro | Recall - Percentage | 0.00% |
| google/gemini-1.5-pro | Complex - Passive Activity Loss | 0.00% |
| google/gemini-1.5-pro | Calculation - QBI Deduction | 0.00% |
| google/gemini-1.5-pro | Calculation - Interest Deduction | 0.00% |
| google/gemini-1.5-pro | Calculation - Residence Exclusion | 0.00% |
| google/gemini-1.5-pro | Calculation - Tax Liability | 0.00% |
| anthropic/claude-3-5-sonnet-20240620 | Calculation - Gross Income | 0.00% |
| anthropic/claude-3-5-sonnet-20240620 | Complex - Opportunity Zone Basis Adjustment | 0.00% |
| anthropic/claude-3-5-sonnet-20240620 | Calculation - Business Expenses | 0.00% |
| anthropic/claude-3-5-sonnet-20240620 | Recall - Numeric | 0.00% |
| anthropic/claude-3-5-sonnet-20240620 | Complex - Charitable Contribution Limit | 0.00% |
| anthropic/claude-3-5-sonnet-20240620 | Recall - Percentage | 0.00% |
| anthropic/claude-3-5-sonnet-20240620 | Complex - Passive Activity Loss | 0.00% |
| anthropic/claude-3-5-sonnet-20240620 | Calculation - QBI Deduction | 0.00% |
| anthropic/claude-3-5-sonnet-20240620 | Calculation - Interest Deduction | 0.00% |
| anthropic/claude-3-5-sonnet-20240620 | Calculation - Residence Exclusion | 0.00% |
| anthropic/claude-3-5-sonnet-20240620 | Calculation - Tax Liability | 0.00% |
| meta/llama3-1-70b-instruct-v1:0 | Calculation - Gross Income | 0.00% |
| meta/llama3-1-70b-instruct-v1:0 | Complex - Opportunity Zone Basis Adjustment | 0.00% |
| meta/llama3-1-70b-instruct-v1:0 | Calculation - Business Expenses | 100.00% |
| meta/llama3-1-70b-instruct-v1:0 | Recall - Numeric | 33.33% |
| meta/llama3-1-70b-instruct-v1:0 | Complex - Charitable Contribution Limit | 100.00% |
| meta/llama3-1-70b-instruct-v1:0 | Recall - Percentage | 27.27% |
| meta/llama3-1-70b-instruct-v1:0 | Complex - Passive Activity Loss | 0.00% |
| meta/llama3-1-70b-instruct-v1:0 | Calculation - QBI Deduction | 33.33% |
| meta/llama3-1-70b-instruct-v1:0 | Calculation - Interest Deduction | 33.33% |
| meta/llama3-1-70b-instruct-v1:0 | Calculation - Residence Exclusion | 33.33% |
| meta/llama3-1-70b-instruct-v1:0 | Calculation - Tax Liability | 0.00% |
| google/gemini-2.0-flash | Calculation - Gross Income | 33.33% |
| google/gemini-2.0-flash | Complex - Opportunity Zone Basis Adjustment | 0.00% |
| google/gemini-2.0-flash | Calculation - Business Expenses | 66.67% |
| google/gemini-2.0-flash | Recall - Numeric | 41.67% |
| google/gemini-2.0-flash | Complex - Charitable Contribution Limit | 100.00% |
| google/gemini-2.0-flash | Recall - Percentage | 54.55% |
| google/gemini-2.0-flash | Complex - Passive Activity Loss | 100.00% |
| google/gemini-2.0-flash | Calculation - QBI Deduction | 33.33% |
| google/gemini-2.0-flash | Calculation - Interest Deduction | 33.33% |
| google/gemini-2.0-flash | Calculation - Residence Exclusion | 100.00% |
| google/gemini-2.0-flash | Calculation - Tax Liability | 0.00% |
| anthropic/claude-3-5-haiku-latest | Calculation - Gross Income | 0.00% |
| anthropic/claude-3-5-haiku-latest | Complex - Opportunity Zone Basis Adjustment | 0.00% |
| anthropic/claude-3-5-haiku-latest | Calculation - Business Expenses | 0.00% |
| anthropic/claude-3-5-haiku-latest | Recall - Numeric | 50.00% |
| anthropic/claude-3-5-haiku-latest | Complex - Charitable Contribution Limit | 0.00% |
| anthropic/claude-3-5-haiku-latest | Recall - Percentage | 54.55% |
| anthropic/claude-3-5-haiku-latest | Complex - Passive Activity Loss | 33.33% |
| anthropic/claude-3-5-haiku-latest | Calculation - QBI Deduction | 66.67% |
| anthropic/claude-3-5-haiku-latest | Calculation - Interest Deduction | 66.67% |
| anthropic/claude-3-5-haiku-latest | Calculation - Residence Exclusion | 100.00% |
| anthropic/claude-3-5-haiku-latest | Calculation - Tax Liability | 33.33% |

## 4. Hardest Individual Questions (0% Accuracy)

| Question ID | Section | Type |
|---|---|---|
| 083011381661 | 1400Z-2 | Complex - Opportunity Zone Basis Adjustment |
| 242b46e6680f | 457A | Recall - Percentage |
| fc7a04e5fcf0 | 1400Z-2 | Complex - Opportunity Zone Basis Adjustment |
| 398fd5d829e4 | 45 | Recall - Numeric |
| 77aecba93c91 | 503 | Recall - Percentage |
| 93c60b9fdc89 | 1 | Calculation - Tax Liability |
