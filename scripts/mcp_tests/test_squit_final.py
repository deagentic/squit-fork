import requests
import json

headers = {
    "X-API-Key": "f6d0f3e1c5f8f4ea054ac19ca8cfc5f84fd967418b714c0be1f0ccd98c53cd1c",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
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

resp = requests.post("https://squit-mcp.deacero.us/mcp", headers=headers, json=payload)
print(resp.status_code)
print(resp.text)
