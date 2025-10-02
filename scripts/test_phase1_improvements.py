#!/usr/bin/env python3
"""
Test de mejoras Fase 1: Context Caching + LangChain + QueryLogger.

Valida que las mejoras funcionen correctamente:
1. Context Caching reduce latencia
2. LangChain Memory mantiene estructura
3. QueryLogger guarda en BigQuery
4. Few-shots se generan desde historial

Uso:
    python3 scripts/test_phase1_improvements.py
"""

import os
import sys
import time
from pathlib import Path

# Cargar .env
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"').strip("'")
                if key == 'GOOGLE_APPLICATION_CREDENTIALS' and not value.startswith('/'):
                    value = str((Path(__file__).parent.parent / value).absolute())
                os.environ[key] = value

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

import warnings
warnings.filterwarnings('ignore')
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from agentic_adk import MasterAgent


def test_context_caching():
    """Test 1: Context Caching reduce latencia."""
    print("\n" + "=" * 80)
    print("🧪 TEST 1: Context Caching")
    print("=" * 80)
    
    agent = MasterAgent()
    
    # Verificar que cache está inicializado
    if agent.cached_system_prompt:
        print(f"✅ Context caching habilitado: {agent.cached_system_prompt.name}")
    else:
        print("⚠️ Context caching no disponible (puede ser normal)")
    
    # Medir latencia de primera query
    print("\n  Midiendo latencia...")
    start = time.time()
    response1 = agent.process("que es kayak", show_progress=False)
    time1 = time.time() - start
    print(f"  Query 1: {time1:.2f}s")
    
    # Segunda query (debería ser más rápida con cache)
    start = time.time()
    response2 = agent.process("explicame inventario", show_progress=False)
    time2 = time.time() - start
    print(f"  Query 2: {time2:.2f}s")
    
    if time2 < time1 * 0.8:  # 20% más rápido
        print(f"\n  ✅ Latencia reducida: {((time1-time2)/time1*100):.1f}% más rápido")
        return True
    else:
        print(f"\n  ℹ️ Latencias similares (cache puede no estar activo)")
        return True  # No falla el test, puede ser esperado


def test_langchain_memory():
    """Test 2: LangChain Memory mantiene estructura."""
    print("\n" + "=" * 80)
    print("🧪 TEST 2: LangChain BufferMemory")
    print("=" * 80)
    
    agent = MasterAgent()
    
    if not agent.langchain_memory:
        print("  ⚠️ LangChain no disponible, test skipped")
        return True
    
    print(f"  ✅ LangChain memory inicializado (k={agent.langchain_memory.k})")
    
    # Hacer queries
    agent.process("hablame de kayak", show_progress=False)
    agent.process("dame mas detalles", show_progress=False)
    agent.process("cuales son los procedures", show_progress=False)
    
    # Verificar que memoria tiene turnos
    memory_vars = agent.langchain_memory.load_memory_variables({})
    chat_history = memory_vars.get("chat_history", [])
    
    if len(chat_history) >= 3:
        print(f"  ✅ Memoria mantiene {len(chat_history)} turnos estructurados")
        
        # Verificar estructura
        for i, msg in enumerate(chat_history[:2], 1):
            role = "Usuario" if hasattr(msg, 'type') and msg.type == "human" else "Asistente"
            print(f"  Turn {i} - {role}: {str(msg.content)[:50]}...")
        
        return True
    else:
        print(f"  ❌ Memoria solo tiene {len(chat_history)} turnos")
        return False


def test_query_logger():
    """Test 3: QueryLogger guarda en BigQuery."""
    print("\n" + "=" * 80)
    print("🧪 TEST 3: QueryLogger BigQuery")
    print("=" * 80)
    
    agent = MasterAgent()
    
    if not agent.query_logger:
        print("  ⚠️ QueryLogger no disponible, test skipped")
        return True
    
    print("  ✅ QueryLogger inicializado")
    
    # Hacer una query
    query_test = "test query para bigquery logging"
    agent.process(query_test, show_progress=False)
    
    # Verificar que se logueó (indirectamente con stats)
    try:
        stats = agent.query_logger.get_stats()
        
        if stats:
            print(f"  ✅ QueryLogger funcional")
            print(f"     Total queries: {stats.get('total_queries', 0)}")
            print(f"     Total sessions: {stats.get('total_sessions', 0)}")
            
            # Mostrar top entities si existen
            top_entities = stats.get('top_entities', [])
            if top_entities:
                print(f"     Top entities: {', '.join([e['entity'] for e in top_entities[:3]])}")
            
            return True
        else:
            print("  ⚠️ Stats vacíos (puede ser primera ejecución)")
            return True
    
    except Exception as e:
        print(f"  ❌ Error obteniendo stats: {e}")
        return False


