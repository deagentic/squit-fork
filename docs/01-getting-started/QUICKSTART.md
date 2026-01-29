# 🚀 SQUIT Quick Start - 5 Minutos

Gu

ía rápida para empezar a usar SQUIT en menos de 5 minutos.

---

## ⚡ Setup Rápido

### 1. Clonar el Repositorio (30 segundos)

```bash
git clone https://github.com/grupodeacero/squit.git
cd squit
```

### 2. Configurar Credenciales (2 minutos)

```bash
# Copiar template de configuración
cp .env.template .env

# Editar con tus credenciales
nano .env
```

**Variables mínimas requeridas:**
```bash
GOOGLE_CLOUD_PROJECT=tu-proyecto-id
GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json
GEMINI_API_KEY=tu-gemini-api-key
GEMINI_CHAT_MODEL=gemini-2.5-flash
```

**Obtener credenciales:**
- **Service Account**: [Google Cloud Console](https://console.cloud.google.com/) → IAM & Admin → Service Accounts
- **Gemini API Key**: [Google AI Studio](https://makersuite.google.com/app/apikey)

### 3. Instalar y Ejecutar (2 minutos)

#### Opción A: Docker (Recomendado)

```bash
# Primera vez
make squit-rebuild

# Siguientes veces
make squit
```

#### Opción B: Python Direct

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar CLI
python3 scripts/squit.py
```

---

## 💬 Usar SQUIT

```
    ███████╗ ██████╗ ██╗   ██╗██╗████████╗
    ██╔════╝██╔═══██╗██║   ██║██║╚══██╔══╝
    ███████╗██║   ██║██║   ██║██║   ██║   
    ╚════██║██║▄▄ ██║██║   ██║██║   ██║   
    ███████║╚██████╔╝╚██████╔╝██║   ██║   
    ╚══════╝ ╚══▀▀═╝  ╚═════╝ ╚═╝   ╚═╝   
    
  "SQL Quit" - Democratizando Código Legacy
  Búsqueda Inteligente | 2.9M Objetos SQL

squit[1]> hablame de kayak

"Kayak" es un sistema de gestión de fechas de embarque...

squit[2]> explicame el primero que mencionaste

✅ Memoria mantiene contexto

squit[3]> exit
```

---

## 📖 Ejemplos Comunes

### Buscar por Funcionalidad
```
¿Dónde está la lógica de inventario?
Busca procedimientos de ventas y facturación
Código que calcule precios o costos
```

### Analizar Objetos
```
Explicame AgAsignaFechasKayakProc
¿Qué hace CVtaVentasSel?
Analiza el procedure de autenticación
```

### Análisis de Impacto
```
Si modifico la tabla VentasPedidos, qué se rompe
Dependencias de AgAsignaFechasKayakProc
Qué procedures usan la tabla Clientes
```

---

## 🔧 Comandos Útiles

```bash
# CLI interactivo
make squit

# Reconstruir imagen
make squit-rebuild

# Limpiar sistema
make squit-clean

# Ver logs
make logs

# Health check
make health
```

---

## 📚 Próximos Pasos

1. **Explora la documentación**: [docs/INDEX.md](../INDEX.md)
2. **Lee la guía del CLI**: [CLI_GUIDE.md](../03-usage/CLI_GUIDE.md)
3. **Revisa ejemplos**: [EXAMPLES.md](../03-usage/EXAMPLES.md)
4. **Arquitectura**: [SYSTEM_OVERVIEW.md](../02-architecture/SYSTEM_OVERVIEW.md)

---

## ⚠️ Troubleshooting

### Error: "Faltan variables de ambiente"
```bash
# Verifica que .env tenga todas las variables
cat .env

# Verifica credenciales
ls -la .config/credentials.json
```

### Error: "Gemini API no responde"
```bash
# Verifica API key
echo $GEMINI_API_KEY

# Prueba llamada manual
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=$GEMINI_API_KEY"
```

### Error: "BigQuery connection failed"
```bash
# Verifica proyecto
gcloud config get-value project

# Verifica permisos
python3 scripts/prod/verify_bigquery_access.py
```

---

## 🆘 ¿Necesitas Ayuda?

- **Documentación**: [docs/INDEX.md](../INDEX.md)
- **Troubleshooting**: [operations/TROUBLESHOOTING.md](../operations/TROUBLESHOOTING.md)
- **Issues**: [GitHub Issues](https://github.com/grupodeacero/squit/issues)
- **Email**: ktouma@deacero.com

---

**¡Listo!** Ahora puedes democratizar tu código SQL legacy con IA 🎉

