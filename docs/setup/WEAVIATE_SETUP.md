# Configuración de Weaviate

Este documento explica cómo configurar la conexión con Weaviate para el proyecto SQUIT.

## Configuración Rápida

### 1. Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto (mismo nivel que `docker-compose.yml`) con las siguientes variables:

```bash
# URL del cluster de Weaviate (incluye https://)
WEAVIATE_URL=https://your-cluster-url.weaviate.network

# API Key para autenticación con Weaviate Cloud
WEAVIATE_API_KEY=your-api-key-here
```

**Importante**: 
- El archivo `.env` debe estar en la raíz del proyecto para que Docker Compose lo cargue automáticamente
- Las variables se cargarán tanto en el contenedor de producción como en el de desarrollo
- No incluyas el archivo `.env` en el control de versiones (ya está en `.gitignore`)

### 2. Obtener Credenciales de Weaviate Cloud

1. Ve a [Weaviate Cloud Console](https://console.weaviate.cloud/)
2. Crea una nueva cuenta o inicia sesión
3. Crea un nuevo cluster (puede ser gratuito para desarrollo)
4. Una vez creado, obtén:
   - **Cluster URL**: La URL completa de tu cluster
   - **API Key**: La clave de API para autenticación

### 3. Verificar Configuración

Antes de ejecutar los health checks, puedes verificar que las variables se cargaron correctamente:

```bash
# Verificar variables dentro del contenedor
make shell
# Dentro del contenedor:
echo $WEAVIATE_URL
echo $WEAVIATE_API_KEY
```

### 4. Verificar Conexión

Ejecuta el health check para verificar que todo funciona:

```bash
# Health check completo (BigQuery + Weaviate)
make health

# Solo Weaviate
make health-weaviate

# Demo completo con health checks
make demo
```

## Comandos Disponibles

### Health Checks

- `make health`: Verifica tanto BigQuery como Weaviate
- `make health-weaviate`: Solo verifica Weaviate
- `make demo`: Ejecuta health checks y ejemplo de uso

### Salida Esperada

Un health check exitoso mostrará:

```
🔍 SQUIT - Health Check Weaviate
===================================
🔍 Verificando conexión con Weaviate...
📍 URL: https://your-cluster.weaviate.network
✅ Conexión con Weaviate exitosa
📊 Versión de Weaviate: 1.25.x

🎉 Health check completado exitosamente!
```

## Troubleshooting

### Error: Variables de entorno no encontradas

```
❌ WEAVIATE_URL no encontrada en variables de entorno
```

**Solución**: Verifica que el archivo `.env` existe y contiene las variables correctas.

### Error: Conexión fallida

```
❌ Error al conectar con Weaviate: [error details]
```

**Posibles causas**:
- URL incorrecta (debe incluir `https://`)
- API Key inválida
- Cluster inactivo o suspendido
- Problemas de red/firewall

### Error: Dependencias no instaladas

```
❌ Error de importación: No module named 'weaviate'
```

**Solución**: Reconstruye el contenedor Docker:
```bash
make build
```

## Integración con el Código

### Uso Básico

```python
import os
import weaviate
from weaviate.classes.init import Auth
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Conectar a Weaviate Cloud
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=os.getenv("WEAVIATE_URL"),
    auth_credentials=Auth.api_key(os.getenv("WEAVIATE_API_KEY")),
)

# Verificar conexión
if client.is_ready():
    print("✅ Conectado a Weaviate")
    # Tu código aquí...
    client.close()
```

## Recursos Adicionales

- [Documentación de Weaviate Python Client](https://docs.weaviate.io/weaviate/client-libraries/python)
- [Weaviate Cloud Console](https://console.weaviate.cloud/)
- [Ejemplos de Código](https://github.com/weaviate/weaviate-python-client)
