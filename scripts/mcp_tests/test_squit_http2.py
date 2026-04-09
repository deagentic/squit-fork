import requests
import json
import os

api_key = os.getenv("SQUIT_API_KEY", "f6d0f3e1c5f8f4ea054ac19ca8cfc5f84fd967418b714c0be1f0ccd98c53cd1c")
headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

# FastMCP a veces usa la raíz para las llamadas POST cuando se monta con app = mcp.http_app()
endpoints = [
    "https://squit-mcp.deacero.us/mcp",
    "https://squit-mcp.deacero.us/",
    "https://squit-mcp.deacero.us/tools/call"
]

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "squit_search",
        "arguments": {
            "query": "login",
            "limit": 2
        }
    }
}

for ep in endpoints:
    print(f"\nProbando {ep}...")
    try:
        resp = requests.post(ep, headers=headers, json=payload, timeout=5)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(json.dumps(resp.json(), indent=2))
        else:
            print(resp.text[:200])
    except Exception as e:
        print(e)
