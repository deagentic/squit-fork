# SQUIT - SQL Objects BigQuery Client
# Makefile para automatización de tareas

# Variables
DOCKER_COMPOSE = docker-compose
DOCKER = docker
APP_NAME = squit-bigquery-client
DEV_SERVICE = squit-dev
PROD_SERVICE = squit-client

# Colores para output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

.PHONY: help build run dev test clean logs shell format lint security install stop restart health-weaviate agentic-setup agentic-demo agentic-ingest migrate-all migrate-test monitor-migration verify-bigquery create-chunks test-chunks search-chunks analyze-data bigquery-full compare-systems clean-chunks mcp-build mcp-run mcp-run-bg mcp-dev mcp-test mcp-logs mcp-stop mcp-inspector

# Comando por defecto
help: ## Mostrar ayuda
	@echo "$(BLUE)SQUIT - SQL Objects BigQuery Client$(NC)"
	@echo "$(YELLOW)Comandos disponibles:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Construcción
build: ## Construir imagen Docker de producción
	@echo "$(BLUE)Construyendo imagen de producción...$(NC)"
	$(DOCKER_COMPOSE) build $(PROD_SERVICE)

build-dev: ## Construir imagen Docker de desarrollo
	@echo "$(BLUE)Construyendo imagen de desarrollo...$(NC)"
	$(DOCKER_COMPOSE) build $(DEV_SERVICE)

build-all: ## Construir todas las imágenes
	@echo "$(BLUE)Construyendo todas las imágenes...$(NC)"
	$(DOCKER_COMPOSE) build

# Ejecución
run: ## Ejecutar aplicación en producción
	@echo "$(GREEN)Ejecutando aplicación...$(NC)"
	$(DOCKER_COMPOSE) up $(PROD_SERVICE)

run-bg: ## Ejecutar aplicación en background
	@echo "$(GREEN)Ejecutando aplicación en background...$(NC)"
	$(DOCKER_COMPOSE) up -d $(PROD_SERVICE)

squit: ## Ejecutar CLI interactivo de SQUIT en Docker
	@echo "$(BLUE)  ███████╗ ██████╗ ██╗   ██╗██╗████████╗$(NC)"
	@echo "$(BLUE)  ██╔════╝██╔═══██╗██║   ██║██║╚══██╔══╝$(NC)"
	@echo "$(BLUE)  ███████╗██║   ██║██║   ██║██║   ██║   $(NC)"
	@echo "$(BLUE)  ╚════██║██║▄▄ ██║██║   ██║██║   ██║   $(NC)"
	@echo "$(BLUE)  ███████║╚██████╔╝╚██████╔╝██║   ██║   $(NC)"
	@echo "$(BLUE)  ╚══════╝ ╚══▀▀═╝  ╚═════╝ ╚═╝   ╚═╝   $(NC)"
	@echo ""
	@echo "$(GREEN)Iniciando CLI interactivo de SQUIT...$(NC)"
	@echo "$(YELLOW)Configuración persistente montada:$(NC)"
	@echo "  • .config/credentials.json"
	@echo "  • data/catalogo.csv (280 apps)"
	@echo "  • .env variables"
	@echo ""
	@$(DOCKER_COMPOSE) --profile cli run --rm squit-cli

squit-build: ## Construir imagen del CLI de SQUIT
	@echo "$(BLUE)Construyendo imagen CLI de SQUIT...$(NC)"
	@$(DOCKER_COMPOSE) --profile cli down 2>/dev/null || true
	@$(DOCKER) rmi squit-squit-cli:latest 2>/dev/null || true
	@$(DOCKER_COMPOSE) --profile cli build --no-cache squit-cli

squit-rebuild: ## Reconstruir y ejecutar CLI de SQUIT (forzar rebuild completo)
	@echo "$(BLUE)Reconstruyendo CLI de SQUIT (sin cache)...$(NC)"
	@$(DOCKER_COMPOSE) --profile cli down 2>/dev/null || true
	@$(DOCKER) rmi squit-squit-cli:latest 2>/dev/null || true
	@$(DOCKER_COMPOSE) --profile cli build --no-cache squit-cli
	@echo "$(GREEN)Iniciando CLI...$(NC)"
	@$(DOCKER_COMPOSE) --profile cli run --rm squit-cli

