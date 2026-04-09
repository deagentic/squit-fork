#!/usr/bin/env python3
"""
Ejecutor limpio sin warnings para el cliente SQUIT.
"""

import logging
import os
import warnings
from contextlib import redirect_stderr
from io import StringIO

# Suprimir warnings específicos
warnings.filterwarnings("ignore", category=UserWarning, module="google.cloud.bigquery")
warnings.filterwarnings("ignore", message=".*BigQuery Storage.*")

# Configurar logging para suprimir warnings de gRPC
logging.getLogger("grpc").setLevel(logging.ERROR)
logging.getLogger("google.auth").setLevel(logging.ERROR)
logging.getLogger("google.cloud").setLevel(logging.ERROR)

# Variables de entorno para suprimir warnings de gRPC/ALTS
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "3"
os.environ["GRPC_TRACE"] = ""
os.environ["GRPC_VERBOSITY"] = "NONE"


def run_example_clean():
    """Ejecutar ejemplo sin warnings."""
    # Capturar stderr para filtrar warnings
    stderr_capture = StringIO()

    with redirect_stderr(stderr_capture):
        try:
            from squit_client import BigQueryClient
            from squit_client.exceptions import SquitError

            print("🔍 SQUIT - Ejemplo de Uso (Modo Limpio)")
            print("=" * 45)

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
                print(
                    f"  • {row['object_type']}: {row['count']:,} ({row['percentage']}%)"
                )

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
            print("✨ Ejecutándose con BigQuery Storage API (sin warnings)")

        except SquitError as e:
            print(f"❌ Error del cliente: {e}")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")

    # Filtrar stderr capturado para mostrar solo errores importantes
    stderr_content = stderr_capture.getvalue()
    if stderr_content:
        # Solo mostrar errores que no sean de ALTS/gRPC
        lines = stderr_content.split("\n")
        important_errors = [
            line
            for line in lines
            if line
            and "ALTS creds ignored" not in line
            and "absl::InitializeLog" not in line
            and "BigQuery Storage module" not in line
        ]

        if important_errors:
            print("\n⚠️  Warnings importantes:")
            for error in important_errors:
                print(f"  {error}")


if __name__ == "__main__":
    run_example_clean()
