#!/usr/bin/env python3
"""
Health check para conexión con Weaviate.
Verifica conectividad y estado del cluster.
"""

import os
import sys
import warnings
from typing import Optional

# Suprimir warnings innecesarios
warnings.filterwarnings("ignore", category=UserWarning)


def check_weaviate_connection() -> bool:
    """
    Verificar conexión con Weaviate usando variables de entorno.

    Returns:
        bool: True si la conexión es exitosa, False en caso contrario
    """
    try:
        # Importar después de configurar warnings
        import weaviate
        from dotenv import load_dotenv
        from weaviate.classes.init import Auth

        # Cargar variables de entorno (intentar .env si existe)
        if os.path.exists(".env"):
            load_dotenv()

        # Obtener credenciales
        weaviate_url = os.getenv("WEAVIATE_URL")
        weaviate_api_key = os.getenv("WEAVIATE_API_KEY")

        if not weaviate_url:
            print("❌ WEAVIATE_URL no encontrada en variables de entorno")
            return False

        if not weaviate_api_key:
            print("❌ WEAVIATE_API_KEY no encontrada en variables de entorno")
            return False

        print("🔍 Verificando conexión con Weaviate...")
        print(f"📍 URL: {weaviate_url}")

        # Conectar a Weaviate Cloud
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=Auth.api_key(weaviate_api_key),
        )

        # Verificar si está listo
        if client.is_ready():
            print("✅ Conexión con Weaviate exitosa")

            # Obtener información del cluster (opcional)
            try:
                meta_info = client.get_meta()
                if meta_info:
                    version = meta_info.get("version", "Desconocida")
                    print(f"📊 Versión de Weaviate: {version}")
            except Exception as e:
                print(f"⚠️  No se pudo obtener metadatos: {e}")

            # Cerrar conexión
            client.close()
            return True
        else:
            print("❌ Weaviate no está listo")
            client.close()
            return False

    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("💡 Instala las dependencias: pip install weaviate-client python-dotenv")
        return False
    except Exception as e:
        print(f"❌ Error al conectar con Weaviate: {e}")
        return False


def main():
    """Función principal para ejecutar el health check."""
    print("🔍 SQUIT - Health Check Weaviate")
    print("=" * 35)

    success = check_weaviate_connection()

    if success:
        print("\n🎉 Health check completado exitosamente!")
        sys.exit(0)
    else:
        print("\n❌ Health check falló")
        print("💡 Verifica que:")
        print("  • Las variables WEAVIATE_URL y WEAVIATE_API_KEY estén en .env")
        print("  • El cluster de Weaviate esté activo")
        print("  • Las credenciales sean correctas")
        sys.exit(1)


if __name__ == "__main__":
    main()