squit-clean: ## Limpiar completamente contenedores e imágenes de SQUIT
	@echo "$(YELLOW)Limpiando contenedores e imágenes...$(NC)"
	@$(DOCKER_COMPOSE) --profile cli down -v 2>/dev/null || true
	@$(DOCKER) rmi squit-squit-cli:latest 2>/dev/null || true
	@$(DOCKER) rmi squit-cli:latest 2>/dev/null || true
	@$(DOCKER) rmi squit-cli:test 2>/dev/null || true
	@echo "$(GREEN)Limpieza completa$(NC)"

dev: ## Iniciar entorno de desarrollo con Jupyter
	@echo "$(GREEN)Iniciando entorno de desarrollo...$(NC)"
	@echo "$(YELLOW)Jupyter Lab estará disponible en: http://localhost:8888$(NC)"
	$(DOCKER_COMPOSE) --profile dev up $(DEV_SERVICE)

dev-bg: ## Iniciar entorno de desarrollo en background
	@echo "$(GREEN)Iniciando entorno de desarrollo en background...$(NC)"
	$(DOCKER_COMPOSE) --profile dev up -d $(DEV_SERVICE)

# Testing y calidad
test: ## Ejecutar tests unitarios
	@echo "$(BLUE)Ejecutando tests...$(NC)"
	$(DOCKER_COMPOSE) run --rm $(PROD_SERVICE) python3 -m pytest tests/ -v

test-cov: ## Ejecutar tests con coverage
	@echo "$(BLUE)Ejecutando tests con coverage...$(NC)"
	$(DOCKER_COMPOSE) run --rm $(PROD_SERVICE) python3 -m pytest tests/ --cov=squit_client --cov-report=html

lint: ## Ejecutar linting (flake8, black, mypy)
	@echo "$(BLUE)Ejecutando linting...$(NC)"
	$(DOCKER_COMPOSE) run --rm $(PROD_SERVICE) flake8 squit_client/
	$(DOCKER_COMPOSE) run --rm $(PROD_SERVICE) black --check squit_client/
	$(DOCKER_COMPOSE) run --rm $(PROD_SERVICE) mypy squit_client/

format: ## Formatear código con black
	@echo "$(BLUE)Formateando código...$(NC)"
	$(DOCKER_COMPOSE) run --rm $(PROD_SERVICE) black squit_client/ tests/

security: ## Ejecutar análisis de seguridad con bandit
	@echo "$(BLUE)Ejecutando análisis de seguridad...$(NC)"
	$(DOCKER_COMPOSE) run --rm $(PROD_SERVICE) bandit -r squit_client/

# Gestión de contenedores
stop: ## Detener todos los servicios
	@echo "$(YELLOW)Deteniendo servicios...$(NC)"
	$(DOCKER_COMPOSE) down

restart: ## Reiniciar servicios
	@echo "$(YELLOW)Reiniciando servicios...$(NC)"
	$(DOCKER_COMPOSE) restart

logs: ## Ver logs de la aplicación
	@echo "$(BLUE)Mostrando logs...$(NC)"
	$(DOCKER_COMPOSE) logs -f $(PROD_SERVICE)

logs-dev: ## Ver logs del entorno de desarrollo
	@echo "$(BLUE)Mostrando logs de desarrollo...$(NC)"
	$(DOCKER_COMPOSE) logs -f $(DEV_SERVICE)

shell: ## Abrir shell en contenedor de producción
	@echo "$(GREEN)Abriendo shell en contenedor...$(NC)"
	$(DOCKER_COMPOSE) run --rm $(PROD_SERVICE) /bin/sh

shell-dev: ## Abrir shell en contenedor de desarrollo
	@echo "$(GREEN)Abriendo shell en contenedor de desarrollo...$(NC)"
	$(DOCKER_COMPOSE) run --rm $(DEV_SERVICE) /bin/bash

# Limpieza
clean: ## Limpiar contenedores, imágenes y volúmenes
	@echo "$(RED)Limpiando contenedores y imágenes...$(NC)"
	$(DOCKER_COMPOSE) down --rmi all --volumes --remove-orphans
	$(DOCKER) system prune -f

