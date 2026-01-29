# 🔌 MCP Server - Model Context Protocol

## 🎯 Objetivo

Crear un **MCP Server** para SQUIT que permita a IDEs (Claude Desktop, Cursor, etc.) acceder directamente a la base de conocimiento SQL legacy.

---

## 📋 ¿Qué es MCP?

**Model Context Protocol** (MCP) es un protocolo abierto desarrollado por Anthropic que permite a aplicaciones proporcionar contexto a LLMs de manera estandarizada.

### Beneficios para SQUIT

1. **Integración con IDEs**
   - Claude Desktop puede buscar en tu codebase SQL
   - Cursor puede acceder a búsqueda semántica
   - Otros IDEs compatibles con MCP

2. **Tools Estandarizados**
   - `squit/search` - Búsqueda semántica
   - `squit/analyze` - Análisis de código
   - `squit/dependencies` - Análisis de dependencias
   - `squit/explain` - Explicaciones en lenguaje simple

3. **Context Enriquecido**
   - LLMs acceden directamente a 3.4M objetos SQL
   - Respuestas basadas en código real
   - Sin copy-paste manual

---

## 🏗️ Arquitectura Propuesta

```
┌──────────────────────────────────────────────┐
│          Claude Desktop / Cursor             │
├──────────────────────────────────────────────┤
│           MCP Client (Built-in)              │
└──────────────────┬───────────────────────────┘
                   │ MCP Protocol (stdio)
                   │
┌──────────────────▼───────────────────────────┐
│              SQUIT MCP Server                │
├──────────────────────────────────────────────┤
│  Tools:                                      │
│  • squit/search (semantic)                   │
│  • squit/analyze (code analysis)             │
│  • squit/dependencies (impact)               │
│  • squit/explain (natural language)          │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│         BigQuery Vector Search               │
│         (3.4M SQL objects)                   │
└──────────────────────────────────────────────┘
```

---

## 🛠️ Implementación

### 1. Crear MCP Server

```python
# mcp/server.py

from mcp.server import Server
from mcp.types import Tool, TextContent

from agentic_adk import MasterAgent
from bigquery_vector import BigQueryVectorSearch

# Inicializar servidor MCP
server = Server("squit")

# Tool 1: Búsqueda semántica
@server.tool()
async def search(query: str, limit: int = 10) -> str:
    """
    Busca código SQL por significado.
    
    Args:
        query: Búsqueda en lenguaje natural
        limit: Cantidad de resultados
    """
    search_engine = BigQueryVectorSearch()
    results = search_engine.semantic_search(query, limit=limit)
    
    # Formatear resultados para MCP
    formatted = f"Encontrados {len(results)} objetos:\n\n"
    for r in results:
        formatted += f"• {r['object_name']} ({r['object_type']})\n"
        formatted += f"  {r['summary'][:200]}...\n\n"
    
    return formatted

# Tool 2: Análisis de código específico
@server.tool()
async def analyze(object_name: str) -> str:
    """
    Analiza un objeto SQL específico.
    
    Args:
        object_name: Nombre del objeto (procedure, table, etc)
    """
    agent = MasterAgent()
    response = agent.process(f"analiza en detalle {object_name}")
    return response

# Tool 3: Dependencias
@server.tool()
async def dependencies(object_name: str) -> str:
    """
    Analiza dependencias de un objeto.
    
    Args:
        object_name: Nombre del objeto
    """
    agent = MasterAgent()
    response = agent.process(f"dependencias de {object_name}")
    return response

# Tool 4: Explicación simple
@server.tool()
async def explain(object_name: str) -> str:
    """
    Explica qué hace un objeto en lenguaje simple.
    
    Args:
        object_name: Nombre del objeto
    """
    agent = MasterAgent()
    response = agent.process(f"explicame {object_name} en lenguaje simple")
    return response

# Iniciar servidor
if __name__ == "__main__":
    server.run()
```

### 2. Configuración para Claude Desktop

```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "squit": {
      "command": "python",
      "args": [
        "/path/to/squit/mcp/server.py"
      ],
      "env": {
        "GOOGLE_CLOUD_PROJECT": "your-project",
        "GEMINI_API_KEY": "your-key"
      }
    }
  }
}
```

### 3. Uso en Claude Desktop

```
Usuario en Claude Desktop:

"Busca procedures relacionados con fechas de embarque"

Claude automáticamente usa:
<use_mcp_tool>
  <server_name>squit</server_name>
  <tool_name>search</tool_name>
  <arguments>
    <query>procedures fechas embarque</query>
    <limit>10</limit>
  </arguments>
</use_mcp_tool>

Resultado:
Encontrados 6 objetos:
• AgAsignaFechasKayakProc (PROCEDURE)
  Asigna fechas estimadas de embarque...
```

---

## 📦 Dependencias

```bash
# Agregar a requirements.txt
mcp>=0.1.0
```

---

## 🧪 Testing

```python
# tests/test_mcp_server.py

import pytest
from mcp.client import Client

@pytest.mark.asyncio
async def test_mcp_search():
    """Test tool de búsqueda."""
    client = Client()
    await client.connect("squit")
    
    result = await client.call_tool("search", {
        "query": "kayak",
        "limit": 5
    })
    
    assert "AgAsignaFechasKayakProc" in result

@pytest.mark.asyncio
async def test_mcp_analyze():
    """Test tool de análisis."""
    client = Client()
    await client.connect("squit")
    
    result = await client.call_tool("analyze", {
        "object_name": "AgAsignaFechasKayakProc"
    })
    
    assert len(result) > 100
```

---

## 📅 Timeline

### Fase 2.1: Prototipo (1 semana)
- [ ] Crear `mcp/server.py` básico
- [ ] Implementar tool `search`
- [ ] Configurar en Claude Desktop
- [ ] Validar funcionamiento

### Fase 2.2: Tools Completos (1 semana)
- [ ] Implementar `analyze`
- [ ] Implementar `dependencies`
- [ ] Implementar `explain`
- [ ] Tests unitarios

### Fase 2.3: Optimización (1 semana)
- [ ] Caching de resultados
- [ ] Streaming responses
- [ ] Error handling robusto
- [ ] Documentación completa

---

## 🔮 Features Futuras

### MCP Tools Extensibles
- `squit/similar` - Código similar
- `squit/impact` - Análisis de impacto
- `squit/refactor` - Sugerencias de refactorización
- `squit/document` - Generar documentación automática
- `squit/translate` - Traducir SQL a otro dialecto

### Integraciones
- VSCode via MCP extension
- JetBrains IDEs
- Neovim plugins
- Emacs modes

---

## 📚 Referencias

- **MCP Spec**: https://modelcontextprotocol.io/
- **MCP Python SDK**: https://github.com/anthropics/mcp-python-sdk
- **Claude Desktop MCP**: https://docs.anthropic.com/claude/docs/mcp

---

**Status**: 📋 Planificado para Fase 2  
**Priority**: Alta (democratiza acceso desde IDEs)  
**Complejidad**: Media  
**Tiempo estimado**: 3 semanas
