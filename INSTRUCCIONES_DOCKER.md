# 🐳 Instrucciones Completas - SQUIT con Docker

**Guía paso a paso para ejecutar SQUIT en Docker sin errores.**

**IMPORTANTE:** Leer completamente antes de ejecutar.

---

## 🎯 Resumen Ejecutivo

**Comando final que usarás:**
```bash
make squit
```

**Pero PRIMERO debes:**
1. Configurar `.env` y credentials
2. Ejecutar `make squit-rebuild` (primera vez)
3. Luego sí, usar `make squit` normalmente

---

## 📋 Paso a Paso - Primera Vez

### Paso 1: Verificar Docker

```bash
# Verificar que Docker está instalado y corriendo
docker --version

# Debe mostrar algo como:
# Docker version 24.x.x
```

Si no está instalado:
- **macOS**: Descargar Docker Desktop desde https://docs.docker.com/desktop/install/mac-install/
- **Linux**: `sudo apt-get install docker-ce docker-ce-cli containerd.io`
- **Windows**: Descargar Docker Desktop desde https://docs.docker.com/desktop/install/windows-install/

```bash
# Iniciar Docker
# macOS: Abrir Docker Desktop
# Linux: sudo systemctl start docker
```

---

### Paso 2: Configurar Archivo `.env`

```bash
# Copiar template
cp .env.template .env

# Editar con tus valores
nano .env
```

**Variables REQUERIDAS (mínimo):**
```bash
GOOGLE_CLOUD_PROJECT=dfor-prj-dev
GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json
GEMINI_API_KEY=tu-api-key-aqui
GEMINI_CHAT_MODEL=gemini-2.5-flash
```

**Verificar:**
```bash
cat .env | grep -E "GOOGLE_CLOUD_PROJECT|GEMINI_API_KEY"
```

---

### Paso 3: Copiar Credentials de Google Cloud

```bash
# Descargar desde Google Cloud Console:
# → IAM & Admin → Service Accounts → Create Key → JSON

# Copiar a ubicación correcta
cp ~/Downloads/tu-proyecto-xxxxx.json .config/credentials.json

# Verificar que existe
ls -lh .config/credentials.json

# Debe mostrar: -rw------- ... credentials.json
# Permisos 600 son importantes para seguridad

# Si permisos son incorrectos:
chmod 600 .config/credentials.json
```

---

### Paso 4: Copiar Catálogo (Opcional)

```bash
# Si tienes el catálogo de 280 aplicaciones
cp tu-catalogo.csv data/catalogo.csv

# Verificar
ls -lh data/catalogo.csv
wc -l data/catalogo.csv
# Debe mostrar: ~280 líneas
```

**Nota:** Si no tienes catálogo, el sistema funciona igual pero sin enriquecimiento contextual.

---

### Paso 5: Limpiar Imágenes Viejas (Si existen)

```bash
# Solo necesario si ejecutaste versiones anteriores
make squit-clean

# Debe mostrar:
# Limpiando contenedores e imágenes...
# Limpieza completa
```

**Primera vez:** Puedes saltarte este paso.

---

### Paso 6: Construir Imagen Docker

```bash
make squit-rebuild
```

**Qué verás:**
```
Reconstruyendo CLI de SQUIT (sin cache)...
[+] Building 77.7s (18/18) FINISHED
 => [builder 4/4] RUN pip install -r requirements.txt
 => [runtime 2/5] COPY --from=builder /opt/venv /opt/venv
 => exporting to image
 ✔ squit-squit-cli Built

Iniciando CLI...
[+] Running 2/2
 ✔ Network squit-network Created
 ✔ Container squit-cli Created

    ███████╗ ██████╗ ██╗   ██╗██╗████████╗
    ... banner ...
    
  ✓ Agente listo

  💬 Conversación con memoria multi-turn activada
  
squit[1]> _  ← AQUÍ PUEDES ESCRIBIR
```

**Tiempo estimado:** 1-2 minutos

