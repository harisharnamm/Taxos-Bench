# Taxos-Bench: U.S. Tax Law Reasoning Benchmark

Taxos-Bench is a large-scale, automated benchmarking suite designed to evaluate the reasoning capabilities of Large Language Models (LLMs) in the domain of U.S. federal tax law. It covers statutory interpretation, complex numeric calculations, and multi-step legal logic derived from the Internal Revenue Code (IRC) and Treasury Regulations.

## 🚀 Overview

Tax reasoning presents a unique challenge for AI: it requires strict adherence to statutory text, handling of deeply nested exceptions, and precise numeric computations. Taxos-Bench provides a rigorous framework to probe these capabilities through:

*   **Statutory Interpretation:** Testing model ability to parse and apply IRC sub-clauses.
*   **Numeric Reasoning:** Validating tax calculations (e.g., tax liability, basis adjustments).
*   **Logical Entailment:** SARA-style (Statutory Reasoning Assistant) logic tests based on Prolog-verified rules.

## 📂 Project Structure

*   `Question Generation/`: Pipelines for generating synthetic tax questions.
    *   `subtitle_a_generator.py`: Specific logic for Income Taxes.
    *   `prolog_manager.py`: Integrates Prolog for verified logical entailment.
*   `taxos_benchmark_v1/`: Core benchmark files and results.
    *   `benchmark_questions.json`: The current evaluation set.
    *   `run_eval.py`: Script to run evaluations across multiple LLMs.
    *   `comprehensive_report.md`: Latest model leaderboard and error analysis.
*   `rule_extraction/`: Tools to convert natural language tax code into structured logical rules.
*   `Scrapers/`: Robust hierarchical scrapers for the Internal Revenue Code.
*   `Data Corpus/`: (External/Excluded) Structured JSON of IRC and Treasury Regulations.

## 🛠 Key Features

- **IRC Scraper:** A comprehensive tool that follows the structure from Subtitles → Chapters → Subchapters → Parts → Sections, preserving tables and definitions.
- **Rule Verification:** Uses a Prolog-based reasoning engine to ensure synthetic questions have ground-truth logical consistency.
- **Multi-Model Support:** Native integration with multiple LLM providers via API to benchmark performance across different architectures.

## 📥 Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/harisharnamm/Taxos-Bench.git
    cd Taxos-Bench
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 📈 Latest Results (v1)

| Model | Accuracy | Avg Latency |
| :--- | :--- | :--- |
| **Mistral Large** | 62.00% | 2.28s |
| **Gemini 2.0 Flash** | 50.00% | 2.41s |
| **GPT-4o** | 48.00% | 2.07s |
| **Claude 3.5 Haiku** | 42.00% | 2.53s |

*For full details, see [taxos_benchmark_v1/comprehensive_report.md](taxos_benchmark_v1/comprehensive_report.md).*

## 📖 Methodology

Taxos-Bench generates questions using three primary methods:
1.  **Statutory Rule Extraction:** Parsing nested IRC clauses into logical predicates.
2.  **Numeric Simulations:** Using formulaic representations of code sections (e.g., §121, §199A) to generate high-variance calculation scenarios.
3.  **Cross-Reference Logic:** Testing ability to navigate complex statutory constraints.

For more details on question generation, see [synthetic_questions_methodology.md](synthetic_questions_methodology.md).

---
*Disclaimer: This tool is for research purposes only and does not constitute tax or legal advice.*
