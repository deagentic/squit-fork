# Guía del Sistema Agentic ADK
## Democratizando Código Legacy con Agentes IA

---

## 🎯 ¿Qué es el Sistema Agentic ADK?

Un sistema de **agentes inteligentes** construido con **Google Agent Development Kit (ADK)** que permite a **cualquier persona** en la organización entender y trabajar con código SQL legacy mediante **lenguaje natural**.

**"SQL Quit"** en acción: Conversa con el código, no lo leas.

### Problema que Resuelve

**Antes:**
- ❌ Buscar manualmente en 3.4M objetos SQL
- ❌ Leer miles de líneas para entender qué hace
- ❌ Adivinar qué se rompe si cambias algo
- ❌ Depender de desarrolladores expertos

**Después (con Agentes):**
- ✅ Preguntar en lenguaje natural: "¿dónde está X?"
- ✅ Obtener explicación simple de código complejo
- ✅ Ver análisis de impacto automático
- ✅ Democratizado para todos

---

## 🚀 Quick Start

### 1. Instalación

```bash
# Instalar dependencias
pip install google-adk google-cloud-bigquery

# Verificar instalación
python scripts/demo_agentic_adk.py --validate
```

### 2. Configuración

```bash
# 1. Copiar template si no existe
cp .env.template .env

# 2. Configurar variables de entorno mínimas
nano .env

# Agregar/verificar:
GOOGLE_CLOUD_PROJECT=tu-proyecto-id
GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json  # ← Ruta correcta
GEMINI_API_KEY=tu-gemini-api-key
GEMINI_CHAT_MODEL=gemini-2.5-flash  # ← Modelo recomendado

# 3. Copiar credentials de Google Cloud
cp ~/Downloads/tu-proyecto-xxxxx.json .config/credentials.json

# 4. Copiar catálogo de aplicaciones (opcional pero recomendado)
# El sistema usa data/catalogo.csv para enriquecer búsquedas
cp tu-catalogo.csv data/catalogo.csv
# (280+ aplicaciones de negocio)
```

### 3. Demo Interactiva

```bash
python scripts/demo_agentic_adk.py
```

### 4. Demo Automática

```bash
python scripts/demo_agentic_adk.py --demo
```

---

## 🤖 Componentes del Sistema

### MasterAgent (Orquestador)

El cerebro del sistema que entiende intención y coordina agentes especializados.

```python
from agentic_adk import MasterAgent

agent = MasterAgent()

# Pregunta en lenguaje natural
response = agent.process("¿Dónde está la lógica de cálculo de comisiones?")
print(response)
```

### Tools Disponibles

#### 1. vector_search_tool
Busca código por intención semántica.

```python
# El agente usa esto cuando preguntas "dónde está" o "código que hace"
query = "autenticación usuarios permisos"
# → Encuentra código relevante aunque use términos diferentes
```

#### 2. get_object_summary_tool
Obtiene resumen ejecutivo de un objeto.

```python
# El agente usa esto cuando preguntas "qué hace X" o "explícame X"
object_name = "sp_ProcesarVentas"
# → Retorna: dominio, complejidad, resumen, dependencias
```

#### 3. get_object_chunks_tool
Lee código completo de un objeto.

```python
# El agente usa esto cuando necesita ver código detallado
parent_object_id = "SERVER|DB|schema|sp_Procedure"
# → Retorna todos los chunks ordenados
```

#### 4. find_dependencies_tool
Encuentra dependencias de un objeto.

```python
# El agente usa esto cuando preguntas "qué usa X" o "dependencias"
object_name = "ClientesMaster"
# → Retorna qué procedimientos/vistas lo usan
```

#### 5. analyze_impact_tool
Analiza impacto de modificar un objeto.

```python
# El agente usa esto cuando preguntas "puedo cambiar X" o "qué se rompe"
object_name = "ClientesMaster"
# → Retorna reporte de riesgo con objetos críticos
```

---

## 💬 Ejemplos de Conversaciones

### Ejemplo 1: Búsqueda de Lógica

**Usuario:** "¿Dónde están los procedimientos que calculan nómina?"

