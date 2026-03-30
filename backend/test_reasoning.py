import requests
import json

url = "http://127.0.0.1:8000/chat"
headers = {
    "X-CoreTex-Key": "treelight-innovation-secure-vault",
    "Content-Type": "application/json"
}
payload = {
    "tier_id": "demo_vault_01",
    "message": "What is the mission statement or core purpose of the Neon Stalker project?",
    "thinking_mode": "high"
}

print("CoreTexAI is thinking (HIGH reasoning mode)...")
response = requests.post(url, headers=headers, json=payload)
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    print(f"\nEngine Response:\n{response.json()['response']}")
else:
    print(f"Error: {response.text}")
