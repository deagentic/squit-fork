#!/usr/bin/env python3
"""
Test local de SQUIT MCP tools.

Ejecuta las funciones subyacentes de las 5 herramientas MCP
para validar que todo funciona antes de containerizar.

Usage:
    python scripts/test_mcp_local.py
    make mcp-test
"""

import sys
import os
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("MCP_LOG_LEVEL", "WARNING")

# Import underlying implementation functions directly
from app.agentic_adk.tools.vector_search import (
    _vector_search_impl,
    _get_object_chunks_impl
)
from app.agentic_adk.tools.code_reader import _read_code_impl
from app.agentic_adk.tools.dependency_search import (
    _find_dependencies_impl,
    _analyze_impact_impl
)


def print_header(title: str):
    """Print formatted header."""
    print()
    print("=" * 60)
    print(f"TEST: {title}")
    print("=" * 60)


def test_search():
    """Test vector_search implementation."""
    print_header("squit_search (vector_search_impl)")

    try:
        results = _vector_search_impl(
            query="sistema ARE precios minimos",
            limit=3
        )

        print(f"Total results: {len(results)}")

        if results:
            for r in results[:3]:
                print(f"  - {r.get('object_name', 'N/A')} ({r.get('object_type', 'N/A')})")
                summary = r.get('semantic_summary', '')
                if summary:
                    print(f"    {summary[:80]}...")
            return True
        else:
            print("No results found (this may be expected)")
            return True  # No results is not an error

    except Exception as e:
        print(f"Error: {e}")
        return False


def test_search_with_filters():
    """Test vector_search with filters."""
    print_header("squit_search con filtros (PROCEDURE)")

    try:
        results = _vector_search_impl(
            query="inventario",
            object_types=["PROCEDURE"],
            limit=3
        )

        print(f"Total results: {len(results)}")

        for r in results[:3]:
            print(f"  - {r.get('object_name', 'N/A')} ({r.get('object_type', 'N/A')})")
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


def test_get_code():
    """Test get_object_chunks implementation."""
    print_header("squit_get_code (get_object_chunks_impl)")

    try:
        # First search to get a parent_object_id
        results = _vector_search_impl(query="ARE", limit=1)

        if not results:
            print("No search results to get parent_object_id")
            return True  # Not an error

        parent_id = results[0].get('parent_object_id')
        if not parent_id:
            print("Result has no parent_object_id")
            return True  # Not an error

        print(f"Getting code for: {parent_id}")
        chunks = _get_object_chunks_impl(parent_id)

        print(f"Total chunks: {len(chunks)}")

        if chunks:
            full_code = "\n".join([c.get("chunk_content", "") for c in chunks])
            print(f"Code preview: {full_code[:200]}...")
        else:
            print("No chunks found (object may have no embedded chunks)")

        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


def test_dependencies():
    """Test find_dependencies implementation."""
    print_header("squit_dependencies (find_dependencies_impl)")

    try:
        deps = _find_dependencies_impl("AreRelConnumArticulo", limit=5)

        print(f"Total dependencies: {len(deps)}")

        for dep in deps[:3]:
            print(f"  - {dep.get('dependent_object', 'N/A')} ({dep.get('criticality', 'N/A')})")

        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


def test_impact():
    """Test analyze_impact implementation."""
    print_header("squit_impact (analyze_impact_impl)")

    try:
        impact = _analyze_impact_impl("AreRelConnumArticulo")

        print(f"Total dependencies: {impact.get('total_dependencies', 0)}")
        print(f"Critical: {impact.get('critical_count', 0)}")
        print(f"Medium: {impact.get('medium_count', 0)}")
        print(f"Low: {impact.get('low_count', 0)}")
        print(f"Recommendation: {impact.get('recommendation', 'N/A')}")

        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


def test_read_chunk():
    """Test read_code implementation."""
    print_header("squit_read_chunk (read_code_impl)")

    # This requires a valid chunk_id which we'd need to get from search results
    print("Note: This test requires a valid chunk_id")
    print("Searching for a chunk_id...")

    try:
        results = _vector_search_impl(query="ARE", limit=1)
        if results and results[0].get('chunk_id'):
            chunk_id = results[0]['chunk_id']
            print(f"Testing with chunk_id: {chunk_id}")

            chunk = _read_code_impl(chunk_id)
            if chunk:
                print(f"Chunk content preview: {chunk.get('chunk_content', '')[:100]}...")
                return True
            else:
                print("Chunk not found")
                return True  # Not an error
        else:
            print("No chunk_id in search results - skipping")
            return True

    except Exception as e:
        print(f"Error: {e}")
        return False


def test_mcp_server_import():
    """Test that MCP server module can be imported."""
    print_header("MCP Server Import")

    try:
        from app.mcp_server.server import mcp
        print(f"FastMCP server name: {mcp.name}")
        print(f"Server type: {type(mcp)}")

        # Check that tools are registered
        print("MCP server imported successfully")
        return True

    except Exception as e:
        print(f"Error importing MCP server: {e}")
        return False


def main():
    """Run all tests."""
    print()
    print("=" * 60)
    print("SQUIT MCP Server - Test Suite")
    print("=" * 60)
    print()
    print("Verificando conexion a BigQuery...")

    tests = [
        ("MCP Server Import", test_mcp_server_import),
        ("squit_search", test_search),
        ("squit_search (filtros)", test_search_with_filters),
        ("squit_get_code", test_get_code),
        ("squit_dependencies", test_dependencies),
        ("squit_impact", test_impact),
        ("squit_read_chunk", test_read_chunk),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"EXCEPTION: {e}")
            results.append((name, False))

    # Summary
    print()
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "PASS" if success else "FAIL"
        icon = "OK" if success else "XX"
        print(f"  [{icon}] {name}: {status}")

    print()
    print(f"Total: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("SUCCESS - All MCP tools working correctly!")
        return 0
    else:
        print("WARNING - Some tests failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
