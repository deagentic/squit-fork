# 🚀 Quick Start con Docker

**SQUIT en un comando: `make squit`**

---

## ⚡ 3 Pasos Rápidos

### 1. Setup (Solo primera vez)

```bash
# 1. Configurar variables
cp .env.template .env
nano .env  # Agregar GOOGLE_CLOUD_PROJECT, GEMINI_API_KEY

# 2. Copiar credentials
cp ~/Downloads/tu-proyecto.json .config/credentials.json

# 3. Copiar catálogo (opcional)
cp tu-catalogo.csv data/catalogo.csv
```

### 2. Ejecutar

```bash
make squit
```

**Eso es todo.** El sistema:
- Construye imagen automáticamente (primera vez: ~2-3 min)
- Monta tu configuración (.config/, data/, .env)
- Inicia CLI interactivo
- Preserva todo entre ejecuciones

### 3. Usar

```
squit[1]> que hace kayak?
squit[2]> explicame AgAsignaFechasKayakProc
squit[3]> exit
```

---

## 📁 Archivos que se Preservan

✅ `.config/credentials.json` - Tu service account  
✅ `data/catalogo.csv` - 280 aplicaciones  
✅ `.env` - Variables de entorno  
✅ Datos generados - Volumen Docker persistente

**Nada se pierde entre ejecuciones.**

---

## 🎯 Comandos Útiles

```bash
# Ejecutar CLI
make squit

# Reconstruir imagen
make squit-rebuild

# Ver ayuda
make help

# Ver logs
docker logs squit-cli

# Detener
docker stop squit-cli
```

---

## ✅ Checklist Pre-ejecución

- [ ] Docker instalado y corriendo
- [ ] `.env` configurado
- [ ] `.config/credentials.json` copiado
- [ ] (Opcional) `data/catalogo.csv` copiado

---

## 🆘 Problemas Comunes

**"Docker daemon not running"**
```bash
# macOS: Abrir Docker Desktop
# Linux: sudo systemctl start docker
```

**"Permission denied"**
```bash
chmod 600 .config/credentials.json
```

**"Cannot find .env"**
```bash
cp .env.template .env
nano .env
```

---

## 📚 Más Información

- **Guía completa:** [docs/usage/DOCKER.md](docs/usage/DOCKER.md)
- **README:** [README.md](README.md)
- **Docs:** [docs/INDEX.md](docs/INDEX.md)

---

**¿Primera vez con Docker?** Ver: https://docs.docker.com/get-started/

**Creado por Karim Touma | Grupo DeAcero**
