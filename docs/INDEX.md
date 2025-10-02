# 📚 Índice de Documentación - SQUIT

Documentación completa del proyecto SQUIT organizada por categorías.

---

## 🚀 Inicio Rápido

**Nuevo en SQUIT?** Empieza aquí:
1. Lee el [README principal](../README.md)
2. Sigue la [Guía de Setup](setup/BIGQUERY_VECTOR_COMPLETE.md)
3. Ejecuta `python3 scripts/squit.py`

---

## 📁 Organización

```
docs/
├── setup/          → Pipeline de datos y configuración inicial
├── usage/          → Cómo usar SQUIT
├── development/    → Arquitectura y desarrollo avanzado
└── archive/        → Documentación histórica/obsoleta
```

---

## 📊 1. SETUP - Pipeline y Configuración

### Pipeline de Datos
- **[BigQuery Vector Complete](setup/BIGQUERY_VECTOR_COMPLETE.md)** ⭐ **PRINCIPAL**
  - Pipeline completo de chunks + embeddings + índice vectorial
  - Guía paso a paso desde extracción hasta búsqueda
  - ~30min chunking, ~2-4h embeddings, ~10min índice

- **[Extraction Guide](setup/EXTRACTION_GUIDE.md)**
  - Cómo extraer código SQL desde SQL Server
  - Script SQL para obtener objetos de todas las DBs
  - Carga a BigQuery

### Configuración
- **[Weaviate Setup](setup/WEAVIATE_SETUP.md)**
  - Setup de Weaviate (opcional, para Fase 2)
  - Docker compose configuration

- **[Models Standard](setup/MODELS_STANDARD.md)**
  - Configuración de modelos IA
  - Gemini 2.5 Flash para agentes
  - Embedding-001 para vectores

---

## 🎯 2. USAGE - Uso de la Aplicación

### Guía Principal
- **[Agentic ADK Guide](usage/AGENTIC_ADK_GUIDE.md)** ⭐ **PRINCIPAL**
  - Cómo usar `python3 scripts/squit.py`
  - Conversaciones multi-turn con memoria
  - Ejemplos de queries y comandos

### Referencias
- **[API Reference](usage/API.md)**
  - APIs de BigQueryVectorSearch
  - MasterAgent methods
  - QueryLogger methods

- **[Examples](usage/EXAMPLES.md)**
  - Ejemplos de código
  - Casos de uso comunes
  - Snippets reutilizables

---

## 💻 3. DEVELOPMENT - Arquitectura y Avanzado

### Arquitectura del Sistema
- **[System Overview](development/SYSTEM_OVERVIEW.md)**
  - Visión general del sistema
  - Componentes principales
  - Flujo de datos

- **[Technical Deep Dive](development/TECHNICAL.md)**
  - Detalles técnicos de implementación
  - Algoritmos y optimizaciones
  - Performance tuning

### Mejoras de Memoria (Fase 1)
- **[Phase 1 Implementation](development/PHASE1_IMPLEMENTATION.md)** ⭐ **NUEVO**
  - Context Caching (latencia -50%)
  - LangChain BufferMemory
  - QueryLogger BigQuery
  - Few-shots automáticos

- **[Memory Optimization](development/MEMORY_OPTIMIZATION.md)**
  - Sistema de memoria multi-turn
  - Context awareness
  - Session management

- **[Memory Research](development/MEMORY_RESEARCH.md)**
  - Investigación de soluciones de memoria
  - Comparación de librerías
  - Vertex AI Memory Bank vs LangChain vs MemGPT

- **[Memory Action Plan](development/MEMORY_ACTION_PLAN.md)**
  - Plan de implementación Fase 2
  - Weaviate Semantic Memory
  - Roadmap futuro

- **[Context Awareness Fix](development/CONTEXT_AWARENESS_FIX.md)**
  - Fix de interpretación contextual
  - System prompt mejorado
  - Test cases

