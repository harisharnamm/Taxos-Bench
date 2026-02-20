.

**📘 Taxos Benchmark — Question Generation Pipeline & Methodology**
===================================================================

A comprehensive, end-to-end description of how Taxos generates high-quality statutory tax-reasoning questions._

**1\. Overview**
----------------

Taxos is a large-scale benchmark for evaluating LLMs on **U.S. tax-law reasoning**, covering:

*   Statutory interpretation
    
*   Numeric and algebraic reasoning
    
*   Exception handling
    
*   Multi-step legal logic
    
*   Cross-references across the Internal Revenue Code (IRC)
    

Taxos combines **automatic rule extraction**, **synthetic numeric simulations**, and **SARA-style Prolog entailment logic** to create a diverse and rigorous benchmark.

This document details:

*   Data sources
    
*   Architecture
    
*   Algorithms for question generation
    
*   Subtitle coverage
    
*   Evaluation methodology
    
*   Quality assurance pipeline
    
**2\. Data Sources**
====================

Taxos integrates three major data inputs.

**2.1 Internal Revenue Code (IRC) — Structured JSON**
-----------------------------------------------------

Each section of the IRC is parsed into:

*   Section number
    
*   Citation
    
*   Heading
    
*   Subsections
    
*   Clauses
    
*   Full text
    
*   Clean HTML-stripped content
    

The structure follows:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Subtitle → Chapter → Section → Subsection → Paragraph → Clause   `

This allows rule extraction from even deeply nested statutory logic.

**2.2 Synthetic Rule Templates**
--------------------------------

These represent real-world tax computations, each mirroring statutory formulas:

*   §121 — Principal residence exclusion
    
*   §163(j) — Business interest limitation
    
*   §170 — Charitable contribution AGI limits
    
*   §351–§358 — Corporate basis, liabilities, control
    
*   §704(d) / §465 / §469 — Loss limitation stack
    
*   §199A — Qualified Business Income deduction
    
*   §1231 — Netting and lookback
    
*   §1400Z-2 — Opportunity zone basis step-ups
    

Templates allow high-variance numeric scenarios with deterministic outcomes.

**2.3 Prolog Rulebase (SARA-style)**
------------------------------------

Inspired by Stanford’s SARA work, Taxos maintains a simplified Prolog rulebase for statutory logic.

Each predicate models a statutory condition:

*   qualifies\_121(Person,Year)
    
*   allowed\_charitable\_deduction(Person,Year,Amount)
    
*   allowed\_passive\_loss(Person,Activity,Year,Allowed)
    

This enables binary entailment cases (Entail/Contradiction) and numeric evaluations.

**3\. Architecture Overview**
=============================

Taxos is implemented in **three generation layers**:

1.  **Corpus-driven rule extraction**
    
2.  **Template-based synthetic numeric computation**
    
3.  **Prolog entailment-based logical reasoning (SARA-style)**
    

This hybrid approach ensures coverage breadth, realism, and depth.

**4\. Layer 1 — Corpus-Driven Rule Extraction**
===============================================

This system parses the IRC text and identifies:

*   Percentages
    
*   Thresholds
    
*   Time rules
    
*   Exceptions
    
*   Definitions
    
*   Basis and gain formulas
    
*   Cross-reference logic
    

### **4.1 Example: Extracted Rule Object**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   {    "section": 170,    "subsection": "(b)(1)(A)",    "rule_type": "percentage_limit",    "value": 0.60,    "trigger": "charitable contribution AGI limit"  }   `

### **4.2 Generator Output Example**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   {    "section": "170",    "citation": "I.R.C. § 170(b)(1)(A)",    "scenario": "Alice has AGI of $120,000 and donates $90,000 to a public charity.",    "question": "What is the maximum deductible charitable contribution?",    "choices": ["$90,000", "$72,000", "$60,000", "$45,000"],    "correct_choice_index": 1,    "answer_explanation": "60% AGI limit applies → 0.6 × 120,000 = 72,000.",    "difficulty": 2,    "source_rules": ["§170(b)(1)(A)"]  }   `

**5\. Layer 2 — Template-Based Numeric Simulation**
===================================================

For complex computation statutes, Taxos uses numeric templates with:

*   Randomized taxpayer profiles
    
*   Multiple taxable years
    
*   Variable filing statuses
    
*   Multi-step interactions
    
*   Deterministic answer computation
    

### **5.1 Example: Corporate Formation Scenario**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Alice transfers property basis $20,000 FMV $200,000 with $50,000 liability to NewCo in §351 exchange.   `

**Correct rule chain:**§351 → §357(c) → §358(a)