**SQUIT:**
```
Encontré 12 procedimientos relacionados con nómina:

🏢 Principales (Alta Complejidad):
1. sp_CalcularNominaMensual (Complejidad: 8.7/10)
   Dominio: Recursos Humanos
   Resumen: Calcula nómina mensual con deducciones, bonos e impuestos

2. sp_ProcesarDeduccionesNomina (Complejidad: 7.2/10)
   Resumen: Procesa deducciones de IMSS, ISR y préstamos

3. fn_CalcularISRMensual (Complejidad: 6.8/10)
   Resumen: Función que calcula ISR según tablas fiscales

¿Quieres que te explique alguno en detalle?
```

### Ejemplo 2: Análisis de Impacto

**Usuario:** "Quiero agregar una columna a la tabla Productos, ¿qué impacta?"

**SQUIT:**
```
⚠️ ANÁLISIS DE IMPACTO: Productos

Total objetos afectados: 45

🔴 CRÍTICOS (5):
- sp_ActualizarInventarioMaster: ESCRIBE en Productos (diario)
- vw_ReporteVentasConsolidado: LEE Productos (dashboard ejecutivo)
- sp_ImportarProductosCSV: ESCRIBE en Productos (semanal)
- sp_CalcularCostoVentas: LEE Productos (proceso crítico)
- vw_ProductosActivos: LEE Productos (40+ reportes dependen)

🟡 RIESGO MEDIO (12):
- sp_BuscarProductoPorCodigo: LEE
- fn_ObtenerPrecioProducto: LEE
- ...

🟢 BAJO RIESGO (28):
- Reportes analíticos varios

RECOMENDACIÓN:
⚠️ ALTO RIESGO - Modificar Productos impacta sistemas críticos.

Siguiente paso:
1. Revisar sp_ActualizarInventarioMaster (¿espera la columna?)
2. Probar en ambiente de desarrollo primero
3. Considerar migración gradual
```

### Ejemplo 3: Explicación de Código

**Usuario:** "¿Qué hace el procedimiento sp_ProcesarVentas?"

**SQUIT:**
```
📋 sp_ProcesarVentas

Dominio: Ventas
Complejidad: Alta (7.5/10)
Líneas: 450
Ubicación: SRVPROD\VENTAS.ProduccionDB.dbo

RESUMEN EJECUTIVO:
Procedimiento principal para procesar ventas diarias, validando datos,
aplicando descuentos y actualizando inventario.

LÓGICA PRINCIPAL:
1. Valida datos de entrada (cliente, productos, cantidades)
2. Verifica disponibilidad en inventario
3. Calcula precios aplicando descuentos por volumen
4. Registra la venta en tablas transaccionales
5. Actualiza stock de inventario
6. Genera facturas electrónicas
7. Calcula comisiones de vendedores

TABLAS USADAS:
- Ventas (escribe)
- DetalleVentas (escribe)
- Inventario (lee y escribe)
- Clientes (lee)
- Productos (lee)
- Comisiones (escribe)

COMPLEJIDAD:
- 8 validaciones de negocio
- 3 transacciones anidadas
- Manejo de errores robusto

¿Quieres que te muestre el código detallado de alguna sección específica?
```

---

## 🏗️ Arquitectura

```
Usuario
  ↓
  Lenguaje Natural
  ↓
MasterAgent (Gemini 2.5 Flash)
  ↓
  Decide qué tool usar
  ↓
┌─────────────┬──────────────┬─────────────┬──────────────┐
│  vector     │  get_object  │  get_object │  find_deps   │
│  _search    │  _summary    │  _chunks    │  _tool       │
└──────┬──────┴──────┬───────┴──────┬──────┴──────┬───────┘
       │             │              │             │
       ▼             ▼              ▼             ▼
    BigQuery      BigQuery       BigQuery     BigQuery
    VECTOR_SEARCH  Query          Query        Query
       │             │              │             │
       └─────────────┴──────────────┴─────────────┘
                     │
                     ▼
              chunk_embeddings
          (768-dim vectors + metadata)
```

---

## 🔧 Uso Programático

### Búsqueda Simple

```python
from agentic_adk import MasterAgent

agent = MasterAgent()

# Búsqueda por intención
response = agent.process("procedimientos de facturación")
print(response)
```

### Análisis de Impacto

```python
# Pregunta sobre modificación
response = agent.process(
    "Quiero agregar una columna a la tabla Ventas, ¿qué se puede romper?"
)
print(response)
```