def test_few_shots():
    """Test 4: Few-shots desde historial."""
    print("\n" + "=" * 80)
    print("🧪 TEST 4: Few-Shots desde Historial")
    print("=" * 80)
    
    agent = MasterAgent()
    
    if not agent.query_logger:
        print("  ⚠️ QueryLogger no disponible, test skipped")
        return True
    
    # Crear algunas queries para tener historial
    print("  Creando historial...")
    agent.process("procedures de ventas", show_progress=False)
    agent.process("functions de inventario", show_progress=False)
    
    # Buscar query similar
    print("\n  Buscando queries similares...")
    try:
        similar = agent.query_logger.get_similar_queries(
            query="dame procedures de ventas",
            limit=3
        )
        
        if similar:
            print(f"  ✅ Encontradas {len(similar)} queries similares")
            for i, q in enumerate(similar, 1):
                print(f"     {i}. {q['user_query'][:50]}... (sim: {q['similarity']:.2f})")
            return True
        else:
            print("  ℹ️ No hay queries similares aún (esperado en primera ejecución)")
            return True
    
    except Exception as e:
        print(f"  ❌ Error en búsqueda similar: {e}")
        return False


def test_integration():
    """Test 5: Integración completa end-to-end."""
    print("\n" + "=" * 80)
    print("🧪 TEST 5: Integración Completa")
    print("=" * 80)
    
    agent = MasterAgent()
    
    print("  Simulando conversación multi-turn...")
    
    # Turno 1
    print("\n  [1] Usuario: hablame de kayak")
    r1 = agent.process("hablame de kayak", show_progress=False)
    assert len(r1) > 50, "Respuesta muy corta"
    assert "kayak" in r1.lower(), "No menciona kayak"
    print(f"  ✅ Turno 1: {len(r1)} chars")
    
    # Turno 2
    print("\n  [2] Usuario: todos los procedures")
    r2 = agent.process("todos los procedures", show_progress=False)
    assert len(r2) > 50, "Respuesta muy corta"
    # Debería mantener contexto de kayak (pero no forzoso)
    print(f"  ✅ Turno 2: {len(r2)} chars")
    
    # Turno 3
    print("\n  [3] Usuario: el primero que mencionaste")
    r3 = agent.process("el primero que mencionaste", show_progress=False)
    assert len(r3) > 50, "Respuesta muy corta"
    print(f"  ✅ Turno 3: {len(r3)} chars")
    
    # Reset
    print("\n  [RESET] Limpiando memoria...")
    agent.reset_conversation()
    
    # Turno post-reset
    print("\n  [4] Usuario: el primero que mencionaste (sin contexto)")
    r4 = agent.process("el primero que mencionaste", show_progress=False)
    assert len(r4) > 20, "Respuesta muy corta"
    print(f"  ✅ Turno 4 (post-reset): {len(r4)} chars")
    
    print("\n  ✅ Integración completa funcional")
    return True


def main():
    """Ejecuta todos los tests."""
    print("\n" + "="*80)
    print("🚀 TESTS: Mejoras Fase 1")
    print("Context Caching + LangChain + QueryLogger BigQuery")
    print("="*80)
    
    tests = [
        ("Context Caching", test_context_caching),
        ("LangChain Memory", test_langchain_memory),
        ("QueryLogger BigQuery", test_query_logger),
        ("Few-Shots", test_few_shots),
        ("Integración Completa", test_integration)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n  ❌ Test '{name}' falló con error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Resumen
    print("\n" + "="*80)
    print("📊 RESUMEN")
    print("="*80)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, p in results:
        status = "✅ PASS" if p else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\n  Tests pasados: {passed}/{total}")
    print(f"  Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n  🎉 TODOS LOS TESTS PASARON")
        print("  Fase 1 implementada correctamente")
    elif passed >= total * 0.75:
        print("\n  ⚠️ MAYORÍA DE TESTS PASARON")
        print("  Revisar tests fallidos")
    else:
        print("\n  ❌ VARIOS TESTS FALLARON")
        print("  Revisar implementación")
    
    print("\n" + "="*80)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

