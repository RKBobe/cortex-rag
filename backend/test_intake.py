import requests
import json

url = "http://127.0.0.1:8000/intake"
headers = {
    "X-CoreTex-Key": "treelight-innovation-secure-vault",
    "Content-Type": "application/json"
}
payload = {
    "repo_url": "https://github.com/RKBobe/neon-stalker",
    "tier_id": "demo_vault_01"
}

response = requests.post(url, headers=headers, json=payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
