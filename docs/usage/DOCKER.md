# 🐳 Uso de SQUIT con Docker

Guía completa para ejecutar SQUIT en contenedores Docker con configuración persistente.

**Última actualización:** 2025-10-02

---

## 🎯 Ventajas de Docker

✅ **Aislamiento completo** - No contamina el sistema host  
✅ **Dependencias incluidas** - Python, librerías, todo pre-instalado  
✅ **Configuración persistente** - Archivos montados, no se pierden  
✅ **Reproducible** - Mismo ambiente en cualquier máquina  
✅ **Fácil de usar** - Un comando: `make squit`

---

## 🚀 Quick Start

### 1. Pre-requisitos

```bash
# Instalar Docker
# macOS: https://docs.docker.com/desktop/install/mac-install/
# Linux: https://docs.docker.com/engine/install/
# Windows: https://docs.docker.com/desktop/install/windows-install/

# Verificar instalación
docker --version
docker-compose --version
```

### 2. Primera Ejecución

```bash
# Clonar repositorio (si no lo has hecho)
git clone https://github.com/grupodeacero/squit.git
cd squit

# Configurar credenciales (IMPORTANTE)
cp .env.template .env
nano .env  # Editar con tus valores

# Copiar credentials de Google Cloud
cp ~/Downloads/tu-proyecto.json .config/credentials.json

# Copiar catálogo (opcional)
cp tu-catalogo.csv data/catalogo.csv

# Ejecutar SQUIT en Docker
make squit
```

**¡Eso es todo!** El sistema:
- Construirá la imagen Docker (primera vez, ~2-3 min)
- Montará tus archivos de configuración
- Iniciará el CLI interactivo
- Preservará todo entre ejecuciones

---

## 📁 Persistencia de Datos

### Volúmenes Montados

El comando `make squit` monta estos directorios:

```
Host → Container

.config/          → /workspace/.config/          (rw)
data/             → /workspace/data/             (rw)
.env              → /workspace/.env              (ro)
app/              → /workspace/app/              (ro)
scripts/          → /workspace/scripts/          (ro)

squit-data volume → /workspace/.squit/          (rw)
```

**Permisos:**
- `rw` = lectura/escritura (datos se guardan)
- `ro` = solo lectura (código protegido)

### Archivos Preservados

✅ **Credenciales**: `.config/credentials.json`  
✅ **Catálogo**: `data/catalogo.csv`  
✅ **Configuración**: `.env`  
✅ **Datos generados**: Volumen `squit-data`

**Todos tus archivos persisten entre ejecuciones.**

---

## 🛠️ Comandos Disponibles

### Comando Principal

```bash
# Ejecutar CLI interactivo
make squit
```

### Construcción

```bash
# Construir imagen (solo si cambió Dockerfile.cli)
make squit-build

# Reconstruir y ejecutar
make squit-rebuild
```

### Gestión

```bash
# Ver contenedores activos
docker ps

# Ver logs
docker logs squit-cli

# Detener contenedor
docker stop squit-cli

# Eliminar contenedor
docker rm squit-cli

# Ver volúmenes
docker volume ls
```

### Limpieza

```bash
# Eliminar contenedores detenidos
docker container prune

# Eliminar imágenes sin usar
docker image prune

# Limpieza completa (¡CUIDADO! Elimina todo Docker)
docker system prune -a
```

---

## ⚙️ Configuración Avanzada

### Variables de Entorno

El archivo `.env` se monta automáticamente. Variables importantes:

```bash
# En tu .env local
GOOGLE_CLOUD_PROJECT=tu-proyecto-id
GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json  # Ruta relativa
GEMINI_API_KEY=tu-api-key
GEMINI_CHAT_MODEL=gemini-2.5-flash
```

**Dentro del container** estas variables se cargan automáticamente.

### Recursos del Container

Por defecto, el CLI no tiene límites de recursos. Para añadirlos:

```yaml
# En docker-compose.yml, añadir a squit-cli:
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
    reservations:
      memory: 512M
      cpus: '0.5'
```

### Networking

El CLI corre en la red `squit-network` para comunicarse con otros servicios si es necesario.

---

## 🔍 Troubleshooting

### Error: "Cannot connect to Docker daemon"

