#!/usr/bin/env python3
"""
Ejemplo de uso del cliente SQUIT reorganizado.
"""

from squit_client import BigQueryClient
from squit_client.exceptions import SquitError


def main():
    """Ejemplo de uso básico."""
    print("🔍 SQUIT - Ejemplo de Uso")
    print("=" * 40)

    try:
        # Inicializar cliente
        client = BigQueryClient()
        print("✅ Cliente inicializado correctamente")

        # Obtener estadísticas rápidas
        print("\n📊 Estadísticas:")
        stats = client.get_statistics()
        print(f"  • Total objetos: {stats['total_objects']:,}")
        print(f"  • Servidores únicos: {stats['unique_servers']}")
        print(f"  • Tipos de objetos: {stats['unique_object_types']}")

        # Top tipos de objetos
        print("\n🔧 Top 5 tipos de objetos:")
        top_types = client.get_top_objects_by_type(5)
        for _, row in top_types.iterrows():
            print(f"  • {row['object_type']}: {row['count']:,} ({row['percentage']}%)")

        # Búsqueda de ejemplo
        print("\n🔍 Búsqueda de procedimientos con 'usuario':")
        results = client.search_objects(
            search_term="usuario", object_types=["PROCEDURE"], limit=5
        )
        print(f"  Encontrados: {len(results)} resultados")
        if not results.empty:
            for _, row in results.iterrows():
                print(f"  • {row['server']} - {row['object_name']}")

        # Consulta personalizada
        print("\n💻 Consulta personalizada:")
        query = """
        SELECT server, COUNT(*) as procedures_count
        FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
        WHERE object_type = 'PROCEDURE'
        GROUP BY server
        ORDER BY procedures_count DESC
        LIMIT 3
        """

        custom_results = client.execute_query(query)
        print("  Top 3 servidores con más procedimientos:")
        for _, row in custom_results.iterrows():
            print(f"  • {row['server']}: {row['procedures_count']:,}")

        print("\n🎉 Ejemplo completado exitosamente!")

    except SquitError as e:
        print(f"❌ Error del cliente: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")


if __name__ == "__main__":
    main()
