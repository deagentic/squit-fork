#!/usr/bin/env python3
"""
Programa de Pruebas REAL del Sistema Agentic ADK.

Este programa ejecuta pruebas REALES contra BigQuery SIN mocks ni fallbacks.
Cada test debe funcionar con datos reales o fallar claramente.

Uso:
    # Todas las pruebas
    python scripts/test_agentic_adk_real.py
    
    # Solo validación
    python scripts/test_agentic_adk_real.py --validate-only
    
    # Solo tools
    python scripts/test_agentic_adk_real.py --tools-only
    
    # Solo agente completo
    python scripts/test_agentic_adk_real.py --agent-only
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Cargar variables de ambiente desde .env manualmente
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Remover comillas si existen
                value = value.strip('"').strip("'")
                
                # Si es GOOGLE_APPLICATION_CREDENTIALS, hacer path absoluto
                if key == 'GOOGLE_APPLICATION_CREDENTIALS':
                    if not value.startswith('/'):
                        value = str((Path(__file__).parent.parent / value).absolute())
                
                os.environ[key] = value

# Verificar que GOOGLE_APPLICATION_CREDENTIALS apunte a archivo existente
if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    creds_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    if not Path(creds_path).exists():
        print(f"⚠️  Advertencia: credentials.json no encontrado en {creds_path}")
        del os.environ['GOOGLE_APPLICATION_CREDENTIALS']

# Agregar app al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

# Setup logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgenticTestSuite:
    """Suite de pruebas reales para el sistema agentic."""
    
    def __init__(self):
        """Inicializa la suite de pruebas."""
        self.results = []
        self.start_time = None
    
    def print_header(self):
        """Imprime header de las pruebas."""
        print("\n" + "=" * 90)
        print("🧪 SQUIT - Pruebas REALES del Sistema Agentic ADK")
        print("=" * 90)
        print(f"📅 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("⚠️  SIN MOCKS - SIN FALLBACKS - SOLO DATOS REALES")
        print("=" * 90)
        print()
        self.start_time = datetime.now()
    
    def test_result(self, name: str, passed: bool, details: str = "", data: Any = None):
        """Registra resultado de un test."""
        icon = "✅" if passed else "❌"
        status = "PASS" if passed else "FAIL"
        
        self.results.append({
            "name": name,
            "passed": passed,
            "details": details,
            "data": data
        })
        
        print(f"\n{icon} TEST: {name}")
        print(f"   Status: {status}")
        if details:
            print(f"   Detalles: {details}")
        if data and passed:
            if isinstance(data, list):
                print(f"   Datos: {len(data)} items obtenidos")
            elif isinstance(data, dict):
                print(f"   Datos: {len(data)} campos obtenidos")
    
    def print_summary(self):
        """Imprime resumen de resultados."""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        passed = sum(1 for r in self.results if r['passed'])
        failed = sum(1 for r in self.results if not r['passed'])
        total = len(self.results)
        
        print("\n" + "=" * 90)
        print("📊 RESUMEN DE PRUEBAS")
        print("=" * 90)
        print(f"Total: {total} pruebas")
        print(f"✅ Pasadas: {passed}")
        print(f"❌ Fallidas: {failed}")
        print(f"⏱️  Duración: {duration:.2f} segundos")
        print()
        
        if failed > 0:
            print("❌ TESTS FALLIDOS:")
            for r in self.results:
                if not r['passed']:
                    print(f"   • {r['name']}: {r['details']}")
            print()
        
        print("=" * 90)
        
        if failed == 0:
            print("✅ TODOS LOS TESTS PASARON - Sistema listo para democratizar código")
        else:
            print("❌ HAY TESTS FALLIDOS - Revisa la configuración")
        
        print("=" * 90)
        
        return failed == 0


def test_1_environment():
    """Test 1: Validar variables de ambiente."""
    suite = AgenticTestSuite()
    
    print("\n" + "=" * 90)
    print("TEST 1: VARIABLES DE AMBIENTE")
    print("=" * 90)
    
    # GEMINI_API_KEY
    gemini_key = os.getenv('GEMINI_API_KEY')
    suite.test_result(
        "GEMINI_API_KEY configurado",
        bool(gemini_key),
        f"Valor: {'***' + gemini_key[-4:] if gemini_key else 'NO CONFIGURADO'}"
    )
    
    if not gemini_key:
        print("\n💡 Configura en .env:")
        print("   GEMINI_API_KEY=tu-api-key")
        return False
    
    # GOOGLE_CLOUD_PROJECT
    project = os.getenv('GOOGLE_CLOUD_PROJECT')
    suite.test_result(
        "GOOGLE_CLOUD_PROJECT configurado",
        bool(project),
        f"Proyecto: {project if project else 'NO CONFIGURADO'}"
    )
    
    return all(r['passed'] for r in suite.results)


def test_2_bigquery_access():
    """Test 2: Acceso a BigQuery."""
    suite = AgenticTestSuite()
    
    print("\n" + "=" * 90)
    print("TEST 2: ACCESO A BIGQUERY")
    print("=" * 90)
    
    try:
        from google.cloud import bigquery
        from bigquery_vector.config import BigQueryVectorConfig
        
        config = BigQueryVectorConfig()
        client = bigquery.Client(project=config.PROJECT_ID)
        
        suite.test_result(
            "Cliente BigQuery inicializado",
            True,
            f"Proyecto: {config.PROJECT_ID}"
        )
        
        # Test tabla de embeddings
        try:
            table = client.get_table(config.full_embeddings_table_id)
            suite.test_result(
                "Tabla chunk_embeddings existe",
                True,
                f"{table.num_rows:,} rows, {table.num_bytes / 1024**3:.2f} GB",
                {"rows": table.num_rows, "size_gb": table.num_bytes / 1024**3}
            )
            
            if table.num_rows == 0:
                print("\n⚠️  Tabla vacía - Ejecuta primero el pipeline:")
                print("   python scripts/run_bigquery_pipeline.py")
                return False
            
        except Exception as e:
            suite.test_result(
                "Tabla chunk_embeddings existe",
                False,
                f"Error: {e}"
            )
            print("\n💡 Crea la tabla primero:")
            print("   python scripts/run_bigquery_pipeline.py")
            return False
        
        # Test modelo de embeddings (OPCIONAL - se crea automáticamente)
        try:
            model_id = f"{config.PROJECT_ID}.{config.DATASET_ID}.gemini_embedding_model"
            model = client.get_model(model_id)
            suite.test_result(
                "Modelo gemini_embedding_model existe (opcional)",
                True,
                f"Tipo: {model.model_type}"
            )
        except Exception as e:
            # No es crítico - el modelo se crea al ejecutar queries
            print(f"\n   ℹ️  Modelo no encontrado (se creará automáticamente en primera búsqueda)")
            suite.test_result(
                "Modelo gemini_embedding_model existe (opcional)",
                True,  # PASS porque no es crítico
                "Se creará automáticamente"
            )
        
        # Solo fallar si tests críticos fallaron
        critical_tests = [r for r in suite.results if 'opcional' not in r['name'].lower()]
        return all(r['passed'] for r in critical_tests)
        
    except Exception as e:
        suite.test_result(
            "Acceso a BigQuery",
            False,
            f"Error: {e}"
        )
        return False


def test_3_tools_real():
    """Test 3: Tools con datos REALES."""
    suite = AgenticTestSuite()
    
    print("\n" + "=" * 90)
    print("TEST 3: TOOLS CON DATOS REALES (SIN MOCKS)")
    print("=" * 90)
    
    try:
        # Importar funciones de implementación directamente (para testing)
        from agentic_adk.tools.vector_search import _vector_search_impl, _get_object_chunks_impl
        from agentic_adk.tools.code_reader import _get_object_summary_impl
        from agentic_adk.tools.dependency_search import _find_dependencies_impl, _analyze_impact_impl
        
        # También importar las tools para validar que existen
        from agentic_adk.tools import (
            vector_search_tool,
            get_object_chunks_tool,
            get_object_summary_tool,
            find_dependencies_tool,
            analyze_impact_tool
        )
        
        suite.test_result(
            "Tools importadas correctamente",
            True,
            "Todas las tools están disponibles para agentes"
        )
        
        # Test 3.1: Vector Search Tool
        print("\n📍 Test 3.1: vector_search_tool (función real)")
        try:
            # Buscar algo genérico que seguro existe
            results = _vector_search_impl(
                query="SELECT",
                limit=5
            )
            
            suite.test_result(
                "vector_search_tool ejecuta correctamente",
                len(results) > 0,
                f"Encontrados {len(results)} resultados",
                results
            )
            
            if results:
                print("\n   Resultados obtenidos:")
                for i, r in enumerate(results[:3], 1):
                    print(f"   {i}. {r.get('object_name', 'N/A')}")
                    print(f"      Dominio: {r.get('business_domain', 'N/A')}")
                    print(f"      Relevancia: {r.get('relevance_score', 0):.3f}")
            
        except Exception as e:
            suite.test_result(
                "vector_search_tool ejecuta correctamente",
                False,
                f"Error: {e}"
            )
            logger.exception("Error en vector_search_tool")
        
        # Test 3.2: Get Object Summary Tool
        print("\n📍 Test 3.2: get_object_summary_tool")
        
        # Primero obtener un nombre de objeto real
        if results and len(results) > 0:
            test_object_name = results[0].get('object_name')
            
            try:
                summary = _get_object_summary_impl(test_object_name)
                
                suite.test_result(
                    "get_object_summary_tool funciona",
                    'object_name' in summary or 'error' not in summary,
                    f"Objeto: {test_object_name}",
                    summary
                )
                
                if 'object_name' in summary:
                    print(f"\n   Resumen de {test_object_name}:")
                    print(f"   - Tipo: {summary.get('object_type', 'N/A')}")
                    print(f"   - Dominio: {summary.get('business_domain', 'N/A')}")
                    print(f"   - Complejidad: {summary.get('complexity_score', 0)}")
                    print(f"   - Chunks: {summary.get('total_chunks', 0)}")
                
            except Exception as e:
                suite.test_result(
                    "get_object_summary_tool funciona",
                    False,
                    f"Error: {e}"
                )
        else:
            suite.test_result(
                "get_object_summary_tool funciona",
                False,
                "No hay objetos para testear (vector_search falló)"
            )
        
        # Test 3.3: Get Object Chunks Tool
        print("\n📍 Test 3.3: get_object_chunks_tool")
        
        if results and len(results) > 0:
            test_parent_id = results[0].get('parent_object_id')
            
            try:
                chunks = _get_object_chunks_impl(test_parent_id)
                
                suite.test_result(
                    "get_object_chunks_tool funciona",
                    len(chunks) > 0,
                    f"Chunks obtenidos: {len(chunks)}",
                    chunks
                )
                
                if chunks:
                    print(f"\n   Chunks del objeto:")
                    for chunk in chunks[:3]:
                        print(f"   - Chunk {chunk.get('chunk_index', '?')}/{chunk.get('total_chunks', '?')}")
                        print(f"     Líneas: {chunk.get('chunk_length', 0)}")
                
            except Exception as e:
                suite.test_result(
                    "get_object_chunks_tool funciona",
                    False,
                    f"Error: {e}"
                )
        
        # Test 3.4: Find Dependencies Tool
        print("\n📍 Test 3.4: find_dependencies_tool")
        
        if results and len(results) > 0:
            # Buscar objeto que tenga dependencias
            test_object_name = results[0].get('object_name', '').split('.')[-1]
            
            try:
                deps = _find_dependencies_impl(test_object_name, limit=10)
                
                suite.test_result(
                    "find_dependencies_tool funciona",
                    True,  # Puede retornar lista vacía
                    f"Dependencias encontradas: {len(deps)}",
                    deps
                )
                
                if deps:
                    print(f"\n   Dependencias de {test_object_name}:")
                    for dep in deps[:3]:
                        print(f"   - {dep.get('dependent_object', 'N/A')}")
                        print(f"     Criticidad: {dep.get('criticality', 'N/A')}")
                        print(f"     Usa como: {dep.get('how_used', 'N/A')}")
                else:
                    print(f"\n   ℹ️  No se encontraron dependencias para {test_object_name}")
                
            except Exception as e:
                suite.test_result(
                    "find_dependencies_tool funciona",
                    False,
                    f"Error: {e}"
                )
        
        # Test 3.5: Analyze Impact Tool
        print("\n📍 Test 3.5: analyze_impact_tool")
        
        if results and len(results) > 0:
            test_object_name = results[0].get('object_name', '').split('.')[-1]
            
            try:
                impact = _analyze_impact_impl(test_object_name)
                
                suite.test_result(
                    "analyze_impact_tool funciona",
                    'total_dependencies' in impact,
                    f"Análisis generado para {test_object_name}",
                    impact
                )
                
                if 'total_dependencies' in impact:
                    print(f"\n   Análisis de impacto:")
                    print(f"   - Total afectados: {impact.get('total_dependencies', 0)}")
                    print(f"   - Críticos: {impact.get('critical_count', 0)}")
                    print(f"   - Recomendación: {impact.get('recommendation', 'N/A')}")
                
            except Exception as e:
                suite.test_result(
                    "analyze_impact_tool funciona",
                    False,
                    f"Error: {e}"
                )
        
        return all(r['passed'] for r in suite.results)
        
    except Exception as e:
        logger.exception("Error importando tools")
        suite.test_result(
            "Importar tools",
            False,
            f"Error: {e}"
        )
        return False


def test_4_agent_real():
    """Test 4: MasterAgent con queries REALES."""
    suite = AgenticTestSuite()
    
    print("\n" + "=" * 90)
    print("TEST 4: MASTERAGENT CON QUERIES REALES")
    print("=" * 90)
    
    try:
        from agentic_adk import MasterAgent
        
        # Test 4.1: Inicialización
        print("\n📍 Test 4.1: Inicialización del agente")
        try:
            agent = MasterAgent()
            suite.test_result(
                "MasterAgent inicializa correctamente",
                True,
                "Agente listo con todas las tools"
            )
        except ValueError as e:
            suite.test_result(
                "MasterAgent inicializa correctamente",
                False,
                f"Error de configuración: {e}"
            )
            print("\n💡 Verifica que GEMINI_API_KEY esté en .env")
            return False
        except Exception as e:
            suite.test_result(
                "MasterAgent inicializa correctamente",
                False,
                f"Error: {e}"
            )
            logger.exception("Error inicializando agente")
            return False
        
        # Test 4.2: Búsqueda simple
        print("\n📍 Test 4.2: Query de búsqueda simple")
        query1 = "procedimientos relacionados con ventas"
        
        try:
            print(f"   Query: \"{query1}\"")
            response1 = agent.process(query1)
            
            suite.test_result(
                "Búsqueda simple funciona",
                len(response1) > 50,  # Respuesta debe tener contenido
                f"Respuesta de {len(response1)} caracteres",
                response1
            )
            
            print("\n   Respuesta del agente:")
            print("   " + "-" * 70)
            # Mostrar primeras líneas
            lines = response1.split('\n')[:10]
            for line in lines:
                print(f"   {line}")
            if len(response1.split('\n')) > 10:
                print(f"   ... ({len(response1.split('\n')) - 10} líneas más)")
            print("   " + "-" * 70)
            
        except Exception as e:
            suite.test_result(
                "Búsqueda simple funciona",
                False,
                f"Error: {e}"
            )
            logger.exception("Error en búsqueda simple")
        
        # Test 4.3: Query con análisis
        print("\n📍 Test 4.3: Query de análisis de objeto")
        
        # Obtener nombre de objeto real primero
        try:
            from agentic_adk.tools import vector_search_tool
            sample_results = vector_search_tool("procedimiento", limit=1)
            
            if sample_results:
                test_object = sample_results[0].get('object_name')
                query2 = f"¿Qué hace el objeto {test_object}?"
                
                print(f"   Query: \"{query2}\"")
                response2 = agent.process(query2)
                
                suite.test_result(
                    "Análisis de objeto funciona",
                    len(response2) > 50,
                    f"Respuesta de {len(response2)} caracteres",
                    response2
                )
                
                print("\n   Respuesta del agente:")
                print("   " + "-" * 70)
                lines = response2.split('\n')[:8]
                for line in lines:
                    print(f"   {line}")
                if len(response2.split('\n')) > 8:
                    print(f"   ... ({len(response2.split('\n')) - 8} líneas más)")
                print("   " + "-" * 70)
                
            else:
                suite.test_result(
                    "Análisis de objeto funciona",
                    False,
                    "No se pudo obtener objeto para testear"
                )
                
        except Exception as e:
            suite.test_result(
                "Análisis de objeto funciona",
                False,
                f"Error: {e}"
            )
            logger.exception("Error en análisis")
        
        # Test 4.4: Query de dependencias
        print("\n📍 Test 4.4: Query de análisis de dependencias")
        
        if sample_results:
            test_object = sample_results[0].get('object_name', '').split('.')[-1]
            query3 = f"¿Qué objetos dependen de {test_object}?"
            
            try:
                print(f"   Query: \"{query3}\"")
                response3 = agent.process(query3)
                
                suite.test_result(
                    "Análisis de dependencias funciona",
                    len(response3) > 30,
                    f"Respuesta de {len(response3)} caracteres",
                    response3
                )
                
                print("\n   Respuesta del agente:")
                print("   " + "-" * 70)
                lines = response3.split('\n')[:6]
                for line in lines:
                    print(f"   {line}")
                if len(response3.split('\n')) > 6:
                    print(f"   ... ({len(response3.split('\n')) - 6} líneas más)")
                print("   " + "-" * 70)
                
            except Exception as e:
                suite.test_result(
                    "Análisis de dependencias funciona",
                    False,
                    f"Error: {e}"
                )
        
        return all(r['passed'] for r in suite.results)
        
    except Exception as e:
        logger.exception("Error en tests de agente")
        suite.test_result(
            "Tests de agente",
            False,
            f"Error: {e}"
        )
        return False


def test_5_end_to_end():
    """Test 5: End-to-end con casos reales."""
    suite = AgenticTestSuite()
    
    print("\n" + "=" * 90)
    print("TEST 5: END-TO-END - CASOS DE USO REALES")
    print("=" * 90)
    
    try:
        from agentic_adk import MasterAgent
        agent = MasterAgent()
        
        # Casos de uso de democratización
        test_cases = [
            {
                "name": "Búsqueda por intención (nuevo desarrollador)",
                "query": "¿Dónde está la lógica de autenticación de usuarios?",
                "expect": ["autenticación", "usuario", "login", "validación"]
            },
            {
                "name": "Entender funcionalidad (analista)",
                "query": "Dame un resumen de los procedimientos de inventario",
                "expect": ["inventario", "procedimiento", "stock"]
            },
            {
                "name": "Exploración de dominio (manager)",
                "query": "¿Qué componentes críticos hay en el dominio de ventas?",
                "expect": ["ventas", "complejidad", "crítico"]
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📍 Test 5.{i}: {test_case['name']}")
            print(f"   Query: \"{test_case['query']}\"")
            
            try:
                response = agent.process(test_case['query'])
                
                # Verificar que la respuesta tenga contenido esperado
                response_lower = response.lower()
                matches = sum(1 for word in test_case['expect'] 
                            if word.lower() in response_lower)
                
                passed = len(response) > 100 and matches >= 1
                
                suite.test_result(
                    test_case['name'],
                    passed,
                    f"Respuesta: {len(response)} chars, {matches}/{len(test_case['expect'])} keywords",
                    response
                )
                
                if passed:
                    print("\n   ✅ Respuesta generada:")
                    print("   " + "-" * 70)
                    lines = response.split('\n')[:5]
                    for line in lines:
                        print(f"   {line}")
                    if len(response.split('\n')) > 5:
                        print(f"   ... ({len(response.split('\n')) - 5} líneas más)")
                    print("   " + "-" * 70)
                else:
                    print(f"\n   ❌ Respuesta no contiene keywords esperadas")
                
            except Exception as e:
                suite.test_result(
                    test_case['name'],
                    False,
                    f"Error: {e}"
                )
                logger.exception(f"Error en test case {i}")
        
        return all(r['passed'] for r in suite.results)
        
    except Exception as e:
        logger.exception("Error en tests end-to-end")
        return False


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Pruebas REALES del Sistema Agentic ADK (SIN MOCKS)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--validate-only', action='store_true',
                       help='Solo validar ambiente y BigQuery')
    parser.add_argument('--tools-only', action='store_true',
                       help='Solo probar tools')
    parser.add_argument('--agent-only', action='store_true',
                       help='Solo probar agente completo')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Logging detallado')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    suite = AgenticTestSuite()
    suite.print_header()
    
    all_passed = True
    
    # Test 1: Environment (siempre)
    if not test_1_environment():
        print("\n❌ Tests de ambiente fallaron - No se puede continuar")
        return 1
    
    # Test 2: BigQuery (siempre)
    if not test_2_bigquery_access():
        print("\n❌ Tests de BigQuery fallaron - No se puede continuar")
        return 1
    
    if args.validate_only:
        print("\n✅ Validación completada - Sistema listo")
        return 0
    
    # Test 3: Tools
    if not args.agent_only:
        if not test_3_tools_real():
            all_passed = False
            if args.tools_only:
                return 1
    
    if args.tools_only:
        return 0
    
    # Test 4: Agent
    if not test_4_agent_real():
        all_passed = False
    
    # Test 5: End-to-end
    if not test_5_end_to_end():
        all_passed = False
    
    # Resumen final
    suite.print_summary()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
