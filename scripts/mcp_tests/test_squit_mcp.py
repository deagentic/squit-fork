import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
import os
import json

async def run():
    api_key = os.getenv("SQUIT_API_KEY", "f6d0f3e1c5f8f4ea054ac19ca8cfc5f84fd967418b714c0be1f0ccd98c53cd1c")
    url = "http://localhost:8000/sse"
    
    print(f"🔄 Conectando a {url}...")
    
    try:
        # Usando el cliente SSE oficial de la librería MCP de Anthropic
        async with sse_client(url, headers={"X-API-Key": api_key}) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                print("✅ Conexión establecida y sesión inicializada.\n")
                
                # Listar herramientas disponibles
                print("🛠️  Herramientas disponibles:")
                tools = await session.list_tools()
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description.split('.')[0]}")
                print()
                
                # Probar la búsqueda
                query = "login"
                print(f"🔍 Ejecutando squit_search con query: '{query}'...")
                
                result = await session.call_tool("squit_search", arguments={"query": query, "limit": 2})
                
                print("\n📊 Resultados:")
                if hasattr(result, 'content'):
                    for content in result.content:
                        if content.type == "text":
                            try:
                                data = json.loads(content.text)
                                print(json.dumps(data, indent=2))
                            except:
                                print(content.text)
                else:
                    print(result)

    except Exception as e:
        print(f"\n❌ Error de conexión o ejecución: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())
