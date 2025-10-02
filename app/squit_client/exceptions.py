"""
Excepciones personalizadas para el cliente SQUIT.

Este módulo define todas las excepciones específicas del dominio
para proporcionar un manejo de errores claro y específico.
"""


class SquitError(Exception):
    """
    Excepción base para errores del cliente SQUIT.

    Todas las excepciones específicas del cliente SQUIT
    deben heredar de esta clase base.
    """

    pass


class ConnectionError(SquitError):
    """
    Error de conexión a BigQuery.

    Se lanza cuando hay problemas de conectividad
    o acceso a los servicios de BigQuery.
    """

    pass


class QueryError(SquitError):
    """
    Error al ejecutar consulta SQL.

    Se lanza cuando hay problemas con la sintaxis SQL,
    permisos insuficientes o errores de ejecución.
    """

    pass


class AuthenticationError(SquitError):
    """
    Error de autenticación con Google Cloud.

    Se lanza cuando hay problemas con las credenciales
    o permisos de acceso a Google Cloud Platform.
    """

    pass


class ConfigurationError(SquitError):
    """
    Error en la configuración del cliente.

    Se lanza cuando hay problemas con parámetros
    de configuración inválidos o faltantes.
    """

    pass


class ValidationError(SquitError):
    """
    Error de validación de datos.

    Se lanza cuando los datos de entrada no cumplen
    con los criterios de validación esperados.
    """

    pass


class ExportError(SquitError):
    """
    Error durante la exportación de datos.

    Se lanza cuando hay problemas al exportar
    resultados a archivos externos.
    """

    pass
