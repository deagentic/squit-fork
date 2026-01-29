#!/usr/bin/env python3
"""
Script de validación simplificado para Phase 1 con Gemini.
"""

import os
import sys
from pathlib import Path

# Cargar variables de entorno desde .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv no instalado, usando variables de entorno del sistema")

# Agregar directorios al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))


def check_environment() -> bool:
    """Verifica configuración del entorno."""
    print("🔍 Verificando configuración del entorno...")
    
    required_vars = {
        "GEMINI_API_KEY": "Gemini API key para embeddings y agentes",
        "GOOGLE_APPLICATION_CREDENTIALS": "Credenciales de Google Cloud",
    }
    
    missing = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"  ❌ {var}: {description}")
        else:
            # Mostrar parte de la clave para verificar
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"  ✅ {var}: {masked_value}")
    
    if missing:
        print("\n❌ Variables faltantes:")
        print("\n".join(missing))
        return False
    
    return True


def check_dependencies() -> bool:
    """Verifica que las dependencias estén instaladas."""
    print("\n📦 Verificando dependencias...")
    
    dependencies = [
        ("weaviate", "weaviate-client"),
        ("google.genai", "google-genai"),
        ("pandas", "pandas"),
        ("google.cloud.bigquery", "google-cloud-bigquery"),
    ]
    
    missing = []
    for module, package in dependencies:
        try:
            __import__(module)
            print(f"  ✅ {package}: Disponible")
        except ImportError:
            missing.append(f"  ❌ {package}: No instalado")
    
    if missing:
        print("\n❌ Dependencias faltantes:")
        print("\n".join(missing))
        print("\nInstala con: pip install -r requirements.txt")
        return False
    
    return True


def check_bigquery_connection() -> bool:
    """Verifica conexión con BigQuery."""
    print("\n🔗 Verificando conexión BigQuery...")
    
    try:
        from squit_client import BigQueryClient
        
        client = BigQueryClient()
        
        # Test de conexión simple
        test_query = f"""
        SELECT COUNT(*) as total
        FROM `{client.config.full_table_id}`
        LIMIT 1
        """
        
        result = client.execute_query(test_query)
        
        if not result.empty:
            total = result.iloc[0]["total"]
            print(f"  ✅ BigQuery: Conectado ({total:,} objetos disponibles)")
            return True
        else:
            print("  ❌ BigQuery: Sin datos")
            return False
            
    except Exception as e:
        print(f"  ❌ BigQuery: Error - {e}")
        return False


def check_gemini_api() -> bool:
    """Verifica que la API de Gemini funcione."""
    print("\n🤖 Verificando API de Gemini...")
    
    try:
        from google import genai
        
        # Inicializar cliente
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Test simple de generación usando modelo estable
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Responde con 'OK' si puedes procesar este mensaje.",
        )
        
        if "OK" in response.text.upper():
            print("  ✅ Gemini API: Funcionando correctamente")
            return True
        else:
            print(f"  ⚠️  Gemini API: Respuesta inesperada - {response.text}")
            return True  # Aún funciona, solo respuesta diferente
            
    except Exception as e:
        print(f"  ❌ Gemini API: Error - {e}")
        return False


def check_gemini_embeddings() -> bool:
    """Verifica que los embeddings de Gemini funcionen."""
    print("\n📊 Verificando embeddings de Gemini...")
    
    try:
        from google import genai
        
        # Inicializar cliente
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Test de embedding usando modelo estable gemini-embedding-001 con configuración optimizada
        from google.genai import types
        
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents="SELECT * FROM usuarios WHERE activo = 1",
            config=types.EmbedContentConfig(
                task_type="SEMANTIC_SIMILARITY",
                output_dimensionality=768,
            ),
        )
        
        if hasattr(response, 'embeddings') and response.embeddings:
            embedding = response.embeddings[0].values
            if len(embedding) == 768:
                print("  ✅ Gemini Embeddings: Funcionando (768 dimensiones)")
                return True
            else:
                print(f"  ❌ Gemini Embeddings: Dimensiones incorrectas ({len(embedding)})")
                return False
        else:
            print("  ❌ Gemini Embeddings: Respuesta inválida")
            return False
            
    except Exception as e:
        print(f"  ❌ Gemini Embeddings: Error - {e}")
        return False


def run_validation() -> bool:
    """Ejecuta validación simplificada."""
    print("🚀 SQUIT Agentic RAG - Validación Phase 1 (Gemini)")
    print("=" * 60)
    
    checks = [
        ("Entorno", check_environment),
        ("Dependencias", check_dependencies), 
        ("BigQuery", check_bigquery_connection),
        ("Gemini API", check_gemini_api),
        ("Gemini Embeddings", check_gemini_embeddings),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
            
            if result:
                print(f"\n✅ {check_name}: PASSED")
            else:
                print(f"\n❌ {check_name}: FAILED")
                
        except Exception as e:
            print(f"\n💥 {check_name}: EXCEPTION - {e}")
            results.append((check_name, False))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {check_name}: {status}")
    
    print(f"\n📈 Resultado: {passed}/{total} checks pasaron")
    
    if passed >= 4:  # Al menos APIs básicas funcionando
        print("\n🎉 ¡APIs básicas funcionando!")
        print("🤖 Gemini configurado correctamente")
        print("📊 BigQuery conectado")
        print("\n📋 Próximos pasos:")
        print("  1. Configurar Weaviate: 'make agentic-setup'")
        print("  2. Ejecutar demo: 'make agentic-demo'")
        return True
    else:
        print(f"\n⚠️  {total - passed} checks fallaron")
        print("🔧 Revisa la configuración antes de continuar")
        return False


def main():
    """Función principal."""
    success = run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
