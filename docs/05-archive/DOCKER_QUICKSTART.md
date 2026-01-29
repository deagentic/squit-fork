# 🚀 Docker Quick Start - SQUIT

**Ejecuta SQUIT en 2 comandos con Docker.**

---

## ⚡ 3 Pasos Rápidos

### 1. Setup (Solo primera vez)

```bash
# a) Configurar variables
cp .env.template .env
nano .env  # Agregar: GOOGLE_CLOUD_PROJECT, GEMINI_API_KEY

# b) Copiar credentials
cp ~/Downloads/tu-proyecto.json .config/credentials.json

# c) Copiar catálogo (opcional - 280 apps)
cp tu-catalogo.csv data/catalogo.csv
```

---

### 2. Construir Imagen

```bash
make squit-rebuild
```

**Qué hace:**
- Construye imagen Docker con Python 3.12
- Instala google-adk 1.15.1 + todas las dependencias
- Configura volúmenes persistentes
- Tiempo: ~1-2 min primera vez

**Salida esperada:**
```
Reconstruyendo CLI de SQUIT (sin cache)...
[+] Building 77.7s (18/18) FINISHED
✔ squit-squit-cli Built

Iniciando CLI...
squit[1]> _  ← Cursor esperando tu input
```

---

### 3. Usar

```
squit[1]> que hace kayak?

"Kayak" es un sistema de gestión de fechas...
Los principales stored procedures son:
- AgAsignaFechasKayakProc
...

squit[2]> exit
```

**Salir:** Escribe `exit` o presiona `Ctrl+C`

---

## 📊 Siguientes Ejecuciones

```bash
# Simplemente ejecutar (usa imagen ya construida)
make squit

# Inicia inmediatamente (~1 seg)
squit[1]> _
```

---

## 🔧 Comandos Disponibles

| Comando | Cuándo Usar | Tiempo |
|---------|-------------|--------|
| `make squit` | Uso normal | <1 seg |
| `make squit-rebuild` | Primera vez o después de actualizar | 1-2 min |
| `make squit-clean` | Limpiar todo y empezar de cero | <5 seg |
| `make help` | Ver todos los comandos | - |

---

## 🐛 Problemas Comunes

### "Docker daemon not running"

```bash
# macOS: Abrir Docker Desktop
# Linux: sudo systemctl start docker
```

### "No module named 'deprecated'"

```bash
make squit-clean
make squit-rebuild
```

### Prompt `squit[1]>` no aparece

```bash
# Asegúrate de usar make squit-rebuild (no make squit-build)
make squit-rebuild
```

### "Cannot find .env"

```bash
cp .env.template .env
nano .env
```

---

## ✅ Checklist Pre-ejecución

- [ ] Docker Desktop instalado y corriendo
- [ ] `.env` configurado (GOOGLE_CLOUD_PROJECT, GEMINI_API_KEY)
- [ ] `.config/credentials.json` copiado
- [ ] (Opcional) `data/catalogo.csv` copiado
- [ ] Ejecutado `make squit-rebuild` (primera vez)

---

## 📁 Archivos que se Preservan

Entre ejecuciones, el sistema preserva:

✅ `.config/credentials.json` - Tu service account  
✅ `data/catalogo.csv` - 280 aplicaciones  
✅ `.env` - Variables de entorno  
✅ Historial de queries - En volumen `squit-data`

**Nada se pierde.** Tus configuraciones están seguras.

---

## 🎯 Comandos Esenciales

```bash
# Primera vez
make squit-rebuild

# Uso diario
make squit

# Si algo falla
make squit-clean
make squit-rebuild

# Ver ayuda
make help
```

---

## 📚 Más Información

- **Guía completa:** [docs/usage/DOCKER.md](docs/usage/DOCKER.md) (exhaustiva, 800+ líneas)
- **Instrucciones detalladas:** [INSTRUCCIONES_DOCKER.md](INSTRUCCIONES_DOCKER.md)
- **README principal:** [README.md](README.md)
- **Índice de docs:** [docs/INDEX.md](docs/INDEX.md)

---

## 💡 Por Qué `make squit` en Lugar de `python3 scripts/squit.py`

| Aspecto | Docker | Local |
|---------|--------|-------|
| Setup | Automático | Manual |
| Dependencias | Incluidas | Instalar manualmente |
| Aislamiento | Total | Contamina sistema |
| Portabilidad | 100% | Depende de OS |
| Limpieza | Fácil | Complicado |

**Docker = Simplicidad + Robustez + Reproducibilidad**

---

**Creado por:** Karim Touma | Grupo DeAcero  
**Última actualización:** 2025-10-02  
**Versión:** 1.0.0