### Summaries
- **[Optimization Summary](development/OPTIMIZATION_SUMMARY.md)**
  - Resumen de mejoras implementadas
  - Métricas de impacto

- **[Phase 1 Executive Summary](development/PHASE1_SUMMARY_EXECUTIVE.md)**
  - Resumen ejecutivo para stakeholders
  - KPIs y resultados

- **[Quickstart Memory](development/QUICKSTART_MEMORY.md)**
  - Guía rápida de memoria multi-turn
  - Comandos y ejemplos

- **[Changelog Memory](development/CHANGELOG_MEMORY.md)**
  - Historial de cambios en sistema de memoria
  - v2.0.1 → v2.1.0

---

## 🗄️ 4. ARCHIVE - Documentación Histórica

Documentación obsoleta o superada por versiones más recientes:

- `archive/AGENTIC_RAG.md` - Sistema RAG original (pre-ADK)
- `archive/AGENTIC_SYSTEM_PLAN.md` - Plan original del sistema
- `archive/MIGRATION_GUIDE.md` - Migración Weaviate→BigQuery
- `archive/PHASE1_SUMMARY.md` - Resumen antiguo de Fase 1
- `archive/TODO.md` - TODOs históricos
- `archive/ESTADO_ACTUAL_SISTEMA.md` - Estado del sistema (snapshot antiguo)
- `archive/BIGQUERY_VECTOR_SYSTEM.md` - Docs antiguas de BigQuery
- `archive/DEMOCRATIZATION_MANIFESTO.md` - Manifiesto del proyecto
- `archive/context.md` - Contexto histórico
- `archive/info.md` - Info misc

**Nota**: Estos docs se mantienen por referencia histórica pero pueden estar desactualizados.

---

## 📖 Guías por Tarea

### "Quiero configurar SQUIT por primera vez"
1. [README.md](../README.md) - Overview
2. [setup/BIGQUERY_VECTOR_COMPLETE.md](setup/BIGQUERY_VECTOR_COMPLETE.md) - Pipeline completo
3. [setup/EXTRACTION_GUIDE.md](setup/EXTRACTION_GUIDE.md) - Extraer código SQL
4. Configure `.env` con tus credenciales

### "Quiero usar el asistente conversacional"
1. [usage/AGENTIC_ADK_GUIDE.md](usage/AGENTIC_ADK_GUIDE.md) - Guía principal
2. `python3 scripts/squit.py`
3. [usage/EXAMPLES.md](usage/EXAMPLES.md) - Ejemplos

### "Quiero entender la arquitectura"
1. [development/SYSTEM_OVERVIEW.md](development/SYSTEM_OVERVIEW.md) - Overview
2. [development/TECHNICAL.md](development/TECHNICAL.md) - Detalles técnicos
3. [development/PHASE1_IMPLEMENTATION.md](development/PHASE1_IMPLEMENTATION.md) - Mejoras Fase 1

### "Quiero contribuir al proyecto"
1. [CONTRIBUTING.md](../CONTRIBUTING.md) - Guía de contribución
2. [development/MEMORY_ACTION_PLAN.md](development/MEMORY_ACTION_PLAN.md) - Roadmap
3. Revisa issues en GitHub

---

## 🔗 Enlaces Externos

- **Gemini API**: https://ai.google.dev/gemini-api/docs
- **BigQuery ML**: https://cloud.google.com/bigquery/docs/generate-text-embedding
- **Google ADK**: https://google.github.io/adk-docs/
- **LangChain**: https://python.langchain.com/docs/

---

## 📝 Convenciones

- ⭐ = Documentación principal/recomendada
- 🆕 = Documentación nueva/reciente
- 📊 = Contiene métricas/datos
- 🔧 = Guía técnica hands-on
- 📖 = Referencia teórica

---

**Última actualización**: 2025-10-01  
**Versión**: 2.1.0