**⚠️ IMPORTANTE:** Si no ves el prompt `squit[1]>`, hay un problema. Ver [Troubleshooting](#troubleshooting).

---

### Paso 7: Probar el Sistema

```bash
# Ya estás en el prompt squit[1]>

# Probar una query simple
squit[1]> que hace kayak?

# Debe responder con información sobre el sistema Kayak

# Salir
squit[2]> exit
```

---

## 🔄 Uso Normal (Después de Primera Vez)

```bash
# Simplemente ejecutar
make squit

# Ya no construye, usa imagen existente
# Inicia en ~1 segundo

squit[1]> tu pregunta aquí
squit[2]> exit
```

---

## 🛠️ Comandos Make - Explicación Completa

### `make squit` - Uso Normal

**Qué hace internamente:**
```makefile
1. Muestra banner ASCII de SQUIT
2. Ejecuta: docker compose --profile cli down (limpia viejos)
3. Ejecuta: docker compose --profile cli run --rm squit-cli
```

**Comando Docker ejecutado:**
```bash
docker compose --profile cli run --rm squit-cli
```

**Flags:**
- `--profile cli` → Activa solo servicios marcados [cli]
- `run` → Modo interactivo (NO `up`)
- `--rm` → Auto-limpieza al salir

**Cuándo usar:**
- ✅ Uso diario normal
- ✅ Después de tener imagen construida
- ✅ Cuando no cambió código/dependencias

**Tiempo:** <1 segundo (instantáneo)

---

### `make squit-rebuild` - Reconstruir Completo

**Qué hace internamente:**
```makefile
1. docker compose --profile cli down     # Detener
2. docker rmi squit-squit-cli:latest     # Eliminar imagen
3. docker compose --profile cli build --no-cache squit-cli  # Construir
4. docker compose --profile cli run --rm squit-cli  # Ejecutar
```

**Cuándo usar:**
- ✅ **Primera vez** (OBLIGATORIO)
- ✅ Después de `git pull` con cambios en requirements.txt
- ✅ Después de modificar Dockerfile.cli
- ✅ Cuando hay errores de "module not found"
- ✅ Después de `make squit-clean`

**Tiempo:** 1-2 min (sin cache) | 30-60 seg (con cache parcial)

**⚠️ IMPORTANTE:** Este es el comando para primera vez.

---

### `make squit-clean` - Limpieza Total

**Qué hace internamente:**
```makefile
1. docker compose --profile cli down -v  # Detener + eliminar volúmenes
2. docker rmi squit-squit-cli:latest     # Eliminar imagen principal
3. docker rmi squit-cli:latest           # Eliminar alternativas
4. docker rmi squit-cli:test             # Eliminar imagen de tests
```

**⚠️ ADVERTENCIA:** Flag `-v` elimina volúmenes (se pierden datos generados).

**Archivos del host NO se tocan:**
- ✅ `.config/credentials.json` - Preservado
- ✅ `data/catalogo.csv` - Preservado
- ✅ `.env` - Preservado

**Solo se eliminan:**
- ❌ Container squit-cli
- ❌ Imagen squit-squit-cli:latest
- ❌ Volumen squit-persistent-data
- ❌ Red squit-network

**Cuándo usar:**
- ⚠️ Cuando hay problemas graves
- ⚠️ Antes de desinstalar
- ⚠️ Para empezar completamente de cero

**Después de `clean`, DEBES hacer `rebuild`:**
```bash
make squit-clean
make squit-rebuild
```

---

### `make squit-build` - Solo Construir

**Qué hace:**
```bash
docker compose --profile cli build --no-cache squit-cli
```

**Diferencia con `rebuild`:**
- Construye imagen
- **NO ejecuta** el CLI

**Cuándo usar:**
- Pre-construir imagen antes de distribuir
- Validar que build funciona
- CI/CD pipelines

---

## 📁 Volúmenes y Persistencia

### Tabla de Montajes

| Directorio Host | Directorio Container | Permisos | Propósito |
|-----------------|---------------------|----------|-----------|
| `.config/` | `/workspace/.config/` | `rw` | Service account JSON |
| `data/` | `/workspace/data/` | `rw` | Catálogo de 280 apps |
| `.env` | `/workspace/.env` | `ro` | Variables de entorno |
| `app/` | `/workspace/app/` | `ro` | Código fuente |
| `scripts/` | `/workspace/scripts/` | `ro` | Scripts CLI |
| `squit-data` (volume) | `/workspace/.squit/` | `rw` | Datos generados |

**Permisos:**
- `rw` = Read/Write (cambios persisten)
- `ro` = Read-Only (código protegido)

### ¿Qué se Preserva?

**Entre ejecuciones de `make squit`:**
- ✅ Credenciales (.config/credentials.json)
- ✅ Catálogo (data/catalogo.csv)
- ✅ Variables (.env)
- ✅ Historial de queries
- ✅ Cache del agente

**Al ejecutar `make squit-clean`:**
- ❌ Volumen squit-data se elimina
- ✅ Archivos del host se preservan

### Actualizar Configuración

**Cambiar credentials:**
```bash
# Editar en host
cp nuevo-proyecto.json .config/credentials.json

# NO necesitas rebuild
make squit  # Usa nuevo credentials automáticamente
```

**Cambiar catálogo:**
```bash
# Editar en host
cp nuevo-catalogo.csv data/catalogo.csv

# NO necesitas rebuild
make squit  # Usa nuevo catálogo automáticamente
```

**Cambiar código:**
```bash
# Editar archivos en app/ o scripts/
nano app/agentic_adk/agents/master_agent.py

# Código está montado como volumen (ro)
make squit  # Usa código actualizado automáticamente
```

**Cambiar dependencias:**
```bash
# Editar requirements.txt
nano requirements.txt

# SÍ necesitas rebuild
make squit-rebuild
```

---

## 🐛 Troubleshooting

### Error: "No module named 'deprecated'"

**Causa:** Imagen vieja con google-adk 0.5.0

**Solución:**
```bash
make squit-clean
make squit-rebuild
```

**Verificar fix:**
```bash
docker run --rm squit-squit-cli:latest python3 -c "
import deprecated
print(f'✅ deprecated: {deprecated.__version__}')
"
```

---

### Error: "No module named 'google.adk.apps'"

**Causa:** google-adk < 1.15.0

**Solución:**
```bash
# Verificar requirements.txt
grep "google-adk" requirements.txt
# Debe mostrar: google-adk>=1.15.0

# Si está correcto, rebuild
make squit-clean
make squit-rebuild
```

**Verificar fix:**
```bash
docker run --rm squit-squit-cli:latest python3 -c "
import google.adk
print(f'✅ google-adk: {google.adk.__version__}')
from google.adk.apps import App
print('✅ google.adk.apps importable')
"
```

---

### Prompt `squit[1]>` no aparece

**Síntoma:** Container inicia pero no muestra prompt.

**Causa:** Estaba usando `docker compose up` (no interactivo).

**Solución ya aplicada:** Makefile usa `docker compose run`.

**Si persiste:**
```bash
# Verificar que Makefile tiene 'run' no 'up'
grep "docker.*run.*squit-cli" Makefile

# Debe mostrar:
# docker compose --profile cli run --rm squit-cli
```

---

### Error: "network squit-network not found"

**Síntoma:**
```
failed to set up container networking: network squit-network not found
```

**Causa:** Estaba usando `docker run` en lugar de `docker compose run`.

**Solución ya aplicada:** Makefile usa `docker compose run` (crea red automáticamente).

**Si persiste:**
```bash
# Crear red manualmente
docker network create squit-network

# Luego ejecutar
make squit
```

---

### Error: "credentials.json was not found"

**Síntoma:**
```
DefaultCredentialsError: File .config/credentials.json was not found
```

**Causa:** Archivo no existe en host.

**Solución:**
```bash
# Verificar en host
ls -la .config/credentials.json

# Si no existe, copiar
cp ~/Downloads/tu-proyecto.json .config/credentials.json

# NO necesitas rebuild, solo reintentar
make squit
```

---

### Build muy lento

**Síntoma:** pip install toma >5 minutos

**Solución:**
```bash
# 1. Verificar conexión a internet
ping pypi.org

# 2. Limpiar cache de Docker
docker builder prune

# 3. Rebuild
make squit-rebuild
```

---

### Imagen no se actualiza

**Síntoma:** Cambios en requirements.txt no se reflejan.

**Causa:** Cache de Docker.

**Solución:**
```bash
# Forzar rebuild sin cache
make squit-clean
make squit-rebuild
```

---

## ✅ Checklist de Validación

Antes de ejecutar `make squit`, verifica:

- [ ] Docker Desktop está corriendo
- [ ] Existe `.env` en root del proyecto
- [ ] `.env` tiene `GOOGLE_CLOUD_PROJECT` configurado
- [ ] `.env` tiene `GEMINI_API_KEY` configurado
- [ ] Existe `.config/credentials.json`
- [ ] `credentials.json` tiene permisos 600
- [ ] (Opcional) Existe `data/catalogo.csv`
- [ ] Ejecutaste `make squit-rebuild` primera vez

**Comando de validación:**
```bash
python3 -c "
from pathlib import Path
import os

checks = [
    ('.env', Path('.env').exists()),
    ('.config/credentials.json', Path('.config/credentials.json').exists()),
    ('GOOGLE_CLOUD_PROJECT', bool(os.getenv('GOOGLE_CLOUD_PROJECT'))),
    ('GEMINI_API_KEY', bool(os.getenv('GEMINI_API_KEY')))
]

for name, status in checks:
    print(f'{'✅' if status else '❌'} {name}')
"
```

---

## 🔍 Verificar Imagen Construida

```bash
# Ver imágenes de SQUIT
docker images | grep squit

# Debe mostrar:
# squit-squit-cli  latest  ...  500MB  ...

# Verificar dependencias instaladas
docker run --rm squit-squit-cli:latest python3 -c "
import sys

deps = {
    'google.adk': None,
    'google.genai': None,
    'deprecated': None,
    'google.cloud.bigquery': 'BigQuery'
}

for module, alias in deps.items():
    try:
        mod = __import__(module)
        version = getattr(mod, '__version__', 'N/A')
        name = alias or module
        print(f'✅ {name}: {version}')
    except Exception as e:
        print(f'❌ {module}: {e}')
"
```

**Salida esperada:**
```
✅ google.adk: 1.15.1
✅ google.genai: 1.40.0
✅ deprecated: 1.2.18
✅ BigQuery: 3.38.0
```

---

## 🎓 Flujos de Trabajo

### Flujo 1: Instalación Fresh

```bash
# 1. Setup
cp .env.template .env
nano .env
cp ~/Downloads/proyecto.json .config/credentials.json

# 2. Build (primera vez)
make squit-rebuild

# 3. Usar
# Ya está corriendo, escribe tu query
squit[1]> que hace kayak?
squit[2]> exit
```

---

### Flujo 2: Uso Diario

```bash
# Día 1
make squit
squit[1]> mi query...
squit[2]> exit

# Día 2
make squit
squit[1]> otra query...
```

---

### Flujo 3: Actualización

```bash
# Pull cambios
git pull origin main

# Si cambió requirements.txt o Dockerfile.cli
make squit-rebuild

# Si solo cambió código (app/, scripts/)
make squit  # Usa código nuevo automáticamente
```

---

### Flujo 4: Solución de Problemas

```bash
# Algo no funciona

# Paso 1: Limpiar todo
make squit-clean

# Paso 2: Rebuild desde cero
make squit-rebuild

# Paso 3: Verificar
squit[1]> test query
```

---

## 📊 Diferencias Técnicas

### `docker compose up` vs `docker compose run`

| Aspecto | `up` | `run` |
|---------|------|-------|
| **Propósito** | Servicios daemon | Comandos interactivos |
| **Background** | Sí (default) | No (foreground) |
| **TTY** | Limitado | Completo |
| **Stdin** | No | Sí |
| **Auto-cleanup** | No | Sí (con --rm) |
| **Múltiples instancias** | Una por servicio | Múltiples posibles |
| **Logs** | Agregados | Directos |

**SQUIT usa `run`** porque:
- Necesita leer input del usuario
- Necesita TTY completo para prompt
- Necesita stdin para queries
- Debe limpiar al salir

### `--no-cache` en Build

**Con cache:**
```bash
docker compose build squit-cli

# Usa layers cacheados
# Rápido (~30 seg) pero puede usar deps viejas
```

**Sin cache:**
```bash
docker compose build --no-cache squit-cli

# Rebuild completo desde cero
# Lento (~1-2 min) pero garantiza deps frescas
```

**`make squit-rebuild` usa `--no-cache`** para garantizar versiones correctas.

---

## 🚀 Optimizaciones Aplicadas

### Multi-Stage Build

**Antes (Single-stage):**
```
Imagen final: ~800 MB
Incluye: gcc, g++, git, headers, etc.
Build time: 5-7 min
```

**Ahora (Multi-stage):**
```
Imagen final: ~500 MB
Incluye: Solo runtime libs
Build time: 1-2 min
```

**Ahorro:** 300 MB (37% más pequeña)

### Virtual Environment

Container usa `/opt/venv` para aislar dependencias:

```
/opt/venv/
├── bin/
│   └── python3 → Python con deps
├── lib/
│   └── python3.12/
│       └── site-packages/
│           ├── google/
│           ├── pandas/
│           └── ...
```

**Beneficio:** No contamina Python del sistema base.

### .dockerignore

Excluye archivos innecesarios del contexto de build:

```
Excluidos (~200 MB):
├─ .git/
├─ docs/
├─ tests/
├─ *.md
├─ __pycache__/
└─ .vscode/

Resultado:
- Contexto de build ~80% más pequeño
- Build ~40% más rápido
```

---

## 📚 Referencias

### Documentación

- **Esta guía (exhaustiva)**: `docs/usage/DOCKER.md` (800+ líneas)
- **Quick start**: `DOCKER_QUICKSTART.md` (2 min de lectura)
- **README principal**: `README.md` (sección Docker)
- **Índice docs**: `docs/INDEX.md`

### Archivos Técnicos

- **Dockerfile.cli**: Imagen multi-stage (72 líneas)
- **docker-compose.yml**: Servicio squit-cli (líneas 41-70)
- **Makefile**: Comandos automatizados (líneas 48-85)
- **.dockerignore**: Exclusiones de build (60 líneas)

### Docker Oficial

- **docker compose run**: https://docs.docker.com/compose/reference/run/
- **Multi-stage builds**: https://docs.docker.com/build/building/multi-stage/
- **Volumes**: https://docs.docker.com/storage/volumes/

---

## 💡 Tips Avanzados

### Ver Logs de Container

```bash
# En otra terminal mientras squit corre
docker logs -f squit-cli
```

### Inspeccionar Container

```bash
# Mientras squit corre, en otra terminal
docker exec -it squit-cli bash

# Dentro del container
ls -la /workspace
cat /workspace/.env
python3 -c "import google.adk; print(google.adk.__version__)"
exit
```

### Ver Volúmenes

```bash
# Listar volúmenes
docker volume ls | grep squit

# Inspeccionar volumen
docker volume inspect squit-persistent-data

# Ver contenido
docker run --rm -v squit-persistent-data:/data alpine ls -la /data
```

### Exportar Imagen

```bash
# Guardar imagen a archivo
docker save squit-squit-cli:latest | gzip > squit-cli.tar.gz

# Importar en otra máquina
docker load < squit-cli.tar.gz
```

---

## 🎯 Resumen de Comandos

### Uso Básico

```bash
make squit-rebuild  # Primera vez
make squit          # Uso normal
```

### Solución de Problemas

```bash
make squit-clean    # Limpiar todo
make squit-rebuild  # Reconstruir
```

### Información

```bash
make help                      # Comandos disponibles
docker images | grep squit     # Ver imágenes
docker ps -a | grep squit      # Ver containers
docker volume ls | grep squit  # Ver volúmenes
```

---

**Última actualización:** 2025-10-02  
**Autor:** Karim Touma | Grupo DeAcero  
**Versión:** 1.0.0  
**Sistema validado con:** Docker 24.x, Python 3.12, google-adk 1.15.1