clean-all: ## Limpieza completa del sistema Docker
	@echo "$(RED)Limpieza completa del sistema Docker...$(NC)"
	$(DOCKER_COMPOSE) down --rmi all --volumes --remove-orphans
	$(DOCKER) system prune -a -f --volumes

# Instalación y configuración
install: ## Instalar dependencias localmente (para desarrollo)
	@echo "$(BLUE)Instalando dependencias localmente...$(NC)"
	pip install -r requirements.txt
	pip install -e .

setup-dev: ## Configurar entorno de desarrollo completo
	@echo "$(BLUE)Configurando entorno de desarrollo...$(NC)"
	@make build-dev
	@echo "$(GREEN)Entorno de desarrollo configurado.$(NC)"
	@echo "$(YELLOW)Usa 'make dev' para iniciar Jupyter Lab$(NC)"

# Ejemplos y demos
demo: ## Ejecutar ejemplo de uso (modo limpio)
	@echo "$(GREEN)Ejecutando ejemplo básico...$(NC)"
	$(DOCKER_COMPOSE) run --rm $(PROD_SERVICE) python3 examples/basic_usage.py

demo-verbose: ## Ejecutar ejemplo con todos los logs
	@echo "$(GREEN)Ejecutando ejemplo modo verbose...$(NC)"
	$(DOCKER_COMPOSE) run --rm $(PROD_SERVICE) python3 examples/example_usage.py

demo-clean: ## Ejecutar ejemplo sin warnings
	@echo "$(GREEN)Ejecutando ejemplo limpio...$(NC)"
	$(DOCKER_COMPOSE) run --rm $(PROD_SERVICE) python3 examples/run_clean.py

query: ## Ejecutar consulta interactiva
	@echo "$(GREEN)Ejecutando cliente interactivo...$(NC)"
	$(DOCKER_COMPOSE) run --rm -it $(PROD_SERVICE) python3 -c "from squit_client import BigQueryClient; client = BigQueryClient(); print('Cliente listo. Usa client.* para consultas')"

# Información del sistema
status: ## Mostrar estado de contenedores
	@echo "$(BLUE)Estado de contenedores:$(NC)"
	$(DOCKER_COMPOSE) ps

images: ## Mostrar imágenes Docker del proyecto
	@echo "$(BLUE)Imágenes Docker del proyecto:$(NC)"
	$(DOCKER) images | grep -E "(squit|bigquery)"

network: ## Mostrar información de red
	@echo "$(BLUE)Información de red:$(NC)"
	$(DOCKER) network ls | grep squit

# Producción
deploy: ## Preparar para despliegue (build + test)
	@echo "$(BLUE)Preparando para despliegue...$(NC)"
	@make build
	@make test
	@echo "$(GREEN)Listo para despliegue!$(NC)"

health: ## Verificar salud de los servicios
	@echo "$(BLUE)Verificando salud de servicios...$(NC)"
	@echo "$(YELLOW)BigQuery:$(NC)"
	$(DOCKER_COMPOSE) run --rm $(PROD_SERVICE) python3 -c "from squit_client import BigQueryClient; client = BigQueryClient(); print('✅ Cliente funcionando correctamente')" || echo "$(RED)❌ Error en el cliente$(NC)"
	@echo "$(YELLOW)Weaviate:$(NC)"
	$(DOCKER_COMPOSE) run --rm $(PROD_SERVICE) python3 weaviate_health.py

health-weaviate: ## Verificar solo conexión con Weaviate
	@echo "$(BLUE)Verificando conexión con Weaviate...$(NC)"
	$(DOCKER_COMPOSE) run --rm $(PROD_SERVICE) python3 weaviate_health.py

# Documentación
docs: ## Generar documentación
	@echo "$(BLUE)La documentación está en el directorio docs/$(NC)"
	@echo "$(YELLOW)README principal: README.md$(NC)"
	@ls -la docs/

# Backup y restore
backup-creds: ## Hacer backup de credenciales (cifrado)
	@echo "$(YELLOW)Creando backup cifrado de credenciales...$(NC)"
	@tar -czf credentials-backup-$$(date +%Y%m%d).tar.gz credentials.json
	@echo "$(GREEN)Backup creado: credentials-backup-$$(date +%Y%m%d).tar.gz$(NC)"

