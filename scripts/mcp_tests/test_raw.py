import requests
import json
import os

api_key = os.getenv("SQUIT_API_KEY", "f6d0f3e1c5f8f4ea054ac19ca8cfc5f84fd967418b714c0be1f0ccd98c53cd1c")
headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json",
    # Emular cómo FastMCP espera recibir la petición REST/JSON-RPC directa
    "Accept": "application/json"
}

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

try:
    resp = requests.post("https://squit-mcp.deacero.us/mcp", headers=headers, json=payload, timeout=5)
    print(f"Status: {resp.status_code}")
    print(resp.text)
except Exception as e:
    print(e)
