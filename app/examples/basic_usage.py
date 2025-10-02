#!/usr/bin/env python3
"""
Ejemplo básico de uso del cliente SQUIT.

Este script demuestra las funcionalidades principales
del cliente BigQuery de manera clara y concisa.
"""

import sys
from pathlib import Path

# Agregar el directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from squit_client import BigQueryClient
from squit_client.exceptions import SquitError
from squit_client.utils import format_number, setup_logging, suppress_warnings


def demonstrate_basic_operations():
    """Demuestra operaciones básicas del cliente."""
    print("🔍 SQUIT - Ejemplo Básico")
    print("=" * 40)

    try:
        # Inicializar cliente
        client = BigQueryClient()
        print("✅ Cliente inicializado correctamente")

        # Validar conexión
        if not client.validate_connection():
            print("❌ Error en la conexión")
            return

        # Obtener estadísticas generales
        print("\n📊 Estadísticas Generales:")
        stats = client.get_statistics()
        print(f"  • Total objetos: {format_number(stats['total_objects'])}")
        print(f"  • Servidores únicos: {stats['unique_servers']}")
        print(f"  • Tipos de objetos: {stats['unique_object_types']}")

        # Top tipos de objetos
        print("\n🔧 Top 5 Tipos de Objetos:")
        top_types = client.get_top_objects_by_type(5)
        for _, row in top_types.iterrows():
            count_formatted = format_number(row["count"])
            print(f"  • {row['object_type']}: {count_formatted} ({row['percentage']}%)")

        print("\n🎉 Ejemplo completado exitosamente!")

    except SquitError as e:
        print(f"❌ Error del cliente: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)


def demonstrate_search_operations():
    """Demuestra operaciones de búsqueda."""
    print("\n" + "=" * 40)
    print("🔍 OPERACIONES DE BÚSQUEDA")
    print("=" * 40)

    try:
        client = BigQueryClient()

        # Búsqueda simple
        print("\n1. Búsqueda de procedimientos con 'usuario':")
        results = client.search_objects(
            search_term="usuario", object_types=["PROCEDURE"], limit=5
        )

        if not results.empty:
            print(f"   Encontrados: {len(results)} resultados")
            for _, row in results.iterrows():
                server_short = row["server"].split("\\")[-1]
                print(f"   • {server_short} - {row['object_name']}")
        else:
            print("   No se encontraron resultados")

        # Búsqueda por servidor específico
        print("\n2. Objetos en servidor específico:")
        server_results = client.get_top_servers(3)
        if not server_results.empty:
            top_server = server_results.iloc[0]["server"]
            objects = client.get_objects_by_database(
                server=top_server, database="TiSeguridad", limit=5
            )

            if not objects.empty:
                print(f"   Objetos en {top_server}/TiSeguridad:")
                for _, row in objects.iterrows():
                    print(f"   • {row['object_type']}: {row['object_name']}")

    except SquitError as e:
        print(f"❌ Error en búsqueda: {e}")


def demonstrate_custom_query():
    """Demuestra consultas personalizadas."""
    print("\n" + "=" * 40)
    print("💻 CONSULTA PERSONALIZADA")
    print("=" * 40)

    try:
        client = BigQueryClient()

        # Consulta personalizada
        custom_query = """
        SELECT
            server,
            COUNT(*) as total_objects,
            COUNT(DISTINCT object_type) as object_types,
            MAX(last_modified) as last_update
        FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
        WHERE object_type IN ('PROCEDURE', 'FUNCTION')
        GROUP BY server
        ORDER BY total_objects DESC
        LIMIT 5
        """

        results = client.execute_query(custom_query)

        print("\nTop 5 servidores por procedimientos y funciones:")
        for _, row in results.iterrows():
            server_name = row["server"].split("\\")[-1]
            total_formatted = format_number(row["total_objects"])
            print(
                f"  • {server_name}: {total_formatted} objetos "
                f"({row['object_types']} tipos)"
            )

    except SquitError as e:
        print(f"❌ Error en consulta: {e}")


def main():
    """Función principal del ejemplo."""
    # Configurar entorno
    suppress_warnings()
    setup_logging("INFO")

    # Ejecutar demostraciones
    demonstrate_basic_operations()
    demonstrate_search_operations()
    demonstrate_custom_query()

    print("\n" + "=" * 40)
    print("✨ Todas las operaciones completadas")
    print("📚 Ver documentación en docs/ para más ejemplos")


if __name__ == "__main__":
    main()