# Información de versión
version: ## Mostrar versión del proyecto
	@echo "$(BLUE)SQUIT Version:$(NC)"
	@python3 -c "import sys; sys.path.insert(0, 'app'); from squit_client import __version__; print(__version__)" 2>/dev/null || echo "1.0.0"

# Comandos Agentic RAG
agentic-setup: ## Configurar sistema Agentic RAG completo
	@echo "$(BLUE)Configurando sistema Agentic RAG...$(NC)"
	@echo "$(YELLOW)1. Verificando configuración...$(NC)"
	@test -f .env || (echo "$(RED)Archivo .env no encontrado. Copia env.example a .env$(NC)" && exit 1)
	@echo "$(YELLOW)2. Construyendo imágenes...$(NC)"
	docker-compose -f docker-compose.weaviate.yml build
	@echo "$(YELLOW)3. Iniciando Weaviate...$(NC)"
	docker-compose -f docker-compose.weaviate.yml up -d weaviate
	@echo "$(GREEN)Sistema Agentic RAG configurado!$(NC)"
	@echo "$(BLUE)Weaviate UI: http://localhost:8080$(NC)"

agentic-demo: ## Ejecutar demo del sistema Agentic RAG
	@echo "$(GREEN)Ejecutando demo Agentic RAG...$(NC)"
	python3 scripts/demo_phase1.py

agentic-demo-full: ## Ejecutar demo completo con Weaviate
	@echo "$(GREEN)Ejecutando demo completo Agentic RAG...$(NC)"
	docker-compose -f docker-compose.weaviate.yml run --rm squit-agentic

agentic-ingest: ## Ejecutar ingesta de muestra (1,000 objetos)
	@echo "$(YELLOW)Iniciando ingesta de muestra BigQuery → Weaviate...$(NC)"
	@echo "$(BLUE)Procesando 1,000 objetos más importantes...$(NC)"
	docker-compose -f docker-compose.weaviate.yml run --rm squit-agentic python3 -c "
	from agentic_rag import IngestionPipeline, WeaviateClient;
	from squit_client import BigQueryClient;
	bq = BigQueryClient();
	wv = WeaviateClient();
	wv.create_schema();
	pipeline = IngestionPipeline(bq, wv);
	filters = {'object_type': ['PROCEDURE', 'FUNCTION', 'VIEW']};
	stats = pipeline.run_full_ingestion(limit=1000, filters=filters);
	print(f'Ingesta de muestra completada: {stats}')
	"

migrate-all: ## Migrar TODOS los datos BigQuery → Weaviate (puede tomar horas)
	@echo "$(RED)⚠️  MIGRACIÓN COMPLETA - Esto puede tomar varias horas$(NC)"
	@echo "$(YELLOW)Migrando ~3.4M objetos SQL con análisis Gemini...$(NC)"
	@echo "$(BLUE)💰 Costo estimado: $10-50 USD en API calls$(NC)"
	docker-compose -f docker-compose.weaviate.yml run --rm squit-agentic python3 scripts/migrate_all_data.py

migrate-test: ## Migrar solo 10 objetos para prueba
	@echo "$(GREEN)Ejecutando migración de prueba (10 objetos)...$(NC)"
	docker-compose -f docker-compose.weaviate.yml run --rm squit-agentic python3 -c "
	from agentic_rag import IngestionPipeline, WeaviateClient;
	from squit_client import BigQueryClient;
	bq = BigQueryClient();
	wv = WeaviateClient();
	wv.create_schema();
	pipeline = IngestionPipeline(bq, wv);
	filters = {'object_type': ['VIEW', 'PROCEDURE']};
	stats = pipeline.run_full_ingestion(limit=10, filters=filters);
	print(f'Prueba completada: Procesados={stats[\"processed\"]}, Exitosos={stats[\"success\"]}');
	if stats['success'] >= 8: print('🎉 PRUEBA EXITOSA - Listo para migración completa');
	else: print('⚠️  Revisar configuración')
	"

monitor-migration: ## Monitorear progreso de migración en tiempo real
	@echo "$(BLUE)Iniciando monitor de migración...$(NC)"
	@echo "$(YELLOW)Mostrará progreso cada 30 segundos$(NC)"
	python3 scripts/monitor_migration.py

