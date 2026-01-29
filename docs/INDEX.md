# 📚 SQUIT Documentation Index

> **"SQL Quit"** - Democratizando Código Legacy con IA

Bienvenido a la documentación completa de SQUIT. Esta página es tu punto de entrada para navegar toda la documentación del proyecto.

---

## 🚀 Quick Links

- **[Quick Start en 5 minutos](01-getting-started/QUICKSTART.md)** - Empezar a usar SQUIT rápidamente
- **[README Principal](../README.md)** - Overview del proyecto y características
- **[Docker Setup](01-getting-started/DOCKER_SETUP.md)** - Instalación con Docker (recomendado)
- **[CLI Guide](03-usage/CLI_GUIDE.md)** - Usar el asistente interactivo

---

## 📖 Documentación por Categoría

### 01. 🎯 Getting Started

Guías para empezar a usar SQUIT.

| Documento | Descripción |
|-----------|-------------|
| [QUICKSTART.md](01-getting-started/QUICKSTART.md) | Guía de inicio en 5 minutos |
| [DOCKER_SETUP.md](01-getting-started/DOCKER_SETUP.md) | Instalación y uso con Docker |

**¿Primer vez con SQUIT?** → Empieza con [QUICKSTART.md](01-getting-started/QUICKSTART.md)

---

### 02. 🏗️ Architecture

Documentación técnica de la arquitectura del sistema.

| Documento | Descripción |
|-----------|-------------|
| [SYSTEM_OVERVIEW.md](02-architecture/SYSTEM_OVERVIEW.md) | Overview general de la arquitectura |
| [BIGQUERY_VECTOR.md](02-architecture/BIGQUERY_VECTOR.md) | Sistema de vector search en BigQuery (PRIMARY) |
| [AGENTIC_SYSTEM.md](02-architecture/AGENTIC_SYSTEM.md) | Sistema agentic con Google ADK |

**Stack técnico:**
- **Backend**: Python 3.11+
- **Storage**: BigQuery (vector native)
- **IA**: Gemini 2.5 Flash + Gemini Embedding-001 (768 dims)
- **Frameworks**: Google ADK, LangChain

---

### 03. 💻 Usage

Guías de uso del sistema.

| Documento | Descripción |
|-----------|-------------|
| [CLI_GUIDE.md](03-usage/CLI_GUIDE.md) | Guía completa del CLI interactivo |
| [API_REFERENCE.md](03-usage/API_REFERENCE.md) | Referencia de APIs de Python |
| [EXAMPLES.md](03-usage/EXAMPLES.md) | Ejemplos de código y casos de uso |

**Casos de uso comunes:**
- Búsqueda semántica de código
- Análisis de dependencias
- Explicación de objetos SQL complejos
- Consultas en lenguaje natural

---

### 04. 🔧 Development

Guías para contribuir y desarrollar en SQUIT.

| Documento | Descripción |
|-----------|-------------|
| [CONTRIBUTING.md](04-development/CONTRIBUTING.md) | Guía para contribuir al proyecto |
| [TESTING.md](04-development/TESTING.md) | Guía completa de testing y coverage |
| [TECHNICAL.md](04-development/TECHNICAL.md) | Detalles técnicos de implementación |
| [CHANGELOG.md](04-development/CHANGELOG.md) | Historial de cambios |
| [ROADMAP.md](04-development/ROADMAP.md) | Roadmap y features futuras |

**Para desarrolladores:**
- Objetivo de coverage: ≥ 70%
- Testing con pytest y mocks
- CI/CD con GitHub Actions
- Code style: black, flake8, mypy

---

### 05. 🚀 Operations

Runbooks y procedimientos operacionales.

| Documento | Descripción |
|-----------|-------------|
| [DEPLOYMENT.md](operations/DEPLOYMENT.md) | Guía de despliegue a producción |
| [TROUBLESHOOTING.md](operations/TROUBLESHOOTING.md) | Solución de problemas comunes |
| [BACKUP_RESTORE.md](operations/BACKUP_RESTORE.md) | Procedimientos de backup y recovery |

