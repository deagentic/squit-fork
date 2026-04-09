import requests
import json
import os

api_key = os.getenv("SQUIT_API_KEY", "f6d0f3e1c5f8f4ea054ac19ca8cfc5f84fd967418b714c0be1f0ccd98c53cd1c")
# Engañar al servidor diciendo que aceptamos ambos formatos
headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
}

# Payload estándar para listar herramientas, en lugar de llamar a una directamente
# Esto nos permite ver si el endpoint básico de mensajes RPC responde
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
}

try:
    resp = requests.post("https://squit-mcp.deacero.us/mcp", headers=headers, json=payload, timeout=5)
    print(f"Status: {resp.status_code}")
    print(resp.text)
except Exception as e:
    print(e)
