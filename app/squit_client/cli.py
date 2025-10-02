"""
Interfaz de línea de comandos para SQUIT.

Este módulo proporciona una interfaz CLI profesional
para interactuar con el cliente BigQuery.
"""

import sys
from typing import Optional

import click

from .client import BigQueryClient
from .exceptions import SquitError
from .utils import format_number, setup_logging, suppress_warnings


@click.group()
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Nivel de logging",
)
@click.option("--quiet", "-q", is_flag=True, help="Suprimir warnings y salida verbose")
@click.option(
    "--credentials",
    "-c",
    type=click.Path(exists=True),
    help="Ruta a las credenciales de Google Cloud",
)
@click.pass_context
def cli(ctx: click.Context, log_level: str, quiet: bool, credentials: Optional[str]):
    """SQUIT - SQL Objects BigQuery Client."""
    ctx.ensure_object(dict)
    ctx.obj["log_level"] = log_level
    ctx.obj["quiet"] = quiet
    ctx.obj["credentials"] = credentials

    setup_logging(log_level)
    if quiet:
        suppress_warnings()


@cli.command()
@click.pass_context
def info(ctx: click.Context):
    """Mostrar información de la tabla."""
    try:
        client = BigQueryClient(ctx.obj["credentials"])
        table_info = client.get_table_info()

        click.echo("📊 Información de la Tabla")
        click.echo("=" * 30)
        click.echo(f"Proyecto: {table_info['project']}")
        click.echo(f"Dataset: {table_info['dataset']}")
        click.echo(f"Tabla: {table_info['table_id']}")
        click.echo(f"Registros: {format_number(table_info['num_rows'])}")
        click.echo(f"Tamaño: {format_number(table_info['num_bytes'])} bytes")
        click.echo(f"Ubicación: {table_info['location']}")
        click.echo(f"Columnas: {len(table_info['schema'])}")

    except SquitError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--limit", "-l", default=10, help="Número de registros")
@click.pass_context
def sample(ctx: click.Context, limit: int):
    """Obtener muestra de datos."""
    try:
        client = BigQueryClient(ctx.obj["credentials"])
        df = client.get_sample_data(limit)

        if not df.empty:
            click.echo(f"📋 Muestra de {len(df)} registros:")
            click.echo(df.to_string(index=False, max_colwidth=30))
        else:
            click.echo("No se encontraron datos")

    except SquitError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("search_term")
@click.option("--type", "-t", "object_types", multiple=True, help="Tipos de objeto")
@click.option("--server", "-s", "servers", multiple=True, help="Servidores")
@click.option("--limit", "-l", default=10, help="Límite de resultados")
@click.pass_context
def search(
    ctx: click.Context,
    search_term: str,
    object_types: tuple,
    servers: tuple,
    limit: int,
):
    """Buscar objetos SQL."""
    try:
        client = BigQueryClient(ctx.obj["credentials"])
        results = client.search_objects(
            search_term=search_term,
            object_types=list(object_types) if object_types else None,
            servers=list(servers) if servers else None,
            limit=limit,
        )

        if not results.empty:
            click.echo(f"🔍 Encontrados {len(results)} resultados:")
            display_cols = ["server", "database", "object_name", "object_type"]
            click.echo(results[display_cols].to_string(index=False))
        else:
            click.echo("No se encontraron resultados")

    except SquitError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--limit", "-l", default=10, help="Número de tipos")
@click.pass_context
def stats(ctx: click.Context, limit: int):
    """Mostrar estadísticas de la tabla."""
    try:
        client = BigQueryClient(ctx.obj["credentials"])

        # Estadísticas generales
        general_stats = client.get_statistics()
        click.echo("📊 Estadísticas Generales")
        click.echo("=" * 25)
        click.echo(f"Total objetos: {format_number(general_stats['total_objects'])}")
        click.echo(f"Servidores únicos: {general_stats['unique_servers']}")
        click.echo(f"Bases de datos: {general_stats['unique_databases']}")
        click.echo(f"Tipos de objetos: {general_stats['unique_object_types']}")

        # Top tipos de objetos
        top_types = client.get_top_objects_by_type(limit)
        click.echo(f"\n🔧 Top {limit} Tipos de Objetos")
        click.echo("=" * 30)
        for _, row in top_types.iterrows():
            click.echo(
                f"{row['object_type']}: {format_number(row['count'])} "
                f"({row['percentage']}%)"
            )

    except SquitError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("query")
@click.option("--output", "-o", help="Archivo de salida")
@click.option("--format", "-f", default="csv", help="Formato de exportación")
@click.option("--limit", "-l", help="Límite de filas")
@click.option("--dry-run", is_flag=True, help="Solo validar consulta")
@click.pass_context
def query(
    ctx: click.Context,
    query: str,
    output: Optional[str],
    format: str,
    limit: Optional[int],
    dry_run: bool,
):
    """Ejecutar consulta SQL personalizada."""
    try:
        client = BigQueryClient(ctx.obj["credentials"])

        if dry_run:
            client.execute_query(query, limit=limit, dry_run=True)
            click.echo("✅ Consulta validada exitosamente")
            return

        df = client.execute_query(query, limit=limit)

        if output:
            success = client.export_data(query, output, format)
            if success:
                click.echo(f"✅ Datos exportados a {output}")
            else:
                click.echo("❌ Error exportando datos")
        else:
            if not df.empty:
                click.echo(df.to_string(index=False, max_colwidth=50))
            else:
                click.echo("No se encontraron resultados")

    except SquitError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def validate(ctx: click.Context):
    """Validar conexión y configuración."""
    try:
        client = BigQueryClient(ctx.obj["credentials"])

        click.echo("🔍 Validando conexión...")
        if client.validate_connection():
            click.echo("✅ Conexión exitosa")

            # Mostrar información básica
            info = client.get_table_info()
            click.echo(f"📊 Tabla: {info['table_id']}")
            click.echo(f"📈 Registros: {format_number(info['num_rows'])}")
        else:
            click.echo("❌ Error en la conexión")
            sys.exit(1)

    except SquitError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


def main():
    """Punto de entrada principal para la CLI."""
    cli()


if __name__ == "__main__":
    main()
