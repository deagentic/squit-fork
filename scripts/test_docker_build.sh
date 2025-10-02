#!/bin/bash
# Script para probar build de Docker y verificar dependencias

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 TEST DE BUILD DOCKER - SQUIT CLI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Verificar archivos necesarios
echo "📁 Verificando archivos necesarios..."
files=("requirements.txt" "Dockerfile.cli" "docker-compose.yml" "app/" "scripts/")
for file in "${files[@]}"; do
    if [ -e "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file NO ENCONTRADO"
        exit 1
    fi
done
echo ""

# 2. Verificar Docker
echo "🐳 Verificando Docker..."
if docker info >/dev/null 2>&1; then
    echo "   ✅ Docker corriendo"
else
    echo "   ❌ Docker no está corriendo"
    echo "   → Iniciar Docker Desktop (macOS) o 'sudo systemctl start docker' (Linux)"
    exit 1
fi
echo ""

# 3. Construir imagen
echo "🔨 Construyendo imagen (esto puede tomar 2-3 minutos)..."
docker build -f Dockerfile.cli -t squit-cli:test . || {
    echo ""
    echo "❌ BUILD FALLÓ"
    echo "Ver logs arriba para detalles"
    exit 1
}
echo "   ✅ Imagen construida exitosamente"
echo ""

# 4. Verificar dependencias en la imagen
echo "📦 Verificando dependencias instaladas..."
docker run --rm squit-cli:test python3 -c "
import sys

# Lista de imports críticos
imports = [
    ('google.cloud.bigquery', 'BigQuery Client'),
    ('google.genai', 'Gemini API'),
    ('google.adk', 'Google ADK'),
    ('deprecated', 'Deprecated module'),
    ('deprecation', 'Deprecation module'),
    ('weaviate', 'Weaviate Client'),
    ('langchain_core', 'LangChain Core'),
    ('pandas', 'Pandas'),
]

print('Verificando imports críticos:')
for module, name in imports:
    try:
        __import__(module)
        print(f'   ✅ {name}')
    except ImportError as e:
        print(f'   ❌ {name}: {e}')
        sys.exit(1)

print()
print('✅ Todas las dependencias verificadas')
" || {
    echo ""
    echo "❌ FALTA ALGUNA DEPENDENCIA"
    exit 1
}
echo ""

# 5. Test de import de squit
echo "🧪 Probando imports de SQUIT..."
docker run --rm squit-cli:test python3 -c "
import sys
sys.path.insert(0, '/workspace/app')

# Test imports de SQUIT
try:
    from squit_client import BigQueryClient
    print('   ✅ squit_client')
except Exception as e:
    print(f'   ❌ squit_client: {e}')
    sys.exit(1)

try:
    from bigquery_vector.config import BigQueryVectorConfig
    print('   ✅ bigquery_vector')
except Exception as e:
    print(f'   ❌ bigquery_vector: {e}')
    sys.exit(1)

try:
    from agentic_adk.catalog_enricher import CatalogEnricher
    print('   ✅ agentic_adk.catalog_enricher')
except Exception as e:
    print(f'   ❌ agentic_adk.catalog_enricher: {e}')
    sys.exit(1)

# ESTE ES EL CRÍTICO - aquí fallaba antes
try:
    from agentic_adk import MasterAgent
    print('   ✅ agentic_adk.MasterAgent')
except Exception as e:
    print(f'   ❌ agentic_adk.MasterAgent: {e}')
    sys.exit(1)

print()
print('✅ Todos los imports de SQUIT funcionan')
" || {
    echo ""
    echo "❌ ERROR EN IMPORTS DE SQUIT"
    exit 1
}
echo ""

# 6. Resumen
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ BUILD Y TESTS EXITOSOS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Resultados:"
echo "   ✅ Imagen construida: squit-cli:test"
echo "   ✅ Dependencias instaladas correctamente"
echo "   ✅ Imports de SQUIT funcionando"
echo "   ✅ MasterAgent importable"
echo ""
echo "🚀 Listo para ejecutar:"
echo "   make squit"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

