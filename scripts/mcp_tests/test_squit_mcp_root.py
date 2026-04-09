import asyncio
from mcp.client.sse import sse_client
import json

async def run():
    url = "https://squit-mcp.deacero.us/sse"  # Probando sin /mcp
    print(f"🔄 Conectando a {url}...")
    try:
        async with sse_client(url, headers={"X-API-Key": "f6d0f3e1c5f8f4ea054ac19ca8cfc5f84fd967418b714c0be1f0ccd98c53cd1c"}) as (read_stream, write_stream):
            print("✅ Conexión SSE establecida en la raíz.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
