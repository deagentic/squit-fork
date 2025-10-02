# 🎯 SQUIT - "SQL Quit"
## Democratizando Código Legacy con IA

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![BigQuery](https://img.shields.io/badge/BigQuery-Native-4285F4?logo=google-cloud)](https://cloud.google.com/bigquery)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-8E75B2?logo=google)](https://ai.google.dev/)
[![LangChain](https://img.shields.io/badge/LangChain-Memory-00D084)](https://python.langchain.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **"SQL Quit"** - Libérate del código SQL críptico y mal documentado.  
> Convierte millones de líneas de código legacy en conocimiento accesible mediante IA.

**SQUIT** transforma código SQL legacy en una base de conocimiento inteligente y buscable. Usando embeddings semánticos, búsqueda híbrida y un agente conversacional con memoria, democratiza el acceso al conocimiento enterrado en décadas de desarrollo.

---

## ✨ Características Principales

- 🔍 **Búsqueda Semántica**: Encuentra código por intención, no por texto exacto
- 🤖 **Agente Conversacional**: Pregunta en lenguaje natural sobre tu codebase
- 💬 **Memoria Multi-Turn**: Conversaciones contextuales con historial
- ⚡ **Context Caching**: Latencia reducida 50%
- 📊 **Few-Shot Learning**: Aprende de queries anteriores automáticamente
- 🏗️ **100% BigQuery**: Escalable a millones de objetos SQL
- 🎯 **Clasificación Inteligente**: Organiza por dominio de negocio y complejidad
- 📈 **Analytics Built-in**: Métricas de uso en BigQuery

---

## 🚀 Quick Start (5 minutos)

### 1. Clonar el Repositorio
```bash
git clone https://github.com/grupodeacero/squit.git
cd squit
```

### 2. Configurar Credenciales
```bash
# 1. Copiar template de configuración
cp .env.template .env

# 2. Obtener y configurar credenciales de Google Cloud
# a) Descargar service account JSON desde Google Cloud Console
#    → IAM & Admin → Service Accounts → Create Key → JSON
cp ~/Downloads/tu-proyecto-xxxxx.json .config/credentials.json

# b) Obtener Gemini API Key
#    → https://makersuite.google.com/app/apikey

# 3. Editar .env con tus valores
nano .env

# Configuración mínima requerida:
# GOOGLE_CLOUD_PROJECT=tu-proyecto-id
# GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json  # ← Ruta correcta
# GEMINI_API_KEY=tu-gemini-api-key
# GEMINI_CHAT_MODEL=gemini-2.5-flash  # ← Modelo recomendado

# 4. Copiar catálogo de aplicaciones (280+ apps)
# Si tienes el catálogo real, copiarlo a:
# cp tu-catalogo.csv data/catalogo.csv
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Verificar Configuración (Opcional)
```bash
# Ver configuración actual del sistema
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, 'app')

from bigquery_vector.config import BigQueryVectorConfig
from agentic_adk.catalog_enricher import CatalogEnricher
import os

print('✅ CONFIGURACIÓN ACTUAL:')
print(f'   BigQuery: {BigQueryVectorConfig().PROJECT_ID}')
print(f'   Dataset: {BigQueryVectorConfig().DATASET_ID}')
print(f'   Catálogo: {len(CatalogEnricher().catalog_df)} apps')
print(f'   Credenciales: {os.getenv(\"GOOGLE_APPLICATION_CREDENTIALS\")}')
"
```

### 5. Ejecutar el Asistente

#### **Opción A: Con Docker** 🐳 (Recomendado - Aislado y Reproducible)

**Primera vez (construir imagen):**
```bash
make squit-rebuild
```

**Siguientes veces:**
```bash
make squit
```

**Ventajas de Docker:**
- ✅ **Aislamiento total** - No contamina tu Python local
- ✅ **Dependencias incluidas** - Todo pre-instalado (google-adk 1.15.1, etc.)
- ✅ **Reproducible** - Funciona igual en cualquier máquina
- ✅ **Configuración persistente** - Tus archivos se preservan (.config/, data/)
- ✅ **Limpieza fácil** - `docker rm` y no queda nada

**Comandos útiles:**
```bash
make squit          # Ejecutar CLI interactivo
make squit-rebuild  # Reconstruir imagen completa (si cambió código)
make squit-clean    # Limpiar todo (imágenes, contenedores, volúmenes)
make help           # Ver todos los comandos disponibles
```

#### **Opción B: Directamente con Python** 🐍

```bash
python3 scripts/squit.py
```

**Cuándo usar:**
- Desarrollo rápido
- Debugging
- Ya tienes Python 3.12+ y dependencias instaladas

💡 **Recomendación:** Usa Docker (`make squit`) para producción y uso diario.

```
    ███████╗ ██████╗ ██╗   ██╗██╗████████╗
    ██╔════╝██╔═══██╗██║   ██║██║╚══██╔══╝
    ███████╗██║   ██║██║   ██║██║   ██║   
    ╚════██║██║▄▄ ██║██║   ██║██║   ██║   
    ███████║╚██████╔╝╚██████╔╝██║   ██║   
    ╚══════╝ ╚══▀▀═╝  ╚═════╝ ╚═╝   ╚═╝   
    
  "SQL Quit" - Democratizando Código Legacy
  Búsqueda Inteligente | 2.9M Objetos SQL
  Powered by Gemini 2.5 Flash + Google ADK

squit[1]> hablame de kayak

"Kayak" es un sistema de gestión de fechas de embarque...
Los principales stored procedures son:
- AgAsignaFechasKayakProc
- KayAsignaFechasKayakProc
...

squit[2]> explicame el primero que mencionaste

✅ Memoria mantiene contexto

AgAsignaFechasKayakProc asigna fechas estimadas...

squit[3]> exit
```

### 🐳 Detalles de Ejecución con Docker

**Arquitectura del Sistema Dockerizado:**

```
┌─────────────────────────────────────────────────────┐
│ make squit                                          │
│  ↓                                                   │
│ docker compose --profile cli run --rm squit-cli     │
│  ↓                                                   │
│ ┌───────────────────────────────────────┐           │
│ │ Container: squit-cli                  │           │
│ │ ─────────────────────────────────────│           │
│ │ Imagen: squit-squit-cli:latest        │           │
│ │ Base: python:3.12-slim-bookworm       │           │
│ │ ─────────────────────────────────────│           │
│ │ Dependencias instaladas:              │           │
│ │  • google-adk: 1.15.1                 │           │
│ │  • google-genai: 1.40.0               │           │
│ │  • google-cloud-bigquery: 3.38.0      │           │
│ │  • deprecated: 1.2.18                 │           │
│ │  • + 80 librerías más                 │           │
│ │ ─────────────────────────────────────│           │
│ │ Volúmenes montados (del host):        │           │
│ │  .config/   → /workspace/.config/  ✅│           │
│ │  data/      → /workspace/data/     ✅│           │
│ │  .env       → /workspace/.env      ✅│           │
│ │  app/       → /workspace/app/      🔒│           │
│ │  scripts/   → /workspace/scripts/  🔒│           │
│ │ ─────────────────────────────────────│           │
│ │ Comando ejecutado:                    │           │
│ │  python3 scripts/squit.py             │           │
│ └───────────────────────────────────────┘           │
└─────────────────────────────────────────────────────┘

✅ = Persistente (lectura/escritura)
🔒 = Protegido (solo lectura)
```

**¿Por qué `docker compose run` en lugar de `up`?**

- `docker compose up` → Para servicios daemon (background)
- `docker compose run` → Para comandos interactivos (TTY completo)

El CLI necesita **interactividad completa** (leer input del usuario), por eso usamos `run --rm`.

**Comandos completos documentados:** [docs/usage/DOCKER.md](docs/usage/DOCKER.md)
```

---

## ⚙️ Configuración Actual del Sistema

### 🔧 Configuración de Producción

El sistema está configurado y funcionando con:

#### 1. **Google Cloud Platform**
```
Proyecto: dfor-prj-dev
Dataset: deacero_sql_objects
Región: us-central1
```

**Tablas en BigQuery:**
- `sql_objects_code` → ~3.4M objetos SQL (fuente)
- `intelligent_chunks` → ~5-10M chunks procesados
- `chunk_embeddings` → Vectores 768-dim (Gemini)
- `query_history` → Analytics de queries

#### 2. **Catálogo de Aplicaciones**
```
Ubicación: data/catalogo.csv
Apps documentadas: 280
Tamaño: 101 KB
```

Dominios de negocio incluidos:
- Ventas, Inventario, Finanzas
- Producción, Compras, Logística
- Recursos Humanos

#### 3. **Modelos de IA**

**Agente Principal:**
```
Modelo: gemini-2.5-flash
Temperature: 0.1 (determinista)
Max tokens: 8000
```

**Embeddings:**
```
Modelo: gemini-embedding-001
Dimensiones: 768
Task type: CODE_RETRIEVAL_QUERY
```

#### 4. **Credenciales y Seguridad**
```
✅ Service Account: .config/credentials.json
✅ API Keys: Configuradas en .env
✅ .gitignore: Protección activa
```

**Permisos de Service Account:**
- BigQuery Data Viewer
- BigQuery Job User
- BigQuery Data Editor

#### 5. **Arquitectura del Sistema**

```
┌─────────────────┐
│   Usuario CLI   │ (scripts/squit.py)
└────────┬────────┘
         │
         v
┌─────────────────┐
│  MasterAgent    │ (Gemini 2.5 Flash)
│  + Memoria      │ (Multi-turn conversacional)
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    v         v
┌───────┐  ┌──────────────┐
│Search │  │CatalogEnrich │
│Agent  │  │(280 apps)    │
└───┬───┘  └──────────────┘
    │
    v
┌─────────────────┐
│ BigQuery Vector │
│ 3.4M objetos    │
│ 768-dim embeds  │
└─────────────────┘
```

---

## 📊 El Problema que Resolvemos

### Código Legacy Sin Documentar

Organizaciones con décadas de desarrollo SQL enfrentan:

- 📚 **Millones de líneas** de código sin documentar
- 🔍 **Conocimiento tribal** en cabezas de desarrolladores veteranos
- 🌀 **Lógica de negocio enterrada** en procedures de 10K+ líneas
- ⏰ **Horas perdidas** buscando "dónde está implementado X"
- 🚫 **Barreras de entrada** para nuevos desarrolladores
- 💸 **Riesgo de cambios** por dependencias invisibles

### La Solución: Democratización con IA

**SQUIT** democratiza el acceso al conocimiento legacy mediante:

1. **🏗️ Estructuración Inteligente**: Clasifica y chunka código automáticamente
2. **🔍 Búsqueda Híbrida**: Encuentra código por significado (70% semántico + 30% keywords)
3. **🤖 Comprensión con IA**: Agente que explica qué hace el código y por qué
4. **🎯 Democratización**: Accesible para todos, no solo expertos

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    SQUIT Architecture                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Extracción SQL                                          │
│     └─> SQL Server → BigQuery (sql_objects_code)           │
│                                                             │
│  2. Pipeline BigQuery                                       │
│     ├─> Chunking Inteligente (30-45min)                    │
│     ├─> Embeddings Gemini (2-4 horas)                      │
│     └─> Vector Index IVF (~10min)                          │
│                                                             │
│  3. Agente Conversacional (Google ADK)                      │
│     ├─> Gemini 2.5 Flash                                   │
│     ├─> Context Caching (-50% latencia)                    │
│     ├─> LangChain Memory (últimos 10 turnos)               │
│     └─> QueryLogger BigQuery (few-shots)                   │
│                                                             │
│  4. Búsqueda Híbrida                                        │
│     ├─> Vector Search (70%)                                │
│     └─> Keyword Search (30%)                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📖 Documentación

### 📚 [Índice Completo de Documentación](docs/INDEX.md)

### Guías Principales

#### 🔧 Setup y Configuración
- **[Pipeline BigQuery Completo](docs/setup/BIGQUERY_VECTOR_COMPLETE.md)** - Guía paso a paso del pipeline
- **[Extracción de SQL Server](docs/setup/EXTRACTION_GUIDE.md)** - Cómo extraer código SQL
- **[Configuración de Modelos](docs/setup/MODELS_STANDARD.md)** - Setup de Gemini

#### 🎯 Uso de la Aplicación
- **[Guía del Agente Conversacional](docs/usage/AGENTIC_ADK_GUIDE.md)** - Cómo usar `squit.py`
- **[API Reference](docs/usage/API.md)** - Referencias de APIs
- **[Ejemplos](docs/usage/EXAMPLES.md)** - Casos de uso y snippets

#### 💻 Desarrollo y Arquitectura
- **[System Overview](docs/development/SYSTEM_OVERVIEW.md)** - Arquitectura del sistema
- **[Phase 1 Implementation](docs/development/PHASE1_IMPLEMENTATION.md)** - Mejoras de memoria
- **[Memory Research](docs/development/MEMORY_RESEARCH.md)** - Investigación de soluciones

---

## 🛠️ Tecnologías

### Core Stack
- **Python 3.11+**: Lenguaje principal
- **Google BigQuery**: Data warehouse y vector database
- **Gemini 2.5 Flash**: LLM para agente conversacional
- **Gemini Embedding-001**: Embeddings semánticos (768 dims)
- **Google ADK**: Framework de agentes
- **LangChain**: Memoria estructurada

### Opcional
- **Weaviate**: Vector database alternativo (Fase 2)
- **Docker**: Containerización

---

## 📊 Dataset de Ejemplo

El proyecto incluye ejemplos para trabajar con datasets SQL legacy:

- **3.4M objetos SQL** de 275 servidores
- **Décadas de código** sin documentar
- **7 dominios de negocio**: ventas, inventario, finanzas, producción, compras, logística, RRHH

---

## 🎓 Casos de Uso

### 1. "¿Dónde está implementada la lógica de autenticación?"

**Búsqueda tradicional (grep):**
```bash
# ❌ Solo encuentra texto exacto
grep -r "authentication" *.sql
```

**SQUIT:**
```bash
squit[1]> donde esta la lógica de autenticación de usuarios

✅ Encuentra código relacionado aunque use términos diferentes
✅ Entiende sinónimos (login, validación, permisos)
✅ Muestra contexto y explicaciones
```

### 2. "¿Qué hace este procedimiento?"

```bash
squit[1]> explicame AgAsignaFechasKayakProc

Procedimiento: AgAsignaFechasKayakProc
Dominio: Ventas / Logística
Complejidad: Alta (8.5/10)

Resumen: Asigna fechas estimadas de embarque y entrega 
para pedidos del sistema Kayak. Maneja simulaciones, 
persistencia de fechas y actualización de múltiples tablas.

Depende de: 12 tablas, 3 procedimientos
Usado por: 8 procesos batch, 2 aplicaciones web
```

### 3. Análisis de Impacto

```bash
squit[1]> si modifico la tabla VentasPedidos, qué se rompe

✅ Analiza dependencias
✅ Identifica procedures/views que la usan
✅ Estima impacto por dominio de negocio
```

---

## 📈 Performance

| Métrica | Valor |
|---------|-------|
| **Objetos soportados** | 3.4M+ |
| **Latencia de búsqueda** | ~2.5s (con cache) |
| **Precisión semántica** | ~90% |
| **Context retention** | 91% |
| **Throughput embeddings** | 300-500/seg |

---

## 📁 Estructura del Proyecto

```
squit/
├── .config/
│   └── credentials.json          # ← Service account de Google Cloud
├── data/
│   └── catalogo.csv               # ← Catálogo de 280+ aplicaciones
├── app/
│   ├── agentic_adk/               # Sistema agentico con Google ADK
│   │   ├── agents/                # Agentes especializados
│   │   │   ├── master_agent.py    # Orquestador principal
│   │   │   ├── code_search_agent.py
│   │   │   └── explanation_agent.py
│   │   ├── tools/                 # Herramientas para agentes
│   │   │   ├── vector_search.py   # Búsqueda en BigQuery
│   │   │   └── dependency_search.py
│   │   ├── catalog_enricher.py    # Enriquecimiento con catálogo
│   │   └── query_logger.py        # Analytics de queries
│   ├── bigquery_vector/           # Pipeline de datos
│   │   ├── chunking_pipeline.py   # Chunking inteligente
│   │   ├── vector_search.py       # Búsquedas vectoriales
│   │   └── progress_tracker.py    # Tracking de progreso
│   └── squit_client/              # Cliente base BigQuery
├── scripts/
│   ├── squit.py                   # ← CLI principal (EMPEZAR AQUÍ)
│   ├── run_bigquery_pipeline.py   # Pipeline de datos
│   └── demo_*.py                  # Demos y ejemplos
├── docs/                          # Documentación completa
│   ├── INDEX.md                   # Índice maestro
│   ├── setup/                     # Guías de instalación
│   ├── usage/                     # Guías de uso
│   └── development/               # Docs técnicos
├── .env                           # ← Configuración (crear desde template)
├── .env.template                  # Template de configuración
└── requirements.txt               # Dependencias Python
```

### 🔑 Archivos de Configuración

| Archivo | Propósito | Ubicación Correcta | En Git |
|---------|-----------|-------------------|--------|
| `.env` | Variables de entorno | Root | ❌ No |
| `credentials.json` | Service account GCP | `.config/` | ❌ No |
| `catalogo.csv` | Catálogo de apps | `data/` | ❌ No |
| `.env.template` | Template de config | Root | ✅ Sí |
| `catalog.example.csv` | Ejemplo de catálogo | `data/` | ✅ Sí |

---

## 🔒 Seguridad y Privacidad

- ✅ **Credenciales**: Nunca se commitean (`.gitignore` robusto)
- ✅ **Service Accounts**: Permisos mínimos necesarios en GCP
- ✅ **API Keys**: Gestionadas via `.env` (no hardcodeadas)
- ✅ **Data Privacy**: Código SQL permanece en tu BigQuery
- ✅ **Gemini API**: Solo recibe queries del usuario, no todo el código
- ✅ **Rutas seguras**: Credenciales en `.config/`, catálogo en `data/`

---

## 🤝 Contribuir

¡Contribuciones son bienvenidas! Por favor lee [CONTRIBUTING.md](CONTRIBUTING.md) para detalles.

### Quick Contribution Guide

1. Fork el repositorio
2. Crea una branch (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la branch (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

### Áreas de Contribución

- 🐛 **Bug fixes**: Reporta o arregla bugs
- 📚 **Documentación**: Mejora docs o traducciones
- ✨ **Features**: Nuevas funcionalidades
- 🧪 **Tests**: Aumenta coverage de tests
- 🎨 **UI/UX**: Mejoras en CLI o interfaces

---

## 📝 Licencia

Este proyecto está bajo licencia MIT. Ver [LICENSE](LICENSE) para detalles.

---

## 👥 Autores

- **Karim Touma** - *Creador y maintainer* - [ktouma@deacero.com](mailto:ktouma@deacero.com)

### Grupo DeAcero
Proyecto desarrollado en Grupo DeAcero para democratizar el acceso al conocimiento enterrado en décadas de código SQL legacy.

---

## 🙏 Agradecimientos

- **Google Cloud** - BigQuery ML y Gemini API
- **Google ADK Team** - Framework de agentes
- **LangChain** - Librería de memoria estructurada
- **Comunidad Open Source** - Inspiración y herramientas

---

## 📬 Contacto

- **Email**: ktouma@deacero.com
- **Issues**: [GitHub Issues](https://github.com/grupodeacero/squit/issues)
- **Discussions**: [GitHub Discussions](https://github.com/grupodeacero/squit/discussions)

---

## 🗺️ Roadmap

### ✅ Fase 1 (Completada)
- [x] Pipeline BigQuery de chunks + embeddings
- [x] Búsqueda híbrida (vector + keywords)
- [x] Agente conversacional con Google ADK
- [x] Context Caching (latencia -50%)
- [x] LangChain Memory estructurada
- [x] QueryLogger BigQuery (few-shots)

### 🚧 Fase 2 (En Progreso)
- [ ] Weaviate Semantic Memory
- [ ] Entity tracking estructurado
- [ ] Few-shots por dominio de negocio
- [ ] Summarization de conversaciones largas
- [ ] **MCP Server** (Model Context Protocol) - Integración con Claude Desktop, Cursor, etc.

### 🔮 Fase 3 (Futuro)
- [ ] Vertex AI Memory Bank integration
- [ ] Multi-tenant support
- [ ] Web UI (Streamlit/Gradio)
- [ ] API REST para integraciones
- [ ] Support para más lenguajes (PL/SQL, T-SQL, etc.)
- [ ] MCP Tools extensibles para IDEs

---

## 📊 Project Stats

[![GitHub Repo](https://img.shields.io/badge/GitHub-grupodeacero%2Fsquit-181717?logo=github)](https://github.com/grupodeacero/squit)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/grupodeacero/squit)](https://github.com/grupodeacero/squit/commits/main)
[![GitHub last commit](https://img.shields.io/github/last-commit/grupodeacero/squit)](https://github.com/grupodeacero/squit/commits/main)
[![Lines of code](https://img.shields.io/tokei/lines/github/grupodeacero/squit)](https://github.com/grupodeacero/squit)

### Dataset & Performance
- **SQL Objects**: 3.4M+
- **BigQuery Tables**: 5+ (chunks, embeddings, history)
- **Search Latency**: ~2.5s (with cache)
- **Embedding Throughput**: 300-500 objects/sec
- **Context Retention**: 91%

---

**Hecho con ❤️ para democratizar el conocimiento legacy**

---

## 🔍 Verificar Estado del Sistema

### Comando de Diagnóstico Rápido

```bash
# Script de diagnóstico completo
python3 -c "
import sys, os
from pathlib import Path
sys.path.insert(0, 'app')

print('🔍 DIAGNÓSTICO RÁPIDO DEL SISTEMA\n')
print('='*50)

# 1. Archivos
print('\n📁 Archivos de Configuración:')
files = {
    '.env': Path('.env'),
    'credentials.json': Path('.config/credentials.json'),
    'catalogo.csv': Path('data/catalogo.csv')
}
for name, path in files.items():
    status = '✅' if path.exists() else '❌'
    print(f'   {status} {name}: {path}')

# 2. Variables
print('\n🔐 Variables de Entorno:')
env_vars = ['GOOGLE_CLOUD_PROJECT', 'GOOGLE_APPLICATION_CREDENTIALS', 'GEMINI_API_KEY']
for var in env_vars:
    val = os.getenv(var, '')
    status = '✅' if val else '❌'
    display = val[:20] + '...' if len(val) > 20 else val
    print(f'   {status} {var}: {display}')

# 3. Sistema
print('\n⚙️  Sistema:')
try:
    from bigquery_vector.config import BigQueryVectorConfig
    config = BigQueryVectorConfig()
    print(f'   ✅ BigQuery: {config.PROJECT_ID}')
    print(f'   ✅ Dataset: {config.DATASET_ID}')
except Exception as e:
    print(f'   ❌ Error: {e}')

try:
    from agentic_adk.catalog_enricher import CatalogEnricher
    enricher = CatalogEnricher()
    print(f'   ✅ Catálogo: {len(enricher.catalog_df)} aplicaciones')
except Exception as e:
    print(f'   ❌ Catálogo: {e}')

print('\n' + '='*50)
"
```

### Checklist de Configuración Actual

- [x] **Proyecto GCP:** `dfor-prj-dev`
- [x] **Dataset:** `deacero_sql_objects` (~3.4M objetos)
- [x] **Credenciales:** `.config/credentials.json` ✅
- [x] **Catálogo:** `data/catalogo.csv` (280 apps, 101 KB) ✅
- [x] **Modelo IA:** `gemini-2.5-flash`
- [x] **Embeddings:** 768-dim vectores
- [ ] **API Key Gemini:** Configurar en `.env` si no está

### Rutas Correctas Configuradas ✅

```
.config/credentials.json    ← Service Account (2.3 KB)
data/catalogo.csv            ← 280 aplicaciones (101 KB)
.env                         ← Variables de entorno
```

**Verificación automática:**
- Sistema busca catálogo en `data/` automáticamente
- Credenciales en `.config/` (ruta correcta configurada)
- Variables de entorno cargadas desde `.env`

---

## 🔗 Enlaces Útiles

- **Documentación:** [docs/INDEX.md](docs/INDEX.md) - Índice maestro
- **Configuración:** [docs/usage/API_CONFIG.md](docs/usage/API_CONFIG.md) - Guía detallada
- **Setup:** [docs/setup/BIGQUERY_VECTOR_COMPLETE.md](docs/setup/BIGQUERY_VECTOR_COMPLETE.md)
- **Agentes:** [docs/usage/AGENTIC_ADK_GUIDE.md](docs/usage/AGENTIC_ADK_GUIDE.md)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)