### Explicación de Código

```python
# Pedir explicación
response = agent.process(
    "Explícame línea por línea qué hace sp_CalcularComisiones"
)
print(response)
```

### Modo Interactivo

```python
agent = MasterAgent()
agent.interactive()  # Inicia conversación interactiva
```

---

## 📊 Casos de Uso Reales

### Para Desarrolladores Nuevos

**Pregunta:** "No entiendo el módulo de inventario, ¿qué componentes tiene?"

**SQUIT identifica:**
- 23 procedimientos de inventario
- 5 componentes principales (entradas, salidas, ajustes, reportes, sincronización)
- Flujo de datos entre componentes
- Procedimientos por orden de complejidad

**Resultado:** Mapa conceptual del módulo en minutos vs días de lectura

### Para Arquitectos

**Pregunta:** "¿Puedo deprecar sp_ActualizacionLegacy sin romper nada?"

**SQUIT analiza:**
- 3 procedimientos llaman a sp_ActualizacionLegacy
- 2 son críticos (producción diaria)
- 1 es legacy (no usado desde hace meses)

**Resultado:** Decisión informada con datos objetivos

### Para Managers

**Pregunta:** "¿Qué tan complejo es modernizar el sistema de ventas?"

**SQUIT reporta:**
- 67 objetos en dominio "ventas"
- 12 de complejidad alta (>8.0)
- 45 de complejidad media (5-8)
- 10 de complejidad baja (<5)

**Resultado:** Plan de modernización priorizado

---

## 🎓 Mejores Prácticas

### 1. Preguntas Efectivas

✅ **BIEN:**
- "¿Dónde está la lógica de autenticación?"
- "Explícame sp_ProcesarVentas"
- "¿Qué se rompe si cambio ClientesMaster?"
- "Procedimientos de cálculo de impuestos"

❌ **EVITAR:**
- Queries SQL exactas (usa BigQuery directo)
- Preguntas yes/no simples
- Múltiples preguntas en una

### 2. Iteración

El agente mantiene contexto:

```
Usuario: "procedimientos de inventario"
SQUIT: [muestra 10 procedimientos]

Usuario: "explícame el primero"
SQUIT: [explica el procedimiento en detalle]

Usuario: "¿qué tablas usa?"
SQUIT: [lista las tablas referenciadas]
```

### 3. Especificidad

Más contexto = mejores resultados:

```
❌ "ventas"
✅ "procedimientos que calculan comisiones de vendedores"

❌ "qué hace esto"
✅ "explícame qué hace sp_CalcularNomina y por qué es complejo"
```

---

## 🔍 Monitoreo y Debugging

### Logs

```bash
# Ver logs de agentes
tail -f agentic_adk.log

# Con más detalle
export LOG_LEVEL=DEBUG
python scripts/demo_agentic_adk.py
```

### Métricas

El sistema registra:
- Latencia por query
- Tools usados
- Errores y excepciones
- Queries BigQuery ejecutadas

---

## 🚀 Próximos Pasos

### Implementado (Fase 1)
- ✅ MasterAgent con orquestación
- ✅ vector_search_tool para búsqueda semántica
- ✅ get_object_summary_tool para resúmenes
- ✅ find_dependencies_tool para dependencias
- ✅ analyze_impact_tool para análisis de riesgo
- ✅ Demo interactiva

### Por Implementar (Fase 2)
- [ ] CodeAnalysisAgent especializado
- [ ] ExplanationAgent para documentación auto-generada
- [ ] Cache de embeddings frecuentes
- [ ] Multi-turn conversations con memoria
- [ ] Generación de código SQL desde lenguaje natural

---

## 📚 Referencias

- **Google ADK Docs**: https://google.github.io/adk-docs/
- **BigQuery Vector Search**: https://cloud.google.com/bigquery/docs/vector-search
- **Plan de Implementación**: [AGENTIC_SYSTEM_PLAN.md](AGENTIC_SYSTEM_PLAN.md)
- **Manifesto**: [DEMOCRATIZATION_MANIFESTO.md](DEMOCRATIZATION_MANIFESTO.md)

---

**Sistema Agentic ADK v1.0**  
*Democratizando código legacy con conversación natural*  
*Desarrollado por Grupo DeAcero*
