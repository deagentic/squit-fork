# 🔐 Configuración de Credenciales

Este folder contiene las credenciales para acceder a Google Cloud Platform.

---

## 📋 Archivos en este Folder

```
.config/
├── README.md                    # Este archivo (instrucciones)
├── credentials.example.json     # Template de ejemplo
└── credentials.json            # TUS credenciales (NO commitear)
```

---

## 🚀 Setup Rápido

### 1. Obtener Credenciales de Google Cloud

#### Opción A: Crear Nueva Service Account (Recomendado)

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto (o crea uno nuevo)
3. Ve a **IAM & Admin** → **Service Accounts**
4. Click **Create Service Account**
5. Nombre: `squit-service-account`
6. Description: `Service account for SQUIT project`
7. Click **Create and Continue**

8. **Asignar Roles** (Grant this service account access to project):
   - `BigQuery Admin` (para acceso completo a BigQuery)
   - O mínimo necesario:
     - `BigQuery Data Editor`
     - `BigQuery Job User`
     - `BigQuery Read Session User`

9. Click **Continue** → **Done**

10. En la lista de Service Accounts, click en la que creaste
11. Ve a tab **Keys**
12. Click **Add Key** → **Create new key**
13. Selecciona **JSON**
14. Click **Create**

Se descargará un archivo JSON. Ese es tu `credentials.json`.

#### Opción B: Usar Cuenta Existente

Si ya tienes una service account:

1. Ve a [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Busca tu service account
3. Click en los 3 puntos (⋮) → **Manage keys**
4. **Add Key** → **Create new key** → **JSON**

### 2. Colocar el Archivo en este Folder

```bash
# Mover el archivo descargado a este folder
mv ~/Downloads/your-project-123456-abcdef.json .config/credentials.json

# O copiar
cp ~/Downloads/your-project-123456-abcdef.json .config/credentials.json
```

### 3. Actualizar .env

Edita el archivo `.env` en la raíz del proyecto:

```bash
# .env
GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json
```

### 4. Verificar Configuración

```bash
# Test de conexión
python3 scripts/verify_bigquery_access.py
```

Deberías ver:
```
✅ Credenciales válidas
✅ BigQuery accesible
✅ Dataset encontrado: deacero_sql_objects
```

---

## 🔒 Seguridad

### ⚠️ IMPORTANTE: Este archivo NO debe ir a Git

El archivo `credentials.json` contiene información sensible y **NUNCA** debe subirse a Git.

**Verificaciones:**

1. `.gitignore` ya incluye:
   ```gitignore
   # Credenciales
   credentials.json
   .config/credentials.json
   *-credentials.json
   ```

2. Verificar que NO está trackeado:
   ```bash
   git status | grep credentials.json
   # No debe devolver nada
   ```

3. Si accidentalmente lo commiteaste:
   ```bash
   # Remover del staging
   git rm --cached .config/credentials.json
   
   # Commit
   git commit -m "Remove credentials from git"
   
   # ⚠️ IMPORTANTE: Rotar las credenciales
   # Ve a Google Cloud Console y elimina la key comprometida
   ```

---

## 🔑 Permisos Mínimos Necesarios

Para SQUIT, la service account necesita:

### BigQuery
- ✅ `bigquery.datasets.get` - Leer datasets
- ✅ `bigquery.tables.get` - Leer tablas
- ✅ `bigquery.tables.list` - Listar tablas
- ✅ `bigquery.tables.getData` - Leer datos
- ✅ `bigquery.tables.create` - Crear tablas (para query_history)
- ✅ `bigquery.tables.update` - Actualizar tablas
- ✅ `bigquery.jobs.create` - Ejecutar queries

### Roles Recomendados
- **Desarrollo**: `BigQuery Admin` (acceso completo)
- **Producción**: `BigQuery Data Editor` + `BigQuery Job User` (acceso limitado)

---

## 🧪 Troubleshooting

### Error: "Could not automatically determine credentials"

```bash
# Verificar que el archivo existe
ls -lh .config/credentials.json

# Verificar que .env apunta correctamente
cat .env | grep GOOGLE_APPLICATION_CREDENTIALS

# Verificar que es JSON válido
python3 -m json.tool .config/credentials.json > /dev/null && echo "✅ JSON válido"
```

### Error: "Permission denied"

La service account no tiene los permisos necesarios:

1. Ve a [IAM & Admin](https://console.cloud.google.com/iam-admin/iam)
2. Busca tu service account
3. Click **Edit** (lápiz)
4. Agrega roles: `BigQuery Admin` o los roles mínimos listados arriba

### Error: "Invalid JSON"

El archivo JSON está corrupto:

1. Abre el archivo en un editor
2. Verifica que tiene la estructura correcta (ver `credentials.example.json`)
3. No debe haber caracteres extra al inicio/final
4. Valida con: `python3 -m json.tool .config/credentials.json`

---

## 📝 Estructura del Archivo

El archivo `credentials.json` debe tener esta estructura:

```json
{
  "type": "service_account",
  "project_id": "tu-proyecto-123456",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "tu-service-account@tu-proyecto.iam.gserviceaccount.com",
  "client_id": "123456789...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

---

## 🔄 Rotar Credenciales

Es buena práctica rotar credenciales periódicamente:

1. Crear nueva key para la service account (pasos arriba)
2. Actualizar `.config/credentials.json` con la nueva key
3. Verificar que funciona
4. Eliminar la key antigua en Google Cloud Console

**Frecuencia recomendada**: Cada 90 días en producción

---

## 📚 Referencias

- [Service Accounts - Google Cloud](https://cloud.google.com/iam/docs/service-accounts)
- [BigQuery Permissions](https://cloud.google.com/bigquery/docs/access-control)
- [Best Practices - Service Accounts](https://cloud.google.com/iam/docs/best-practices-service-accounts)

---

**Última actualización**: 2025-10-01