**Output MCQ:**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   {    "section": "357(c)",    "type": "Calculation - Recognized Gain",    "choices": ["$0", "$20,000", "$30,000", "$50,000"],    "correct_choice_index": 2,    "answer_explanation": "Liability ($50k) exceeds basis ($20k) → recognized gain = 30k."  }   `

Templates dramatically expand the diversity beyond what text-extraction alone can produce.

**6\. Layer 3 — SARA-Style Prolog Entailment Generator**
========================================================

Taxos extends SARA’s methodology to real tax law.

### **6.1 Pipeline**

1.  Generate a fact pattern
    
2.  Convert to Prolog facts
    
3.  Choose a statutory predicate
    
4.  Run query in SWI-Prolog
    
5.  Record result as:
    
    *   "Entailment"
        
    *   "Contradiction"
        
    *   **numeric** value (computed by Prolog)
        

### **6.2 Example Output**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   {    "text": "Alice lived at the property for 26 months out of the 5 years before sale.",    "question": "Does Alice qualify for the §121 exclusion?",    "facts": "residence(alice, home1, '2020-01-01', '2022-03-01'). sale(alice, home1, 2023).",    "query": "qualifies_121(alice,2023).",    "answer": "Entailment",    "source_rules": ["§121"]  }   `

**7\. Subtitle Coverage (A → K)**
=================================

Taxos originally focused on Subtitle A (Income Taxes).We now extend to Subtitles **B–K**, where we:

1.  Randomly choose actionable sections
    
2.  Extract rules where meaningful
    
3.  Produce valid MCQs or entailment cases
    
4.  Skip empty declarative sections
    

This produces broad statutory coverage without manually coding rules for all ~3000 sections.

**8\. Question Format Standards**
=================================

All Taxos MCQs must contain **exactly four choices**.

### **8.1 Required Fields**

*   id
    
*   section
    
*   citation
    
*   type
    
*   scenario
    
*   question
    
*   choices (length = 4)
    
*   correct\_choice\_index
    
*   answer\_explanation
    
*   reasoning
    
*   difficulty
    
*   source\_rules
    

### **8.2 Difficulty Rubric**

LevelDescription1Single-step threshold or definition2Basic statutory application3Multi-step numeric reasoning4Cross-section interactions5Complex exceptions + multi-rule chain

**9\. Quality Assurance System**
================================

### **9.1 Automated Validators**

*   Correct schema
    
*   Exactly 4 answer choices
    
*   Deduplication via MD5 hashing
    
*   Difficulty scoring consistency
    

### **9.2 LLM-Assisted Review**

Small random batches evaluated using:

*   GPT-4.1
    
*   Claude 3.5 Sonnet
    
*   OpenAI o3-mini
    

The models check:

*   clarity
    
*   correctness
    
*   distractor quality
    
*   ambiguity
    

### **9.3 Human Review**

Manual spot checks focus on:

*   ambiguous statute sections
    
*   edge-case numeric computations
    
*   multi-year logic
    

**10\. Evaluation Methodology for Models**
==========================================

Taxos defines two evaluation tracks.

**Track A — MCQ Accuracy**
--------------------------

For each question:

1.  Model must answer with "A", "B", "C", or "D"
    
2.  Compare against gold answer index
    
3.  Compute:
    
    *   Overall accuracy
        
    *   Accuracy per-difficulty
        
    *   Accuracy per-section
        
    *   Accuracy per-subtitle
        

Ideal for leaderboard-style model comparison.

**Track B — Regulation-Level Q&A (Short Answer)**
-------------------------------------------------

For tax regulations (non-IRC) or open-ended statutory Q&A, evaluation uses:

*   **Exact-match** where possible
    
*   **LLM-as-judge** for interpretive questions
    
*   **Rubric-based scoring**
    

This allows evaluating not only numeric answers but text-based reasoning quality.

**11\. Summary of Taxos Generation Methodology**
================================================

Here is the complete strategy in one unified view:

1.  **Extract rules** directly from IRC text
    
2.  **Detect numeric limits, thresholds, time rules**
    
3.  **Generate MCQs** from extracted rules
    
4.  **Generate deep numeric problems** using structured templates
    
5.  **Create Prolog entailment tasks** for logical evaluation
    
6.  **Apply strict formatting rules** (4 choices, explanations, citation)
    
7.  **Expand coverage** across Subtitles A–K
    
8.  **Validate quality** through both automated and LLM review
    
9.  **Use the dataset to benchmark LLMs** on tax reasoning
    

Taxos is therefore:

*   **Corpus-grounded**
    
*   **Programmatically verifiable**
    
*   **High-variance**
    
*   **Legally accurate**
    
*   **Statistically robust**