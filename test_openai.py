import os, httpx

print("KEY ↠", repr(os.getenv("OPENAI_API_KEY")))

resp = httpx.post(
    "https://api.openai.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"},
    json={
      "model": "gpt-3.5-turbo",
      "messages": [{"role":"user","content":"Say hello"}]
    }
)
print("STATUS:", resp.status_code)
print("BODY:", resp.text)