agentic-dev: ## Iniciar entorno de desarrollo Agentic RAG
	@echo "$(GREEN)Iniciando entorno de desarrollo Agentic RAG...$(NC)"
	@echo "$(YELLOW)Jupyter Lab estará disponible en: http://localhost:8888$(NC)"
	@echo "$(YELLOW)Weaviate UI en: http://localhost:8080$(NC)"
	docker-compose -f docker-compose.weaviate.yml --profile dev up

agentic-stop: ## Detener servicios Agentic RAG
	@echo "$(YELLOW)Deteniendo servicios Agentic RAG...$(NC)"
	docker-compose -f docker-compose.weaviate.yml down

agentic-logs: ## Ver logs del sistema Agentic RAG
	@echo "$(BLUE)Mostrando logs Agentic RAG...$(NC)"
	docker-compose -f docker-compose.weaviate.yml logs -f

agentic-health: ## Verificar salud del sistema Agentic RAG
	@echo "$(BLUE)Verificando salud del sistema Agentic RAG...$(NC)"
	@echo "$(YELLOW)Weaviate:$(NC)"
	@curl -s http://localhost:8080/v1/.well-known/ready | jq . || echo "$(RED)❌ Weaviate no disponible$(NC)"
	@echo "$(YELLOW)SQUIT Agentic:$(NC)"
	@docker-compose -f docker-compose.weaviate.yml run --rm squit-agentic python3 -c "from agentic_rag import WeaviateClient; client = WeaviateClient(); health = client.health_check(); print(f'Status: {health[\"status\"]}'); print(f'Collections: {health[\"collections\"]}')" || echo "$(RED)❌ SQUIT Agentic no disponible$(NC)"

agentic-reset: ## Resetear datos de Weaviate (CUIDADO: borra todo)
	@echo "$(RED)⚠️  CUIDADO: Esto borrará todos los datos de Weaviate$(NC)"
	@read -p "¿Estás seguro? (y/N): " confirm && [ "$$confirm" = "y" ]
	docker-compose -f docker-compose.weaviate.yml down -v
	docker volume rm squit_weaviate_data 2>/dev/null || true
	@echo "$(GREEN)Datos de Weaviate reseteados$(NC)"

validate-phase1: ## Validar que Phase 1 esté funcionando correctamente
	@echo "$(BLUE)Validando Phase 1 del sistema Agentic RAG...$(NC)"
	python3 scripts/validate_phase1_simple.py

validate-phase1-full: ## Validación completa (requiere Weaviate ejecutándose)
	@echo "$(BLUE)Validando Phase 1 completo...$(NC)"
	python3 scripts/validate_phase1.py

analyze-bigquery: ## Analizar schema y datos de BigQuery antes de migración
	@echo "$(BLUE)Analizando schema y datos de BigQuery...$(NC)"
	docker-compose -f docker-compose.weaviate.yml run --rm squit-agentic python3 scripts/analyze_bigquery_schema.py

demo-chunking: ## Demostrar estrategias de smart chunking para objetos masivos
	@echo "$(BLUE)Demostrando smart chunking...$(NC)"
	python3 scripts/demo_smart_chunking.py

# Comandos BigQuery Vector Search (Sistema Principal)
create-chunks: ## Crear chunks inteligentes con embeddings en BigQuery
	@echo "$(GREEN)🧠 Creando chunks inteligentes en BigQuery...$(NC)"
	@echo "$(YELLOW)Usando: gemini-embedding-001 (768 dims optimizadas) + SQL nativo$(NC)"
	@echo "$(YELLOW)⚠️  Esto procesará TODO el dataset (3.4M objetos)$(NC)"
	@echo "$(YELLOW)⏰ Tiempo estimado: 4-7 horas$(NC)"
	@echo "$(YELLOW)💰 Costo estimado: \$$30-60 USD$(NC)"
	@echo "$(BLUE)💡 El proceso corre EN LA NUBE - puedes cerrar tu laptop$(NC)"
	@echo ""
	@read -p "¿Continuar? (y/N): " confirm && [ "$$confirm" = "y" ]
	@echo ""
	python3 scripts/bigquery_create_chunks.py

