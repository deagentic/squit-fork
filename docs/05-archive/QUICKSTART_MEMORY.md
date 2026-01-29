# 🚀 Quick Start: Memoria Multi-Turn en SQUIT

## ⚡ Inicio Rápido (2 minutos)

### 1. Ejecutar SQUIT con memoria
```bash
cd /Users/karim/My\ Drive\ \(ktouma@deacero.com\)/squit
python3 scripts/squit.py
```

### 2. Conversación con contexto
```
squit[1]> explicame kayak, cuales son los principales store procedures
→ Obtiene lista completa con detalles

squit[2]> dame mas detalles del primer procedure que mencionaste
→ ✅ Recuerda "kayak" y la lista del turno anterior

squit[3]> y sus dependencias
→ ✅ Sabe que hablas de ese procedure específico
```

### 3. Reset cuando cambies de tema
```
squit[4]> reset
→ 🔄 Memoria limpiada

squit[1]> ahora hablemos de inventario
→ Nueva conversación sin contexto de kayak
```

## 🎯 Comandos Disponibles

| Comando | Acción |
|---------|--------|
| `reset`, `clear`, `reiniciar` | Limpia memoria y empieza nueva sesión |
| `exit`, `quit`, `salir`, `q` | Cierra SQUIT |

## 💡 Tips

### ✅ Buenas Prácticas

**Análisis progresivo:**
```
[1]> busca procedures de ventas
[2]> el tercero, explicalo
[3]> muestra su codigo sql
[4]> y que hace ese SELECT de la linea 45
```

**Referencias contextuales:**
- "este procedimiento"
- "el primero que mencionaste"  
- "esos objetos"
- "la tabla anterior"

**Reset estratégico:**
```
[5]> reset  # Cambias de tema
[1]> ahora analiza procedures de compras
```

### ❌ Evitar

**No abusar de contexto excesivo:**
```
[1]> kayak
[2]> inventario
[3]> que relacion tienen?  # ⚠️ Poco contexto
```

Mejor con reset:
```
[1]> kayak
[2]> reset
[1]> inventario
[2]> reset
[1]> como se relacionan kayak e inventario?  # ✅ Contexto explícito
```

## 🧪 Validar que Funciona

### Test de Memoria Básica
```bash
python3 scripts/test_memory.py

# Deberías ver:
# ✅ MEMORIA FUNCIONAL: El agente recordó el contexto del turno anterior
# ✅ RESET FUNCIONAL: El agente olvidó el contexto anterior
```

### Test de Conciencia Contextual
```bash
python3 scripts/test_context_awareness.py

# Valida 4 casos:
# 1. Referencias vagas ("todos") en contexto
# 2. Referencias ordinales ("el primero")
# 3. Referencias posesivas ("sus")
# 4. Reset limpia contexto

# Deberías ver:
# ✅ TEST 1: PASÓ - Mantuvo contexto de kayak
# ✅ TEST 2: PASÓ - Recordó contexto de inventario
# ✅ TEST 3: PASÓ - Entendió 'sus' como del procedure
# ✅ TEST 4: PASÓ - Olvidó contexto después de reset
# 🎉 Conciencia contextual funcional
```

## 📊 Indicadores de Memoria Activa

### Prompt con contador
```
squit[1]>  # Primer turno
squit[2]>  # Segundo turno (memoria de turno 1)
squit[3]>  # Tercer turno (memoria de turnos 1-2)
```

### Después de reset
```
squit[5]> reset
squit[1]>  # ✅ Contador reinicia, memoria limpia
```

## 🔧 Troubleshooting

### No recuerda contexto
```bash
# Verificar que no hay errores al iniciar
python3 scripts/squit.py

# Deberías ver:
✓ Agente listo
💬 Conversación con memoria multi-turn activada
```

### Error al inicializar
```bash
# Verificar variables de entorno
echo $GEMINI_API_KEY
echo $GOOGLE_CLOUD_PROJECT

# Si faltan, editar .env
nano .env
```

## 📚 Más Información

- **Documentación técnica**: `docs/MEMORY_OPTIMIZATION.md`
- **Resumen ejecutivo**: `OPTIMIZATION_SUMMARY.md`
- **Test de validación**: `scripts/test_memory.py`

---

**Última actualización**: 2025-10-01  
**Versión**: 2.0.0

