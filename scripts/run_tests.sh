#!/bin/bash
# Script helper para ejecutar pruebas del sistema agentic con configuración automática

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "🧪 SQUIT - Ejecutor de Pruebas Agentic ADK"
echo "================================================================================"
echo ""

# Cambiar al directorio del proyecto
cd "$(dirname "$0")/.."

# Cargar variables de .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Variables cargadas desde .env"
else
    echo -e "${RED}❌ Archivo .env no encontrado${NC}"
    echo "Copia env.example como .env y configura los valores"
    exit 1
fi

# Verificar GEMINI_API_KEY
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}❌ GEMINI_API_KEY no configurado en .env${NC}"
    exit 1
fi
echo "✅ GEMINI_API_KEY configurado"

# Configurar GOOGLE_CLOUD_PROJECT si no está
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    export GOOGLE_CLOUD_PROJECT=dfor-prj-dev
    echo "✅ GOOGLE_CLOUD_PROJECT configurado: dfor-prj-dev"
fi

# Configurar credenciales de Google Cloud
if [ -f "credentials.json" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/credentials.json"
    echo "✅ Usando credentials.json"
elif [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo -e "${YELLOW}⚠️  credentials.json no encontrado - Usando gcloud auth${NC}"
    echo "Si falla, ejecuta: gcloud auth application-default login"
fi

echo ""
echo "================================================================================"
echo "🚀 Ejecutando pruebas..."
echo "================================================================================"
echo ""

# Ejecutar pruebas
python3 scripts/test_agentic_adk_real.py "$@"

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✅ Pruebas completadas exitosamente${NC}"
else
    echo -e "${RED}❌ Algunas pruebas fallaron${NC}"
fi

exit $exit_code