**Para operaciones:**
- Health checks automatizados
- Métricas y monitoring
- Procedimientos de recovery
- Escalabilidad

---

### 06. 📦 Archive

Documentación histórica y legacy.

| Directorio | Descripción |
|------------|-------------|
| [05-archive/](05-archive/) | Documentos antiguos y legacy preservados |

**Nota**: Esta carpeta contiene documentos históricos que pueden ser útiles para referencia, pero no son la documentación oficial actual.

---

## 🎯 Documentación por Rol

### Para Usuarios Finales
1. [QUICKSTART.md](01-getting-started/QUICKSTART.md) - Empezar en 5 minutos
2. [CLI_GUIDE.md](03-usage/CLI_GUIDE.md) - Usar el asistente interactivo
3. [EXAMPLES.md](03-usage/EXAMPLES.md) - Ver ejemplos de uso

### Para Desarrolladores
1. [CONTRIBUTING.md](04-development/CONTRIBUTING.md) - Cómo contribuir
2. [TESTING.md](04-development/TESTING.md) - Escribir tests
3. [API_REFERENCE.md](03-usage/API_REFERENCE.md) - APIs de Python
4. [TECHNICAL.md](04-development/TECHNICAL.md) - Detalles técnicos

### Para DevOps
1. [DOCKER_SETUP.md](01-getting-started/DOCKER_SETUP.md) - Docker deployment
2. [DEPLOYMENT.md](operations/DEPLOYMENT.md) - Despliegue a producción
3. [TROUBLESHOOTING.md](operations/TROUBLESHOOTING.md) - Resolver problemas
4. [BACKUP_RESTORE.md](operations/BACKUP_RESTORE.md) - Backup y recovery

### Para Arquitectos
1. [SYSTEM_OVERVIEW.md](02-architecture/SYSTEM_OVERVIEW.md) - Arquitectura general
2. [BIGQUERY_VECTOR.md](02-architecture/BIGQUERY_VECTOR.md) - Sistema vectorial
3. [AGENTIC_SYSTEM.md](02-architecture/AGENTIC_SYSTEM.md) - Sistema agentic

---

## 📊 Quick Stats

- **SQL Objects**: 3.4M+ objetos en 275 servidores
- **Vector Database**: BigQuery native (PRIMARY) + Weaviate (opcional)
- **Embedding Model**: Gemini Embedding-001 (768 dimensions)
- **LLM**: Gemini 2.5 Flash
- **Search**: Búsqueda híbrida 70% vector + 30% keywords
- **Memory**: Multi-turn conversacional con LangChain

---

## 🔗 Enlaces Externos

- **GitHub**: [grupodeacero/squit](https://github.com/grupodeacero/squit)
- **BigQuery ML Docs**: [Google Cloud BigQuery ML](https://cloud.google.com/bigquery/docs/bqml-introduction)
- **Gemini API**: [Google AI Gemini](https://ai.google.dev/)
- **Google ADK**: [Agent Development Kit](https://google.github.io/adk-docs/)

---

## 📝 Convenciones de Documentación

- **Formato**: Markdown (.md)
- **Estilo**: GitHub Flavored Markdown
- **Lenguaje**: Español (con términos técnicos en inglés cuando aplique)
- **Estructura**: Títulos jerárquicos con H1-H6
- **Code blocks**: Con syntax highlighting

---

## 🆘 ¿Necesitas Ayuda?

1. **Busca en esta documentación** usando Ctrl+F o ⌘+F
2. **Revisa [TROUBLESHOOTING.md](operations/TROUBLESHOOTING.md)** para problemas comunes
3. **Consulta [EXAMPLES.md](03-usage/EXAMPLES.md)** para ver ejemplos prácticos
4. **Abre un Issue** en GitHub si encuentras algún problema
5. **Contacta al equipo** en ktouma@deacero.com

---

## 🔄 Actualización de Documentación

**Última revisión**: 2025-01-14  
**Versión del sistema**: 2.0.0  
**Mantenedor**: Karim Touma (@ktouma)

---

**¿Listo para empezar?** → [QUICKSTART.md](01-getting-started/QUICKSTART.md)
