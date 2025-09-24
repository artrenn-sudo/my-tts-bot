import os, requests
API_KEY = os.environ["GEMINI_API_KEY"]
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
r = requests.post(url, params={"key": API_KEY}, json={
  "contents":[{"parts":[{"text":"từ chính xác có dấu của duahau là gì"}]}]
})
print(r.json()["candidates"][0]["content"]["parts"][0]["text"])