**Problema:** Docker no está corriendo

**Solución:**
```bash
# macOS: Abrir Docker Desktop
# Linux: Iniciar servicio
sudo systemctl start docker
```

### Error: "Permission denied" en .config/

**Problema:** Permisos incorrectos

**Solución:**
```bash
chmod 600 .config/credentials.json
chmod 755 .config
```

### Error: "No such file or directory: .env"

**Problema:** Falta archivo .env

**Solución:**
```bash
cp .env.template .env
nano .env  # Configurar
```

### Error: "Image build failed"

**Problema:** Error en construcción

**Solución:**
```bash
# Ver logs detallados
make squit-build 2>&1 | tee build.log

# Limpiar cache y reconstruir
docker builder prune
make squit-rebuild
```

### El catálogo no se encuentra

**Problema:** Archivo no montado correctamente

**Solución:**
```bash
# Verificar que existe
ls -la data/catalogo.csv

# Verificar montaje en container
docker exec squit-cli ls -la /workspace/data/

# Si no aparece, revisar docker-compose.yml
```

### Memoria insuficiente

**Problema:** Container se queda sin memoria

**Solución:**
```bash
# En Docker Desktop: Settings → Resources → Memory
# Incrementar a 4GB o más

# O editar docker-compose.yml para limitar memoria
```

---

## 📊 Comparación: Docker vs Local

| Aspecto | Docker (`make squit`) | Local (`python3 scripts/squit.py`) |
|---------|----------------------|-------------------------------------|
| **Setup inicial** | ~5 min (build) | ~10 min (deps) |
| **Dependencias** | ✅ Auto-instaladas | ⚠️  Manual |
| **Aislamiento** | ✅ Total | ❌ Contamina sistema |
| **Portabilidad** | ✅ Funciona igual everywhere | ⚠️  Depende de Python local |
| **Performance** | ⚠️  Overhead mínimo (~5%) | ✅ Nativa |
| **Persistencia** | ✅ Volúmenes Docker | ✅ Directo en FS |
| **Limpieza** | ✅ `docker rm` y listo | ⚠️  Desinstalar deps |

**Recomendación:** Usa Docker para producción y entornos limpios. Usa local para desarrollo rápido.

---

## 🎓 Ejemplos Prácticos

### Ejemplo 1: Primera vez

```bash
# Setup inicial
cd squit
cp .env.template .env
nano .env  # Configurar

# Copiar credentials
cp ~/Downloads/mi-proyecto.json .config/credentials.json

# Ejecutar
make squit
```

### Ejemplo 2: Uso diario

```bash
# Simplemente ejecutar
make squit

# Salir: Ctrl+C o escribir 'exit'
```

### Ejemplo 3: Actualizar código

```bash
# Pull cambios
git pull origin main

# Reconstruir si es necesario
make squit-rebuild
```

### Ejemplo 4: Múltiples proyectos

```bash
# Proyecto 1
cd ~/projects/squit-produccion
make squit

# Proyecto 2 (en otra terminal)
cd ~/projects/squit-desarrollo
make squit

# Cada uno usa su propia configuración
```

---

## 🔐 Seguridad

### Protección de Credenciales

✅ **Montaje read-only** para código  
✅ **Permisos 600** en credentials.json  
✅ **NO se copian** al container (solo mount)  
✅ **.gitignore** protege archivos sensibles  

### Red Aislada

El CLI corre en red privada `squit-network`. No expone puertos públicos.

### Limpieza Automática

Al detener el container, se elimina automáticamente (no queda basura).

---

## 📚 Referencias

- **Dockerfile.cli**: [Dockerfile.cli](../../Dockerfile.cli) - Imagen del CLI
- **docker-compose.yml**: [docker-compose.yml](../../docker-compose.yml) - Orquestación
- **Makefile**: [Makefile](../../Makefile) - Comandos automatizados
- **Docker Docs**: https://docs.docker.com/

---

## 🆘 Soporte

**Issues:** [GitHub Issues](https://github.com/grupodeacero/squit/issues)  
**Docs:** [docs/INDEX.md](../INDEX.md)  
**Email:** ktouma@deacero.com

---

**Última actualización:** 2025-10-02  
**Mantenido por:** Grupo DeAcero

