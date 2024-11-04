import requests
import json

def ai_response(url, key ,model ,content):
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    data = {
        'model': model,
        'temperature': 0.2,
        'max_tokens': 100,
        'messages': [
            {
                "role": "user",
                "content": content
            }
        ]
    }
    json.dumps(data)
    response = requests.post(url, data=json.dumps(data), headers=headers)
    story = response.json()["choices"][0]["message"]["content"]
    return story