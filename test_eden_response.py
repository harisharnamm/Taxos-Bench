import requests
import json
import os

EDENAI_API_KEY = os.getenv("EDENAI_API_KEY")

headers = {
    "Authorization": f"Bearer {EDENAI_API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "providers": "google",
    "settings": { "google": "gemini-2.0-flash" },
    "text": "Hello",
    "chatbot_global_action": "You are a helpful assistant.",
    "temperature": 0.0,
    "max_tokens": 10,
    "fallback_providers": ""
}

response = requests.post(
    "https://api.edenai.run/v2/text/chat",
    headers=headers,
    json=data
)

print(json.dumps(response.json(), indent=2))
