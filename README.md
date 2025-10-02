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
git clone https://github.com/tu-usuario/squit.git
cd squit
```

### 2. Configurar Credenciales
```bash
# 1. Copiar template de configuración
cp .env.template .env

# 2. Obtener credenciales de Google Cloud
# Ver instrucciones detalladas en .config/README.md

# 3. Copiar credentials.json a .config/
cp ~/Downloads/tu-proyecto-xxxxx.json .config/credentials.json

# 4. Editar .env con tus valores
# Necesitas:
# - Google Cloud Project con BigQuery
# - Gemini API Key (https://makersuite.google.com/app/apikey)
# - Credentials ya están en .config/credentials.json
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar el Asistente
```bash
python3 scripts/squit.py
```

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

## 🔒 Seguridad y Privacidad

- ✅ **Credenciales**: Nunca se commitean (`.gitignore` robusto)
- ✅ **Service Accounts**: Permisos mínimos necesarios en GCP
- ✅ **API Keys**: Gestionadas via `.env` (no hardcodeadas)
- ✅ **Data Privacy**: Código SQL permanece en tu BigQuery
- ✅ **Gemini API**: Solo recibe queries del usuario, no todo el código

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
- **Issues**: [GitHub Issues](https://github.com/tu-usuario/squit/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tu-usuario/squit/discussions)

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

### 🔮 Fase 3 (Futuro)
- [ ] Vertex AI Memory Bank integration
- [ ] Multi-tenant support
- [ ] Web UI (Streamlit/Gradio)
- [ ] API REST para integraciones
- [ ] Support para más lenguajes (PL/SQL, T-SQL, etc.)

---

## 📊 Stats

![GitHub stars](https://img.shields.io/github/stars/tu-usuario/squit?style=social)
![GitHub forks](https://img.shields.io/github/forks/tu-usuario/squit?style=social)
![GitHub issues](https://img.shields.io/github/issues/tu-usuario/squit)
![GitHub pull requests](https://img.shields.io/github/issues-pr/tu-usuario/squit)

---

**Hecho con ❤️ para democratizar el conocimiento legacy**
