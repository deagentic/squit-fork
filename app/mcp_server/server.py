"""
SQUIT MCP Server - Busqueda semantica de codigo SQL via MCP.

Expone 5.7M objetos SQL de Deacero a LLMs usando el protocolo MCP.
Soporta transports: STDIO (Claude Desktop) y HTTP (produccion).

Version: 1.0.0
MCP Spec: 2025-06-18
FastMCP: 2.14.3+
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List

from fastmcp import FastMCP

# Setup path para importar modulos existentes
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agentic_adk.tools.vector_search import (
    _vector_search_impl,
    _get_object_chunks_impl
)
from app.agentic_adk.tools.code_reader import _read_code_impl
from app.agentic_adk.tools.dependency_search import (
    _find_dependencies_impl,
    _analyze_impact_impl
)

# Logging estructurado
logging.basicConfig(
    level=os.getenv("MCP_LOG_LEVEL", "INFO"),
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}'
)
logger = logging.getLogger("squit-mcp")

# ============================================================
# FastMCP Server
# ============================================================

mcp = FastMCP(
    name="squit",
    instructions="Busqueda semantica en 5.7M objetos SQL legacy de Deacero. "
                 "Encuentra procedures, views, functions y tablas por significado."
)


@mcp.tool()
def squit_search(
    query: str,
    business_domains: Optional[List[str]] = None,
    object_types: Optional[List[str]] = None,
    limit: int = 10
) -> dict:
    """
    Busca codigo SQL por significado usando busqueda semantica hibrida.

    Busca en 5.7M objetos SQL (procedures, views, functions, triggers)
    enriquecido con catalogo de 280 aplicaciones de negocio.

    Args:
        query: Busqueda en lenguaje natural. Ejemplos:
               - "calculo de inventario kayak"
               - "fechas de embarque"
               - "sistema ARE precios minimos"
        business_domains: Filtrar por dominio. Opciones:
               ventas, inventario, finanzas, produccion, logistica, compras
        object_types: Filtrar por tipo. Opciones:
               PROCEDURE, VIEW, FUNCTION, TRIGGER, TABLE
        limit: Maximo resultados (1-50, default 10)

    Returns:
        dict con status, total_results, y lista de resultados con:
        - object_name, object_type, business_domain
        - semantic_summary, parent_object_id, relevance_score
    """
    logger.info(f"search: query='{query}' domains={business_domains} types={object_types}")

    try:
        results = _vector_search_impl(
            query=query,
            business_domains=business_domains,
            object_types=object_types,
            limit=min(limit, 50)
        )

        formatted = [{
            "object_name": r.get("object_name"),
            "object_type": r.get("object_type"),
            "business_domain": r.get("business_domain"),
            "semantic_summary": r.get("semantic_summary"),
            "parent_object_id": r.get("parent_object_id"),
            "relevance_score": round(r.get("relevance_score", 0), 3),
            "preview": (r.get("chunk_preview") or "")[:200]
        } for r in results]

        return {"status": "success", "total_results": len(formatted), "results": formatted}

    except Exception as e:
        logger.error(f"search error: {e}")
        return {"status": "error", "error": str(e), "query": query}


@mcp.tool()
def squit_get_code(parent_object_id: str) -> dict:
    """
    Obtiene el codigo SQL completo de un objeto.

    Usa el parent_object_id de los resultados de squit_search.

    Args:
        parent_object_id: ID del objeto. Formato: SERVER|DB|schema|object_name
                         Ejemplo: "DEAOFINET06|Operacion|ARESch|ARECalculoPreciosMinimosMx"

    Returns:
        dict con full_code (SQL completo), total_chunks, y metadata de cada chunk
    """
    logger.info(f"get_code: {parent_object_id}")

    try:
        chunks = _get_object_chunks_impl(parent_object_id)

        if not chunks:
            return {"status": "not_found", "parent_object_id": parent_object_id}

        full_code = "\n".join([c.get("chunk_content", "") for c in chunks])

        return {
            "status": "success",
            "parent_object_id": parent_object_id,
            "total_chunks": len(chunks),
            "full_code": full_code,
            "chunks_metadata": [{
                "index": c.get("chunk_index"),
                "summary": c.get("semantic_summary"),
                "complexity": c.get("complexity_score")
            } for c in chunks]
        }
    except Exception as e:
        logger.error(f"get_code error: {e}")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def squit_dependencies(object_name: str, limit: int = 20) -> dict:
    """
    Encuentra que objetos SQL dependen de un objeto especifico.

    CRITICO para analisis de impacto: antes de modificar una tabla
    o procedure, identifica que codigo se puede romper.

    Args:
        object_name: Nombre del objeto. Ejemplos:
                    - "ClientesMaster" (tabla)
                    - "sp_CalcularInventario" (procedure)
                    - "vw_VentasDiarias" (view)
        limit: Maximo dependencias a retornar (default: 20)

    Returns:
        Lista de dependientes con:
        - object_name, object_type
        - criticality: CRITICAL (escribe), MEDIUM (lee), LOW (referencia)
        - how_used: READ, WRITE, EXECUTE, REFERENCE
    """
    logger.info(f"dependencies: {object_name}")

    try:
        deps = _find_dependencies_impl(object_name, limit=limit)
        return {
            "status": "success",
            "object_analyzed": object_name,
            "total_dependencies": len(deps),
            "dependencies": deps
        }
    except Exception as e:
        logger.error(f"dependencies error: {e}")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def squit_impact(object_name: str) -> dict:
    """
    Analiza el impacto potencial de modificar un objeto SQL.

    Genera reporte ejecutivo con clasificacion de riesgo.

    Args:
        object_name: Nombre del objeto a analizar

    Returns:
        Reporte con:
        - total_dependencies, critical_count, medium_count, low_count
        - by_type: distribucion por tipo de objeto
        - by_domain: distribucion por dominio de negocio
        - top_critical: los objetos mas criticos
        - recommendation: SAFE / CAUTION / HIGH_RISK con explicacion
    """
    logger.info(f"impact: {object_name}")

    try:
        impact = _analyze_impact_impl(object_name)
        return {"status": "success", **impact}
    except Exception as e:
        logger.error(f"impact error: {e}")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def squit_read_chunk(chunk_id: str) -> dict:
    """
    Lee un chunk especifico de codigo SQL.

    Util para obtener fragmentos especificos sin cargar el objeto completo.

    Args:
        chunk_id: ID unico del chunk (de resultados de squit_search)

    Returns:
        chunk_content, object_name, object_type, semantic_summary
    """
    logger.info(f"read_chunk: {chunk_id}")

    try:
        chunk = _read_code_impl(chunk_id)
        if not chunk:
            return {"status": "not_found", "chunk_id": chunk_id}
        return {"status": "success", **chunk}
    except Exception as e:
        logger.error(f"read_chunk error: {e}")
        return {"status": "error", "error": str(e)}


# ============================================================
# Entry Point
# ============================================================

def main():
    """Iniciar servidor MCP."""
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

    if transport == "http":
        # Modo HTTP para produccion containerizada
        import uvicorn
        # Usar la aplicación MCP directamente para evitar problemas de montaje/lifespan
        app = mcp.http_app(transport="sse")

        from starlette.responses import JSONResponse
        async def health_check(request):
            return JSONResponse({"status": "healthy", "service": "squit-mcp"})
        
        app.add_route("/health", health_check)

        port = int(os.getenv("PORT", 8000))
        logger.info(f"Starting HTTP server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)  # nosec B104
    else:
        # Modo STDIO para Claude Desktop
        logger.info("Starting STDIO server")
        mcp.run()


if __name__ == "__main__":
    main()
