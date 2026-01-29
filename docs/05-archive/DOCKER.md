# 🐳 Guía Completa de Docker - SQUIT

Documentación exhaustiva del sistema Docker para SQUIT CLI.

**Última actualización:** 2025-10-02

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Quick Start](#quick-start)
3. [Arquitectura del Sistema](#arquitectura-del-sistema)
4. [Comandos Make](#comandos-make)
5. [Configuración y Volúmenes](#configuración-y-volúmenes)
6. [Proceso de Build](#proceso-de-build)
7. [Troubleshooting](#troubleshooting)
8. [Comparación Docker vs Local](#comparación-docker-vs-local)
9. [Optimizaciones y Performance](#optimizaciones-y-performance)

---

## 🎯 Introducción

### ¿Por Qué Docker?

SQUIT CLI se ejecuta en Docker para proporcionar:

✅ **Aislamiento completo** - No contamina tu sistema host  
✅ **Dependencias garantizadas** - Mismo ambiente en todas partes  
✅ **Configuración persistente** - Archivos preservados entre ejecuciones  
✅ **Reproducibilidad** - Funciona igual en Mac, Linux, Windows  
✅ **Limpieza fácil** - Un comando para eliminar todo

### Abstracción Completa

```
Usuario escribe:     make squit
Sistema ejecuta:     docker compose --profile cli run --rm squit-cli
Container ejecuta:   python3 scripts/squit.py
Usuario interactúa:  squit[1]> que hace kayak?
```

**Todo el proceso es transparente para el usuario.**

---

## ⚡ Quick Start

### Pre-requisitos

1. **Docker Desktop instalado y corriendo**
   - macOS: https://docs.docker.com/desktop/install/mac-install/
   - Linux: https://docs.docker.com/engine/install/
   - Windows: https://docs.docker.com/desktop/install/windows-install/

2. **Configuración básica**
   ```bash
   cp .env.template .env
   nano .env  # Configurar GOOGLE_CLOUD_PROJECT, GEMINI_API_KEY
   cp ~/Downloads/tu-proyecto.json .config/credentials.json
   cp tu-catalogo.csv data/catalogo.csv  # Opcional
   ```

### Primera Ejecución

```bash
# 1. Limpiar cualquier imagen vieja (si existe)
make squit-clean

# 2. Construir imagen (sin cache, ~1-2 min)
make squit-rebuild

# Espera a que complete el build...
# Verás el prompt: squit[1]>
```

### Uso Diario

```bash
# Simplemente ejecutar
make squit

# Escribe tu pregunta
squit[1]> que hace kayak?
squit[2]> explicame AgAsignaFechasKayakProc
squit[3]> exit
```

---

## 🏗️ Arquitectura del Sistema

### Flujo Completo

```
┌─────────────────────────────────────────────────────────┐
│ USUARIO                                                 │
├─────────────────────────────────────────────────────────┤
│ $ make squit                                            │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│ MAKEFILE                                                │
├─────────────────────────────────────────────────────────┤
│ 1. Muestra banner ASCII                                 │
│ 2. Limpia contenedores viejos (opcional)                │
│ 3. Ejecuta: docker compose --profile cli run --rm ...   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│ DOCKER COMPOSE                                          │
├─────────────────────────────────────────────────────────┤
│ 1. Lee docker-compose.yml                               │
│ 2. Crea red squit-network (si no existe)                │
│ 3. Monta volúmenes según configuración                  │
│ 4. Carga variables de .env                              │
│ 5. Inicia container con flag -it (interactivo)          │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│ CONTAINER (squit-cli)                                   │
├─────────────────────────────────────────────────────────┤
│ Imagen: squit-squit-cli:latest                          │
│ Base: python:3.12-slim-bookworm                         │
│ Working dir: /workspace                                 │
│ ─────────────────────────────────────────────────────  │
│ PYTHONPATH=/workspace/app                               │
│ GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json │
│ + todas las vars de .env                                │
│ ─────────────────────────────────────────────────────  │
│ Ejecuta: python3 scripts/squit.py                       │
│ ─────────────────────────────────────────────────────  │
│ Scripts/squit.py:                                       │
│  1. Carga .env desde /workspace/.env                    │
│  2. Importa MasterAgent desde /workspace/app            │
│  3. Inicializa agente (Gemini 2.5 Flash)                │
│  4. Muestra prompt interactivo: squit[1]>               │
│  5. Procesa queries del usuario                         │
│  6. Guarda historial en volumen persistente             │
└─────────────────────────────────────────────────────────┘
```

### Componentes Clave

#### 1. **Dockerfile.cli** (Multi-Stage Build)

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim-bookworm AS builder
- Instala herramientas de compilación (gcc, g++, git, libpq-dev)
- Crea virtual environment en /opt/venv
- Instala TODAS las dependencias Python
- Usa cache de pip para builds rápidos

# Stage 2: Runtime
FROM python:3.12-slim-bookworm AS runtime
- Solo dependencias de runtime (libpq5, ca-certificates)
- Copia venv del builder (sin tools de compilación)
- Imagen final 50% más pequeña (~500 MB)
- Healthcheck incluido
```

**Beneficio:** Imagen optimizada sin bloat de compiladores.

#### 2. **docker-compose.yml** (Servicio squit-cli)

```yaml
squit-cli:
  build:
    context: .
    dockerfile: Dockerfile.cli
  
  env_file: .env  # Carga variables de entorno
  
  volumes:
    # Persistentes (rw)
    - ./.config:/workspace/.config:rw
    - ./data:/workspace/data:rw
    - squit-data:/workspace/.squit:rw
    
    # Solo lectura (ro)
    - ./.env:/workspace/.env:ro
    - ./app:/workspace/app:ro
    - ./scripts:/workspace/scripts:ro
  
  stdin_open: true  # Habilita stdin
  tty: true         # Habilita TTY
  
  profiles: [cli]   # No inicia automáticamente
```

**Importante:** `stdin_open` y `tty` solos NO son suficientes. Se necesita `docker compose run` (no `up`) para interactividad completa.

#### 3. **Makefile** (Comandos Automatizados)

```makefile
squit:
  - Muestra banner
  - Ejecuta: docker compose --profile cli run --rm squit-cli
  - Flag --rm: Auto-limpieza al salir

squit-rebuild:
  - Limpia contenedores viejos
  - Elimina imagen vieja
  - Build sin cache (--no-cache)
  - Ejecuta con 'run --rm' (interactivo)

squit-clean:
  - Elimina contenedores
  - Elimina imágenes
  - Elimina volúmenes (-v)
```

---

## 📦 Comandos Make Detallados

### `make squit` - Ejecutar CLI

**Qué hace:**
1. Muestra banner ASCII de SQUIT
2. Limpia contenedores viejos con `docker compose down`
3. Ejecuta `docker compose --profile cli run --rm squit-cli`

**Cuándo usar:**
- Uso normal diario
- Después de tener la imagen construida
- Para iniciar sesión interactiva

**Salida esperada:**
```
squit[1]> _
```

**Salir:**
- Escribir `exit` o `quit`
- Ctrl+C (detiene limpiamente)

---

### `make squit-rebuild` - Reconstruir Completo

**Qué hace:**
1. Detiene contenedores: `docker compose down`
2. Elimina imagen vieja: `docker rmi squit-squit-cli:latest`
3. Construye sin cache: `docker compose build --no-cache`
4. Ejecuta: `docker compose run --rm squit-cli`

**Cuándo usar:**
- Primera vez
- Después de cambios en requirements.txt
- Después de cambios en Dockerfile.cli
- Cuando hay errores de dependencias
- Después de `make squit-clean`

**Tiempo estimado:**
- Primera vez: ~1-2 min
- Con cache parcial: ~30-60 seg

---

### `make squit-build` - Solo Construir

**Qué hace:**
1. Detiene contenedores
2. Elimina imagen vieja
3. Construye sin cache
4. **NO ejecuta** (solo build)

**Cuándo usar:**
- Cuando solo quieres pre-construir la imagen
- Para verificar que el build funciona
- Antes de distribuir la imagen

---

### `make squit-clean` - Limpieza Total

**Qué hace:**
1. Detiene todos los contenedores del perfil cli
2. Elimina contenedores
3. Elimina volúmenes (-v flag)
4. Elimina todas las imágenes de SQUIT

**Cuándo usar:**
- Cuando hay problemas persistentes
- Para empezar de cero
- Antes de rebuild completo

**⚠️ ADVERTENCIA:** Elimina volúmenes persistentes (datos generados se pierden).

---

### `make help` - Ver Todos los Comandos

Lista todos los comandos disponibles con descripción.

---

## 🔧 Configuración y Volúmenes

### Tabla de Volúmenes Montados

| Host (Tu máquina) | Container | Permisos | Propósito |
|-------------------|-----------|----------|-----------|
| `.config/` | `/workspace/.config/` | `rw` | Credentials de Google Cloud |
| `data/` | `/workspace/data/` | `rw` | Catálogo de 280 apps |
| `.env` | `/workspace/.env` | `ro` | Variables de entorno |
| `app/` | `/workspace/app/` | `ro` | Código fuente (protegido) |
| `scripts/` | `/workspace/scripts/` | `ro` | Scripts CLI (protegido) |
| `squit-data` (volume) | `/workspace/.squit/` | `rw` | Datos generados |

**Permisos:**
- `rw` = Read/Write (persistente, se guardan cambios)
- `ro` = Read-Only (protegido, no se puede modificar)

### Variables de Entorno

**Cargadas desde `.env`:**
```bash
GOOGLE_CLOUD_PROJECT=dfor-prj-dev
GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json
GEMINI_API_KEY=tu-api-key
GEMINI_CHAT_MODEL=gemini-2.5-flash
BIGQUERY_DATASET=deacero_sql_objects
BIGQUERY_TABLE=sql_objects_code
# ... todas las demás
```

**Sobreescritas en container:**
```bash
PYTHONPATH=/workspace/app
GRPC_VERBOSITY=ERROR
GLOG_minloglevel=2
```

### Archivos que Persisten

✅ `.config/credentials.json` - Tu service account  
✅ `data/catalogo.csv` - 280 aplicaciones  
✅ `.env` - Variables (solo lectura en container)  
✅ Historial de queries - Volumen `squit-data`  
✅ Cache de agente - Volumen `squit-data`  

**Nada se pierde entre ejecuciones.**

---

## 🔨 Proceso de Build

### Dockerfile Multi-Stage Explicado

#### **Stage 1: Builder** (Compilación)

```dockerfile
FROM python:3.12-slim-bookworm AS builder

RUN apt-get install gcc g++ git libpq-dev
# ↑ Herramientas de compilación (solo para build)

RUN python -m venv /opt/venv
# ↑ Virtual environment aislado

RUN pip install -r requirements.txt --timeout=300 --retries=3
# ↑ Instala TODAS las dependencias:
#   - google-adk 1.15.1
#   - google-genai 1.40.0
#   - google-cloud-bigquery 3.38.0
#   - deprecated 1.2.18
#   - + 80 dependencias más

# Tiempo: ~30-50 seg con cache
```

**Salida del Stage 1:**
- Virtual environment completo en `/opt/venv`
- Tamaño: ~800 MB (con compiladores)

#### **Stage 2: Runtime** (Imagen Final)

```dockerfile
FROM python:3.12-slim-bookworm AS runtime

RUN apt-get install libpq5 ca-certificates
# ↑ Solo runtime libs (NO compiladores)

COPY --from=builder /opt/venv /opt/venv
# ↑ Copia venv del builder (sin gcc/g++)

COPY app/ ./app/
COPY scripts/ ./scripts/

CMD ["python3", "scripts/squit.py"]
```

**Salida del Stage 2:**
- Imagen final: ~500 MB (50% más pequeña)
- Solo lo necesario para ejecutar
- Sin bloat de herramientas de compilación

### Dependencias Instaladas

**Versiones exactas (validadas):**

```
Core Google:
├─ google-adk: 1.15.1
├─ google-genai: 1.40.0
├─ google-cloud-bigquery: 3.38.0
├─ google-cloud-bigquery-storage: 2.33.1
├─ google-cloud-aiplatform: 1.118.0
└─ google-auth: 2.41.1

Agentes y Tools:
├─ deprecated: 1.2.18 (requerido por google-adk)
├─ deprecation: 2.1.0 (usado por weaviate)
├─ langchain-core: 0.3.77
└─ mcp: 1.16.0

Data Processing:
├─ pandas: 2.3.3
├─ numpy: 1.26.4
└─ pyarrow: 15.0.2

Vector DB:
└─ weaviate-client: 4.17.0

Development:
├─ pytest: 7.4.4
├─ black: 24.10.0
├─ mypy: 1.18.2
└─ flake8: 7.3.0

+ 60 dependencias transitivas más
```

**Total:** ~90 paquetes Python instalados y validados.

### Cache de Build

Docker usa cache inteligente:

```
Primera vez (sin cache):
├─ Descarga imagen base: ~30 seg
├─ Instala apt packages: ~10 seg
├─ pip install deps: ~40 seg
└─ Total: ~1-2 min

Con cache (cambios menores):
├─ Usa layers cacheados: ~5 seg
├─ Solo reinstala lo que cambió: ~20 seg
└─ Total: ~30-60 seg

Sin cambios (imagen ya existe):
└─ Total: Instantáneo
```

---

## 🎯 Comandos Make - Explicación Exhaustiva

### 1. `make squit` - Uso Normal

**Comando completo ejecutado:**
```bash
docker compose --profile cli run --rm squit-cli
```

**Desglose:**
- `docker compose` - Orquestador de containers
- `--profile cli` - Activa servicios marcados con `profiles: [cli]`
- `run` - Ejecuta servicio de forma interactiva (NO `up`)
- `--rm` - Auto-limpieza cuando termina
- `squit-cli` - Nombre del servicio en docker-compose.yml

**¿Por qué `run` y no `up`?**

| Comando | Propósito | Interactivo | TTY | Auto-cleanup |
|---------|-----------|-------------|-----|--------------|
| `docker compose up` | Servicios daemon | ❌ No | Limitado | Manual |
| `docker compose run` | Comandos interactivos | ✅ Sí | Completo | Con --rm |

**SQUIT necesita `run`** porque:
- ✅ Acepta input del usuario (queries)
- ✅ Muestra prompt: `squit[1]>`
- ✅ Stdin/stdout completos
- ✅ Ctrl+C funciona correctamente

**Flags implícitos de `run`:**
- `-i` (interactive) → Mantiene stdin abierto
- `-t` (tty) → Asigna pseudo-terminal
- Heredado de `stdin_open: true` y `tty: true` en YAML

**Salida:**
```
squit[1]> _  ← Cursor esperando input
```

---

### 2. `make squit-rebuild` - Rebuild Completo

**Comandos ejecutados:**
```bash
# 1. Limpieza
docker compose --profile cli down
docker rmi squit-squit-cli:latest

# 2. Build
docker compose --profile cli build --no-cache squit-cli

# 3. Ejecutar
docker compose --profile cli run --rm squit-cli
```

**Paso a paso:**

**1. `docker compose down`**
- Detiene containers del profile cli
- Elimina containers
- Elimina red (si no tiene otros containers)
- NO elimina volúmenes (datos persisten)

**2. `docker rmi squit-squit-cli:latest`**
- Elimina imagen vieja
- Fuerza rebuild completo
- Previene usar cache corrupto

**3. `docker compose build --no-cache`**
- Construye imagen desde cero
- No usa cache de layers
- Garantiza versiones frescas de dependencias
- Toma ~1-2 min

**4. `docker compose run --rm`**
- Ejecuta CLI interactivo
- Con imagen recién construida

**Cuándo usar:**
- ✅ Primera vez
- ✅ Después de `git pull` con cambios en requirements.txt
- ✅ Después de modificar Dockerfile.cli
- ✅ Cuando hay errores de "module not found"
- ✅ Después de `make squit-clean`

---

### 3. `make squit-clean` - Limpieza Profunda

**Comandos ejecutados:**
```bash
docker compose --profile cli down -v
docker rmi squit-squit-cli:latest
docker rmi squit-cli:latest
docker rmi squit-cli:test
```

**Qué elimina:**

```
Contenedores:
├─ squit-cli (si está corriendo)
└─ Cualquier otro del perfil cli

Volúmenes (-v flag):
├─ squit-persistent-data ⚠️ SE PIERDEN DATOS
└─ Cualquier volumen anónimo

Imágenes:
├─ squit-squit-cli:latest (imagen principal)
├─ squit-cli:latest (si existe)
├─ squit-cli:test (imagen de tests)
└─ Layers huérfanos (dangling)

Red:
└─ squit-network (si no hay otros containers)
```

**⚠️ ADVERTENCIA:**

El flag `-v` elimina volúmenes, incluyendo:
- Historial de queries
- Cache del agente
- Cualquier dato generado

**Archivos del host NO se tocan:**
- `.config/credentials.json` ✅ Preservado
- `data/catalogo.csv` ✅ Preservado
- `.env` ✅ Preservado

**Usar cuando:**
- Hay problemas persistentes inexplicables
- Quieres empezar completamente de cero
- Vas a desinstalar SQUIT
- Cambios mayores en arquitectura

---

### 4. `make squit-build` - Solo Construir

**Comando ejecutado:**
```bash
docker compose --profile cli build --no-cache squit-cli
```

**Diferencia con `squit-rebuild`:**
- ✅ Construye imagen
- ❌ NO ejecuta el CLI

**Usar para:**
- Pre-construir imagen antes de distribuir
- Validar que el build funciona
- CI/CD pipelines
- Preparar imagen sin iniciar container

---

## 🔍 Troubleshooting Exhaustivo

### Error: "No module named 'deprecated'"

**Síntomas:**
```
ModuleNotFoundError: No module named 'deprecated'
google/adk/tools/base_tool.py, line 23
```

**Causa:**
- Imagen vieja en cache (google-adk 0.5.0 sin deprecated)
- requirements.txt no tenía la dependencia

**Solución:**
```bash
# 1. Verificar requirements.txt
grep "deprecated" requirements.txt
# Debe mostrar: deprecated>=1.2.14

# 2. Limpiar y rebuild
make squit-clean
make squit-rebuild
```

**Verificar fix:**
```bash
docker run --rm squit-squit-cli:latest python3 -c "
import deprecated
print(f'deprecated: {deprecated.__version__}')
"
# Debe mostrar: deprecated: 1.2.18
```

---

### Error: "No module named 'google.adk.apps'"

**Síntomas:**
```
ModuleNotFoundError: No module named 'google.adk.apps'
```

**Causa:**
- google-adk versión 0.5.0 (vieja, sin módulo `apps`)
- requirements.txt tenía `google-adk>=0.5.0,<1.0.0`

**Solución:**
```bash
# 1. Verificar requirements.txt
grep "google-adk" requirements.txt
# Debe mostrar: google-adk>=1.15.0

# 2. Rebuild completo
make squit-clean
make squit-rebuild
```

**Verificar fix:**
```bash
docker run --rm squit-squit-cli:latest python3 -c "
import google.adk
print(f'google-adk: {google.adk.__version__}')
from google.adk.apps import App
print('✅ google.adk.apps existe')
"
# Debe mostrar: google-adk: 1.15.1
```

---

### Error: "network squit-network not found"

**Síntomas:**
```
Error response from daemon: network squit-network not found
```

**Causa:**
- Estaba usando `docker run` en lugar de `docker compose run`
- Red no se crea automáticamente con `docker run`

**Solución ya aplicada:**
- Cambio a `docker compose run` (crea red automáticamente)
- Ya está corregido en Makefile

**Si persiste:**
```bash
# Crear red manualmente
docker network create squit-network

# O usar make squit que la crea automáticamente
make squit
```

---

### Error: "Container name 'squit-cli' already in use"

**Síntomas:**
```
Error: container name squit-cli is already in use
```

**Causa:**
- Container anterior no se limpió
- Sin flag `--rm`

**Solución:**
```bash
# Eliminar container viejo
docker rm -f squit-cli

# O usar clean
make squit-clean
```

---

### Prompt `squit[1]>` no aparece

**Síntomas:**
- Container inicia
- Muestra banner
- Se queda esperando sin prompt

**Causa:**
- Usando `docker compose up` en lugar de `run`
- stdin/tty no configurados correctamente

**Solución ya aplicada:**
- Makefile usa `docker compose run --rm` (ya corregido)

**Verificar:**
```bash
# Debe ver squit[1]> al final
make squit
```

---

### Build muy lento o falla con timeout

**Síntomas:**
```
ERROR: pip install timeout
```

**Causa:**
- Red lenta
- Timeout muy corto

**Solución ya aplicada:**
- Dockerfile.cli usa `--timeout=300 --retries=3`

**Si persiste:**
```bash
# Aumentar timeout manualmente
docker build -f Dockerfile.cli \
  --build-arg PIP_TIMEOUT=600 \
  -t squit-squit-cli:latest .
```

---

### Imagen muy grande

**Síntomas:**
```
squit-squit-cli:latest  800MB  (demasiado grande)
```

**Solución ya aplicada:**
- Multi-stage build (Stage 1: builder, Stage 2: runtime)
- Imagen final: ~500 MB

**Verificar tamaño:**
```bash
docker images squit-squit-cli:latest
# Debe mostrar ~500 MB
```

---

## 📊 Comparación Docker vs Local

### Tabla Comparativa Exhaustiva

| Aspecto | Docker (`make squit`) | Local (`python3 scripts/squit.py`) |
|---------|----------------------|-------------------------------------|
| **Setup inicial** | 1-2 min (build) | 10-15 min (instalar deps) |
| **Dependencias** | ✅ Auto-instaladas | ⚠️ Manual (pip install -r) |
| **Versión Python** | ✅ 3.12 (garantizada) | ⚠️ Depende de sistema |
| **Aislamiento** | ✅ Total (venv en container) | ❌ Usa Python global |
| **Portabilidad** | ✅ Funciona en Mac/Linux/Win | ⚠️ Depende de OS |
| **Performance** | ⚠️ Overhead ~5-10% | ✅ Nativa 100% |
| **Persistencia** | ✅ Volúmenes Docker | ✅ Directo en filesystem |
| **Limpieza** | ✅ `make squit-clean` | ⚠️ Desinstalar deps |
| **Debugging** | ⚠️ Logs indirectos | ✅ Directo |
| **Actualización** | ✅ `git pull && make squit-rebuild` | ⚠️ `git pull && pip install -U -r requirements.txt` |
| **Espacio en disco** | ⚠️ ~500 MB (imagen) | ✅ ~200 MB (libs en site-packages) |
| **RAM usage** | ⚠️ +100-200 MB (overhead Docker) | ✅ Nativa |
| **Compatibilidad** | ✅ 99% (solo requiere Docker) | ⚠️ Depende de sistema |
| **Seguridad** | ✅ Aislado, readonly volumes | ⚠️ Acceso completo al sistema |

### Recomendaciones de Uso

**Usar Docker cuando:**
- ✅ Primera vez con SQUIT
- ✅ Producción o ambiente estable
- ✅ Múltiples usuarios en equipo (mismo ambiente)
- ✅ No quieres instalar deps Python localmente
- ✅ Quieres aislamiento total

**Usar Local cuando:**
- ✅ Desarrollo activo en el código
- ✅ Debugging intensivo
- ✅ Performance crítica (latencia mínima)
- ✅ Ya tienes ambiente Python configurado
- ✅ Prototipado rápido

**Uso híbrido (recomendado para devs):**
- Local para desarrollo
- Docker para testing/producción
- `make squit` para demos

---

## ⚙️ Optimizaciones y Performance

### Multi-Stage Build Benefits

```
Single-stage:               Multi-stage:
┌─────────────┐             ┌─────────────┐
│ python:3.12 │             │ Builder     │
│ + gcc/g++   │             │ + gcc/g++   │
│ + git       │             │ + todas deps│
│ + libpq-dev │             └──────┬──────┘
│ + todas deps│                    │ copia venv
│             │                    ↓
│ Tamaño:     │             ┌─────────────┐
│ ~800 MB     │             │ Runtime     │
│             │             │ + solo libs │
└─────────────┘             │ + venv      │
                            │             │
                            │ Tamaño:     │
                            │ ~500 MB     │
                            └─────────────┘

Diferencia: -300 MB (37% más pequeña)
```

### Build Cache Layers

Docker cachea cada layer del Dockerfile:

```
Layer 1: FROM python:3.12          → CACHED (si ya existe)
Layer 2: RUN apt-get install...    → CACHED (si no cambió)
Layer 3: RUN python -m venv        → CACHED
Layer 4: COPY requirements.txt     → INVALIDATED si cambió
Layer 5: RUN pip install...        → REBUILD si Layer 4 cambió
Layer 6: COPY app/                 → REBUILD si código cambió
```

**Optimización en Dockerfile.cli:**
```dockerfile
# Copiar requirements ANTES del código
COPY requirements.txt .
RUN pip install -r requirements.txt  # ← Se cachea si no cambió

# Copiar código DESPUÉS
COPY app/ ./app/  # ← Cambios frecuentes no invalidan pip install
```

### Virtual Environment Aislado

**Beneficios:**
```
Host Python: 3.12 (tu sistema)
  ├─ tus paquetes
  ├─ tus versiones
  └─ NO afectado por Docker

Container Python: 3.12 (aislado)
  └─ /opt/venv/
      ├─ google-adk 1.15.1
      ├─ google-genai 1.40.0
      └─ Todo aislado del host
```

**Sin conflictos entre:**
- Tu ambiente local de desarrollo
- El ambiente de SQUIT en Docker

---

## 🔐 Seguridad y Mejores Prácticas

### Protección de Credenciales

```
❌ MAL (copiar a imagen):
COPY .config/credentials.json /app/

✅ BIEN (montar como volumen):
volumes:
  - ./.config:/workspace/.config:rw

Resultado:
- Credentials NO van a la imagen Docker
- NO se pueden extraer con 'docker save'
- Solo disponibles en runtime
- Se pueden actualizar sin rebuild
```

### Readonly Volumes para Código

```yaml
volumes:
  - ./app:/workspace/app:ro      # ← Readonly
  - ./scripts:/workspace/scripts:ro
```

**Beneficios:**
- Container no puede modificar tu código
- Protección contra bugs o malware
- Auditable (código no muta)

### .dockerignore Optimizado

```dockerignore
# NO copiar a imagen:
.env              # Variables sensibles
credentials.json  # Credenciales
data/catalogo.csv # Datos privados
.git/             # Historial innecesario
docs/             # Documentación pesada
```

**Resultado:**
- Contexto de build ~80% más pequeño
- Build más rápido
- Menos datos sensibles en imagen

---

## 📚 Referencias Técnicas

### Documentación Docker Oficial

- **docker compose run**: https://docs.docker.com/compose/reference/run/
- **Multi-stage builds**: https://docs.docker.com/build/building/multi-stage/
- **Volumes**: https://docs.docker.com/storage/volumes/
- **Networks**: https://docs.docker.com/network/

### Archivos del Proyecto

| Archivo | Propósito | Líneas |
|---------|-----------|--------|
| `Dockerfile.cli` | Build de imagen CLI | 72 |
| `docker-compose.yml` | Orquestación (servicio squit-cli) | 106 |
| `Makefile` | Comandos automatizados | 423 |
| `.dockerignore` | Optimización de build | 60 |
| `DOCKER_QUICKSTART.md` | Quick start | 120 |
| `INSTRUCCIONES_DOCKER.md` | Guía paso a paso | 140 |
| `docs/usage/DOCKER.md` | Esta guía (exhaustiva) | 800+ |

---

## 🎓 Flujos de Trabajo Completos

### Flujo 1: Primer Uso

```bash
# Setup (una vez)
cd squit
cp .env.template .env
nano .env  # GOOGLE_CLOUD_PROJECT, GEMINI_API_KEY
cp ~/Downloads/proyecto.json .config/credentials.json

# Primera ejecución
make squit-rebuild  # Build ~1-2 min

# Uso
squit[1]> que hace kayak?
squit[2]> exit

# Siguientes veces
make squit  # Instantáneo
```

### Flujo 2: Desarrollo

```bash
# Hacer cambios en app/
nano app/agentic_adk/agents/master_agent.py

# NO necesitas rebuild (volumen montado como ro)
make squit  # Usa código actualizado automáticamente

# Si cambias requirements.txt
nano requirements.txt
make squit-rebuild  # Rebuild necesario
```

### Flujo 3: Actualización desde Git

```bash
# Pull cambios
git pull origin main

# Si hubo cambios en Dockerfile o requirements
make squit-rebuild

# Si solo cambió código (app/, scripts/)
make squit  # Usa código nuevo automáticamente
```

### Flujo 4: Limpieza y Reinstalación

```bash
# Algo salió mal, empezar de cero
make squit-clean
make squit-rebuild

# Fresh start garantizado
```

---

## 📊 Métricas y Estadísticas

### Tamaños de Imagen

```
Layer                          Tamaño
────────────────────────────────────────
python:3.12-slim-bookworm      ~130 MB
+ apt packages (runtime)        ~15 MB
+ Python venv (/opt/venv)      ~350 MB
+ app/ + scripts/               ~2 MB
────────────────────────────────────────
Total imagen final:            ~500 MB
```

### Tiempos de Ejecución

| Operación | Sin Cache | Con Cache | Reuso Imagen |
|-----------|-----------|-----------|--------------|
| `make squit-rebuild` | 1-2 min | 30-60 seg | N/A |
| `make squit-build` | 1-2 min | 30-60 seg | N/A |
| `make squit` | N/A | N/A | <1 seg |
| `make squit-clean` | <5 seg | <5 seg | <5 seg |

### Dependencias Instaladas

```
Categoría              # Paquetes   Tamaño
─────────────────────────────────────────────
Google Cloud              15        ~180 MB
Google AI (genai, adk)     2        ~120 MB
Data Processing            5         ~80 MB
Development Tools          8         ~40 MB
Vector DB                  1         ~20 MB
Misc (crypto, http, etc)  60         ~60 MB
─────────────────────────────────────────────
Total:                    ~90        ~500 MB
```

---

## 🔗 Enlaces y Recursos

### Documentación SQUIT

- **README Principal**: [../../README.md](../../README.md)
- **Quick Start Docker**: [../../DOCKER_QUICKSTART.md](../../DOCKER_QUICKSTART.md)
- **Instrucciones Docker**: [../../INSTRUCCIONES_DOCKER.md](../../INSTRUCCIONES_DOCKER.md)
- **INDEX Docs**: [../INDEX.md](../INDEX.md)

### Archivos Técnicos

- **Dockerfile.cli**: [../../Dockerfile.cli](../../Dockerfile.cli)
- **docker-compose.yml**: [../../docker-compose.yml](../../docker-compose.yml)
- **Makefile**: [../../Makefile](../../Makefile)
- **requirements.txt**: [../../requirements.txt](../../requirements.txt)

---

## 💡 Tips y Mejores Prácticas

### Para Usuarios

✅ **DO:**
- Usar `make squit` para uso diario
- Usar `make squit-rebuild` después de git pull
- Mantener Docker Desktop actualizado
- Revisar logs con `docker logs squit-cli`

❌ **DON'T:**
- No usar `docker compose up` (no es interactivo)
- No modificar docker-compose.yml sin documentar
- No eliminar volúmenes sin backup

### Para Desarrolladores

✅ **DO:**
- Probar cambios localmente primero
- Usar `make squit-rebuild` después de cambios en requirements
- Documentar cambios en Dockerfile
- Mantener .dockerignore actualizado

❌ **DON'T:**
- No hardcodear credentials en Dockerfile
- No copiar archivos sensibles a imagen
- No usar `latest` tag en producción real

---

**Última actualización:** 2025-10-02  
**Mantenido por:** Karim Touma | Grupo DeAcero  
**Versión Docker:** 1.0.0  
**google-adk:** 1.15.1  
**python:** 3.12-slim-bookworm
