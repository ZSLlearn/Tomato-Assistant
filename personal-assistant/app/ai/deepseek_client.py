import requests


class DeepSeekClient:
    BASE = "https://api.deepseek.com/v1"

    def __init__(self, api_key, timeout=30):
        self.api_key = api_key
        self.timeout = timeout

    def chat_completion(self, messages, tools=None, model="deepseek-chat"):
        payload = {"model": model, "messages": messages, "temperature": 0.7}
        if tools:
            payload["tools"] = tools
        resp = requests.post(
            f"{self.BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()
