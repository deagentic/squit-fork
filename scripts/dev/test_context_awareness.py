#!/usr/bin/env python3
"""
Test de conciencia contextual en memoria multi-turn.

Valida que el agente interprete referencias vagas en contexto.

Uso:
    python3 scripts/test_context_awareness.py
"""

import os
import sys
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


def validate_response_context(response: str, expected_keywords: list[str], context_name: str) -> bool:
    """
    Valida que la respuesta contenga keywords esperados del contexto.
    
    Args:
        response: Respuesta del agente
        expected_keywords: Keywords que deben aparecer
        context_name: Nombre del contexto para logs
        
    Returns:
        True si la respuesta es contextual
    """
    response_lower = response.lower()
    found = [kw for kw in expected_keywords if kw.lower() in response_lower]
    
    if found:
        print(f"   ✅ Contexto '{context_name}' detectado: {', '.join(found)}")
        return True
    else:
        print(f"   ❌ Contexto '{context_name}' NO detectado")
        print(f"   ⚠️  Expected: {expected_keywords}")
        print(f"   ⚠️  Got: {response[:200]}...")
        return False


def test_context_awareness():
    """Test de conciencia contextual con referencias vagas."""
    print("\n" + "=" * 80)
    print("🧪 TEST: Conciencia Contextual en Memoria Multi-Turn")
    print("=" * 80)
    
    # Inicializar agente
    print("\n1️⃣  Inicializando agente...")
    agent = MasterAgent()
    print(f"   ✅ Session ID: {agent.session_id[:8]}...")
    
    passed_tests = 0
    total_tests = 0
    
    # =========================================================================
    # TEST 1: Referencia vaga "todos" en contexto
    # =========================================================================
    print("\n2️⃣  TEST 1: Referencia vaga 'todos' con contexto activo")
    print("   " + "-" * 76)
    
    total_tests += 1
    print("   Turno 1: 'hablame de kayak'")
    response1 = agent.process("hablame de kayak", show_progress=False)
    print(f"   ✅ Respuesta 1: {len(response1)} chars")
    
    # Validar que habló de kayak
    if "kayak" in response1.lower():
        print("   ✅ Contexto 'kayak' establecido")
    
    print("\n   Turno 2: 'todos los store procedures'")
    print("   Expected: Debe interpretar como 'todos los de kayak'")
    response2 = agent.process("todos los store procedures", show_progress=False)
    print(f"   ✅ Respuesta 2: {len(response2)} chars")
    
    # Validar que mantuvo contexto de kayak
    if validate_response_context(
        response2, 
        ["kayak", "AgAsignaFechasKayakProc", "KayAsignaFechasKayakProc"],
        "kayak"
    ):
        passed_tests += 1
        print("   ✅ TEST 1: PASÓ - Mantuvo contexto de kayak")
    else:
        print("   ❌ TEST 1: FALLÓ - No mantuvo contexto")
    
    # =========================================================================
    # TEST 2: Referencia ordinal "el primero"
    # =========================================================================
    print("\n3️⃣  TEST 2: Referencia ordinal 'el primero'")
    print("   " + "-" * 76)
    
    # Reset para test limpio
    agent.reset_conversation()
    
    total_tests += 1
    print("   Turno 1: 'procedures de inventario'")
    response3 = agent.process("procedures de inventario", show_progress=False)
    print(f"   ✅ Respuesta 1: {len(response3)} chars")
    
    print("\n   Turno 2: 'el primero que mencionaste, dame detalles'")
    response4 = agent.process("el primero que mencionaste, dame detalles", show_progress=False)
    print(f"   ✅ Respuesta 2: {len(response4)} chars")
    
    # Validar que habló de inventario (no topic drift)
    if validate_response_context(
        response4,
        ["inventario", "producto", "almacen", "stock"],
        "inventario"
    ):
        passed_tests += 1
        print("   ✅ TEST 2: PASÓ - Recordó contexto de inventario")
    else:
        print("   ❌ TEST 2: FALLÓ - Perdió contexto")
    
    # =========================================================================
    # TEST 3: Referencia posesiva "sus dependencias"
    # =========================================================================
    print("\n4️⃣  TEST 3: Referencia posesiva 'sus'")
    print("   " + "-" * 76)
    
    # Reset para test limpio
    agent.reset_conversation()
    
    total_tests += 1
    print("   Turno 1: 'explicame AgAsignaFechasKayakProc'")
    response5 = agent.process("explicame AgAsignaFechasKayakProc", show_progress=False)
    print(f"   ✅ Respuesta 1: {len(response5)} chars")
    
    print("\n   Turno 2: 'sus dependencias'")
    response6 = agent.process("sus dependencias", show_progress=False)
    print(f"   ✅ Respuesta 2: {len(response6)} chars")
    
    # Validar que habló de dependencias de ese procedure
    if validate_response_context(
        response6,
        ["AgAsignaFechasKayakProc", "kayak", "depend", "tabla", "procedure"],
        "AgAsignaFechasKayakProc"
    ):
        passed_tests += 1
        print("   ✅ TEST 3: PASÓ - Entendió 'sus' como del procedure")
    else:
        print("   ❌ TEST 3: FALLÓ - No entendió referencia posesiva")
    
    # =========================================================================
    # TEST 4: Reset limpia contexto
    # =========================================================================
    print("\n5️⃣  TEST 4: Reset limpia contexto correctamente")
    print("   " + "-" * 76)
    
    total_tests += 1
    print("   Turno 1: 'hablame de ventas'")
    response7 = agent.process("hablame de ventas", show_progress=False)
    print(f"   ✅ Respuesta 1: {len(response7)} chars")
    
    print("\n   Reset: Limpiando memoria...")
    old_session = agent.session_id[:8]
    agent.reset_conversation()
    new_session = agent.session_id[:8]
    print(f"   ✅ Session: {old_session}... → {new_session}...")
    
    print("\n   Turno 2 (post-reset): 'el primero que mencionaste'")
    response8 = agent.process("el primero que mencionaste", show_progress=False)
    print(f"   ✅ Respuesta 2: {len(response8)} chars")
    
    # Validar que NO recuerda (debe pedir aclaración)
    confusion_keywords = ["no tengo", "cuál", "qué", "más información", "específico", "contexto"]
    if any(kw in response8.lower() for kw in confusion_keywords):
        passed_tests += 1
        print("   ✅ TEST 4: PASÓ - Olvidó contexto después de reset")
    else:
        print("   ❌ TEST 4: FALLÓ - Aún recuerda después de reset")
    
    # =========================================================================
    # RESUMEN
    # =========================================================================
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE TESTS")
    print("=" * 80)
    
    print(f"\n   Tests pasados: {passed_tests}/{total_tests}")
    print(f"   Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n   ✅ TODOS LOS TESTS PASARON")
        print("   🎉 Conciencia contextual funcional")
    elif passed_tests >= total_tests * 0.75:
        print("\n   ⚠️  MAYORÍA DE TESTS PASARON")
        print("   💡 Conciencia contextual parcialmente funcional")
    else:
        print("\n   ❌ VARIOS TESTS FALLARON")
        print("   🔧 Requiere ajustes en system prompt")
    
    print("\n" + "=" * 80)
    print()
    
    return passed_tests == total_tests


if __name__ == "__main__":
    try:
        success = test_context_awareness()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