verify-bigquery: ## Verificar acceso y configuración de BigQuery
	@echo "$(BLUE)🔍 Verificando acceso a BigQuery...$(NC)"
	python3 scripts/verify_bigquery_access.py

setup-vertex-ai: ## Configurar conexión remota a Vertex AI
	@echo "$(GREEN)🔗 Configurando Vertex AI connection...$(NC)"
	python3 scripts/setup_vertex_ai_connection.py

setup-vertex-sql: ## Crear modelo Vertex AI con SQL directo
	@echo "$(GREEN)🔗 Creando modelo con SQL directo...$(NC)"
	python3 scripts/create_vertex_connection_sql.py

setup-bigquery-ml: ## Setup completo BigQuery ML (conexión + modelo)
	@echo "$(GREEN)🚀 Setup completo BigQuery ML + Vertex AI$(NC)"
	@echo "$(YELLOW)Esto creará conexión y modelo de embeddings$(NC)"
	./scripts/setup_bigquery_ml_complete.sh

test-chunks-simple: ## Prueba rápida de chunking (solo análisis)
	@echo "$(BLUE)🧪 Prueba rápida de chunking...$(NC)"
	@echo "$(YELLOW)Solo validación de chunking, sin embeddings$(NC)"
	python3 scripts/bigquery_test_simple.py

test-flow-complete: ## Prueba completa del flujo con embeddings dummy
	@echo "$(GREEN)🚀 Probando flujo completo...$(NC)"
	@echo "$(YELLOW)Chunking + embeddings dummy + búsquedas$(NC)"
	python3 scripts/bigquery_test_flow_complete.py

test-chunks: ## Probar chunking con 100 objetos representativos
	@echo "$(BLUE)🧪 Probando chunking con 100 objetos...$(NC)"
	@echo "$(YELLOW)Muestra estratificada: mega/large/medium/small$(NC)"
	python3 scripts/bigquery_test_chunks.py

generate-embeddings: ## Generar embeddings reales con Vertex AI API
	@echo "$(GREEN)🎯 Generando embeddings con Gemini...$(NC)"
	python3 scripts/bigquery_generate_embeddings.py

generate-test-embeddings: ## Generar embeddings para datos de prueba
	@echo "$(BLUE)🎯 Generando embeddings de prueba...$(NC)"
	python3 scripts/bigquery_generate_embeddings.py test

search-chunks: ## Realizar búsquedas vectoriales en BigQuery
	@echo "$(GREEN)🔍 Búsquedas vectoriales BigQuery...$(NC)"
	python3 scripts/bigquery_search_chunks.py demo

search-interactive: ## Búsqueda interactiva en BigQuery
	@echo "$(GREEN)🔍 Modo interactivo de búsqueda...$(NC)"
	python3 scripts/bigquery_search_chunks.py interactive

analyze-patterns: ## Analizar patrones del codebase con BigQuery
	@echo "$(BLUE)📊 Analizando patrones del codebase...$(NC)"
	python3 scripts/bigquery_search_chunks.py patterns

create-search-functions: ## Crear funciones SQL reutilizables
	@echo "$(BLUE)🔧 Creando funciones SQL de búsqueda...$(NC)"
	python3 scripts/bigquery_search_chunks.py functions

analyze-data: ## Análisis completo de datos y calidad
	@echo "$(BLUE)📊 Análisis completo de datos...$(NC)"
	python3 scripts/bigquery_analyze_data.py all

analyze-source: ## Analizar datos fuente antes de chunking
	@echo "$(BLUE)📊 Analizando datos fuente...$(NC)"
	python3 scripts/bigquery_analyze_data.py source

analyze-quality: ## Analizar calidad de chunks generados
	@echo "$(BLUE)📊 Analizando calidad de chunking...$(NC)"
	python3 scripts/bigquery_analyze_data.py chunks

check-readiness: ## Verificar si el sistema está listo para búsquedas
	@echo "$(BLUE)🚀 Verificando preparación del sistema...$(NC)"
	python3 scripts/bigquery_analyze_data.py readiness

