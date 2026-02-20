import json
import os
import requests
import time
import re
import os

# Configuration
# It's recommended to set this as environment variable: export EDENAI_API_KEY='your_key'
EDENAI_API_KEY = os.getenv("EDENAI_API_KEY")
EVAL_SET_PATH = "./taxos_benchmark_v1/benchmark_questions.json"
RESULTS_PATH = "./taxos_benchmark_v1/results.jsonl"
PROMPT_PATH = "./taxos_benchmark_v1/evaluation_prompt.txt"

# Providers and specific models to evaluate on Eden AI
# Format: (provider, model_name)
MODELS_CONFIG = [
    ("google", "gemini-2.0-flash"),
    ("anthropic", "claude-3-5-haiku-latest")
]

def load_prompt():
    with open(PROMPT_PATH, 'r') as f:
        return f.read()

def format_question_for_model(q):
    choices_text = ""
    letters = ['A', 'B', 'C', 'D', 'E']
    for i, choice in enumerate(q['choices']):
        if i < len(letters):
            choices_text += f"{letters[i]}) {choice}\n"
    
    user_content = f"Scenario: {q['scenario']}\nQuestion: {q['question']}\nChoices:\n{choices_text}"
    return user_content

def call_edenai(provider, model, system_prompt, user_prompt):
    if not EDENAI_API_KEY:
        return {"error": "Missing API Key"}
        
    headers = {
        "Authorization": f"Bearer {EDENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "providers": provider,
        "settings": { provider: model },
        "text": user_prompt,
        "chatbot_global_action": system_prompt,
        "temperature": 0.0,
        "max_tokens": 10,
        "fallback_providers": ""
    }
    
    max_retries = 3
    base_delay = 2

    for attempt in range(max_retries):
        try:
            response = requests.post(
                "https://api.edenai.run/v2/text/chat",
                headers=headers,
                json=data,
                timeout=45
            )
            
            if response.status_code == 429:
                delay = base_delay * (2 ** attempt)
                print(f"Rate limited. Retrying in {delay}s...")
                time.sleep(delay)
                continue
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt == max_retries - 1:
                return {"error": str(e)}
            time.sleep(1)
            
    return {"error": "Max retries exceeded"}

def normalize_answer(raw_output):
    if not raw_output:
        return None
    
    # Clean whitespace
    text = raw_output.strip()
    
    # 1. Check for single letter
    if len(text) == 1 and text.upper() in ['A', 'B', 'C', 'D', 'E']:
        return text.upper()
    
    # 2. Check for "A)" or "A."
    match = re.match(r"^([A-E])[\)\.]", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
        
    # 3. Check for "The answer is A"
    match = re.search(r"answer is ([A-E])", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
        
    # 4. Last resort: look for the last capital letter A-E
    matches = re.findall(r"\b([A-E])\b", text.upper())
    if matches:
        return matches[-1] 
        
    return "INVALID"

def run_evaluation():
    if not EDENAI_API_KEY:
        print("Error: EDENAI_API_KEY environment variable not set.")
        print("Please run: export EDENAI_API_KEY='your_key_here'")
        return

    print("Loading evaluation set...")
    questions = []
    with open(EVAL_SET_PATH, 'r') as f:
        if EVAL_SET_PATH.endswith('.jsonl'):
            for line in f:
                questions.append(json.loads(line))
        else:
            questions = json.load(f)
            
    system_prompt = load_prompt()
    
    # Load existing results to resume if needed
    processed_ids = set()
    if os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH, 'r') as f:
            for line in f:
                try:
                    res = json.loads(line)
                    processed_ids.add((res['model'], res['question_id']))
                except: pass
    
    print(f"Starting evaluation of {len(questions)} questions on {len(MODELS_CONFIG)} models...")
    
    with open(RESULTS_PATH, 'a') as f_out:
        for provider, model_name in MODELS_CONFIG:
            full_model_id = f"{provider}/{model_name}"
            print(f"Evaluating model: {full_model_id}")
            
            for q in questions:
                if (full_model_id, q['id']) in processed_ids:
                    continue
                
                user_prompt = format_question_for_model(q)
                
                start_time = time.time()
                response = call_edenai(provider, model_name, system_prompt, user_prompt)
                latency = time.time() - start_time
                
                raw_output = ""
                error = None
                
                if "error" in response:
                    error = response["error"]
                    print(f"  Error on {q['id']}: {error}")
                else:
                    try:
                        # Eden AI response structure: { "openai": { "generated_text": "...", ... } }
                        provider_response = response.get(provider, {})
                        if provider_response.get('status') == 'success':
                            raw_output = provider_response.get('generated_text', '')
                        else:
                            error = provider_response.get('error', {}).get('message', 'Unknown error')
                            if not error:
                                raw_output = str(provider_response)
                    except Exception as e:
                        error = f"Parsing error: {str(e)}"
                        raw_output = str(response)
                
                normalized = normalize_answer(raw_output)
                
                # Determine correctness
                letters = ['A', 'B', 'C', 'D', 'E']
                correct_letter = letters[q['correct_choice_index']]
                is_correct = (normalized == correct_letter)
                
                result_record = {
                    "model": full_model_id,
                    "provider": provider,
                    "specific_model": model_name,
                    "question_id": q['id'],
                    "section": q['section'],
                    "type": q['type'],
                    "difficulty": q['difficulty'],
                    "correct_letter": correct_letter,
                    "raw_output": raw_output,
                    "normalized_output": normalized,
                    "is_correct": is_correct,
                    "latency": latency,
                    "error": error,
                    "timestamp": time.time()
                }
                
                f_out.write(json.dumps(result_record) + "\n")
                f_out.flush()
                
                # Rate limit niceness
                time.sleep(0.5)

    print("Evaluation complete.")

if __name__ == "__main__":
    run_evaluation()
