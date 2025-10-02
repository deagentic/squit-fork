# 📁 Data Folder

Datos y configuraciones del proyecto.

---

## 📋 Archivos

### `catalog.example.csv`
Catálogo de ejemplo de aplicaciones y dominios de negocio (formato simplificado).

**Columnas (formato simplificado):**
- `application_name`: Nombre de la aplicación
- `database_name`: Base de datos
- `business_domain`: Dominio (ventas, inventario, etc.)
- `description`: Descripción

**Formato completo (usado en `app/data/catalogo.csv`):**
- `Name`: Nombre de aplicación
- `Sistema Objeto`: Código de sistema (ej: "KAY - Kayak")
- `Descripcion`: Descripción detallada
- `Proceso End To End`: Proceso de negocio
- Plus: 15+ columnas adicionales (tecnología, servidores, etc.)

---

## 🔍 **Carga Automática de Catálogo**

El sistema busca automáticamente catálogos en este orden de prioridad:

1. `data/catalogo.csv` ⭐ **(catálogo real con 280+ aplicaciones)**
2. `data/catalog.csv` (alternativa)
3. `data/catalog.example.csv` (ejemplo formato simple)

**Ubicación única**: Solo usa archivos en `data/` (root), no en `app/data/`.

**Nota**: Los archivos `*.csv` en esta carpeta están en `.gitignore`

---

**Última actualización**: 2025-10-02