# Pipeline completo BigQuery
bigquery-full: ## Pipeline completo BigQuery (dataset completo 3.4M objetos)
	@echo "$(GREEN)🚀 Pipeline completo BigQuery Vector Search$(NC)"
	@echo "$(YELLOW)⚠️  Dataset completo: 3.4M objetos$(NC)"
	@echo "$(YELLOW)⏰ Tiempo estimado: 4-7 horas$(NC)"
	@echo "$(YELLOW)💰 Costo estimado: \$$30-60 USD$(NC)"
	@echo "$(BLUE)💡 Corre EN LA NUBE - puedes cerrar tu laptop$(NC)"
	@echo ""
	@make create-chunks
	@echo ""
	@echo "$(GREEN)✅ Pipeline BigQuery completado!$(NC)"
	@echo "$(BLUE)🔍 Para buscar: make search-interactive$(NC)"

monitor-bigquery: ## Monitorear progreso del pipeline en la nube
	@echo "$(BLUE)📊 Monitoreando pipeline BigQuery...$(NC)"
	@echo "$(YELLOW)Actualizándose cada 30 segundos$(NC)"
	./scripts/monitor_bigquery_pipeline.sh

compare-systems: ## Comparar BigQuery Vector Search vs Weaviate
	@echo "$(BLUE)⚖️  Comparando sistemas vectoriales...$(NC)"
	python3 scripts/compare_vector_systems.py

# Comandos de limpieza BigQuery
clean-chunks: ## Limpiar tablas de chunks (CUIDADO: borra datos)
	@echo "$(RED)⚠️  CUIDADO: Esto borrará las tablas de chunks$(NC)"
	@read -p "¿Estás seguro? (y/N): " confirm && [ "$$confirm" = "y" ]
	@echo "$(YELLOW)Limpiando tablas de chunks...$(NC)"
	@python3 -c "
	from google.cloud import bigquery;
	from app.bigquery_vector.config import BigQueryVectorConfig;
	config = BigQueryVectorConfig();
	client = bigquery.Client();
	try:
	    client.query(f'DROP TABLE IF EXISTS \`{config.full_chunks_table_id}\`').result();
	    client.query(f'DROP TABLE IF EXISTS \`{config.full_embeddings_table_id}\`').result();
	    print('✅ Tablas de chunks eliminadas');
	except Exception as e:
	    print(f'❌ Error: {e}')
	"

# ============================================================
# MCP Server Commands - Model Context Protocol
# ============================================================

mcp-build: ## Construir imagen MCP Server
	@echo "$(BLUE)Construyendo SQUIT MCP Server...$(NC)"
	$(DOCKER) build -f Dockerfile.mcp -t squit-mcp:latest .

mcp-run: ## Ejecutar MCP Server (modo HTTP)
	@echo "$(GREEN)Iniciando MCP Server (HTTP mode)...$(NC)"
	$(DOCKER_COMPOSE) --profile mcp up squit-mcp

mcp-run-bg: ## Ejecutar MCP Server en background
	@echo "$(GREEN)Iniciando MCP Server en background...$(NC)"
	$(DOCKER_COMPOSE) --profile mcp up -d squit-mcp

mcp-dev: ## Ejecutar MCP Server local (modo STDIO para desarrollo)
	@echo "$(BLUE)Iniciando MCP Server (STDIO mode)...$(NC)"
	MCP_TRANSPORT=stdio GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json python -m app.mcp_server

mcp-test: ## Probar tools MCP localmente
	@echo "$(BLUE)Probando tools MCP...$(NC)"
	GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json python scripts/test_mcp_local.py

mcp-logs: ## Ver logs del MCP Server
	$(DOCKER_COMPOSE) logs -f squit-mcp

mcp-stop: ## Detener MCP Server
	$(DOCKER_COMPOSE) --profile mcp down

mcp-inspector: ## Abrir MCP Inspector para testing interactivo
	@echo "$(BLUE)Abriendo MCP Inspector...$(NC)"
	@echo "$(YELLOW)Requiere: npm install -g @anthropics/mcp-inspector$(NC)"
	npx @anthropics/mcp-inspector python -m app.mcp_server

mcp-health: ## Verificar salud del MCP Server
	@echo "$(BLUE)Verificando salud del MCP Server...$(NC)"
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "$(RED)MCP Server no disponible$(NC)"
