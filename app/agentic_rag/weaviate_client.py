"""
Cliente para conectar y gestionar Weaviate.

Este módulo maneja la conexión con Weaviate y proporciona
métodos para crear collections y gestionar datos.
"""

import logging
from typing import Dict, List, Optional, Any

import weaviate
import weaviate.classes as wvc

from .config import WeaviateConfig
from .schema_gemini import CodeObjectsSchema, DependenciesSchema, MetadataSchema, PatternsSchema

logger = logging.getLogger(__name__)


class WeaviateClient:
    """
    Cliente para interactuar con Weaviate.
    
    Maneja la conexión, creación de schemas y operaciones CRUD
    para el sistema de Agentic RAG.
    """

    def __init__(self, config: Optional[WeaviateConfig] = None):
        """
        Inicializa el cliente Weaviate.
        
        Args:
            config: Configuración de Weaviate. Si no se proporciona,
                   usa la configuración por defecto.
        """
        self.config = config or WeaviateConfig()
        self._client: Optional[weaviate.WeaviateClient] = None
        self._connect()

    def _connect(self) -> None:
        """Establece conexión con Weaviate."""
        try:
            # Configurar headers de autenticación
            headers = {}
            if self.config.WEAVIATE_API_KEY:
                headers["Authorization"] = f"Bearer {self.config.WEAVIATE_API_KEY}"

            # Parsear URL correctamente
            url = self.config.WEAVIATE_URL
            if "://" in url:
                # Extraer solo el host, sin puerto duplicado
                host = url.split("://")[1].split(":")[0]
                port = 8080
            else:
                host = url.split(":")[0]
                port = 8080
            
            # Conectar a Weaviate
            self._client = weaviate.connect_to_local(
                host=host,
                port=port,
                headers=headers,
            )
            
            # Verificar conexión
            if self._client.is_ready():
                logger.info("Conexión exitosa con Weaviate en %s", self.config.WEAVIATE_URL)
            else:
                raise Exception("Weaviate no está listo")
                
        except Exception as e:
            logger.error("Error conectando a Weaviate: %s", e)
            raise

    @property
    def client(self) -> weaviate.WeaviateClient:
        """Retorna el cliente Weaviate."""
        if self._client is None:
            raise Exception("Cliente Weaviate no inicializado")
        return self._client

    def create_schema(self) -> bool:
        """
        Crea todas las collections necesarias en Weaviate.
        
        Returns:
            True si todas las collections se crearon exitosamente.
        """
        try:
            schemas = [
                CodeObjectsSchema.get_collection_config(),
                DependenciesSchema.get_collection_config(), 
                MetadataSchema.get_collection_config(),
                PatternsSchema.get_collection_config(),
            ]
            
            for schema_config in schemas:
                collection_name = schema_config["name"]
                
                # Verificar si la collection ya existe
                if self.client.collections.exists(collection_name):
                    logger.info("Collection %s ya existe", collection_name)
                    continue
                
                # Crear collection
                collection = self.client.collections.create(
                    name=collection_name,
                    description=schema_config["description"],
                    properties=schema_config["properties"],
                    vectorizer_config=schema_config["vectorizer_config"],
                    generative_config=schema_config.get("generative_config"),
                )
                
                logger.info("Collection %s creada exitosamente", collection_name)
            
            return True
            
        except Exception as e:
            logger.error("Error creando schema: %s", e)
            return False

    def get_collection(self, collection_name: str) -> weaviate.Collection:
        """
        Obtiene una collection por nombre.
        
        Args:
            collection_name: Nombre de la collection.
            
        Returns:
            Collection de Weaviate.
            
        Raises:
            Exception: Si la collection no existe.
        """
        try:
            return self.client.collections.get(collection_name)
        except Exception as e:
            raise Exception(f"Collection {collection_name} no encontrada: {e}")

    def insert_code_object_with_vector(self, code_data: Dict[str, Any], vector: List[float]) -> str:
        """
        Inserta un objeto de código con vector manual en Weaviate.
        
        Args:
            code_data: Diccionario con los datos del objeto.
            vector: Vector embedding generado externamente.
            
        Returns:
            UUID del objeto insertado.
        """
        try:
            collection = self.get_collection("CodeObjects")
            
            # Preparar datos para inserción
            properties = self._prepare_code_object_properties(code_data)
            
            # Insertar objeto con vector manual
            uuid = collection.data.insert(
                properties=properties,
                vector=vector,
            )
            logger.debug("Objeto de código insertado con vector: %s", uuid)
            
            return str(uuid)
            
        except Exception as e:
            logger.error("Error insertando objeto de código con vector: %s", e)
            raise

    def insert_code_object(self, code_data: Dict[str, Any]) -> str:
        """
        Inserta un objeto de código en Weaviate.
        
        Args:
            code_data: Diccionario con los datos del objeto.
            
        Returns:
            UUID del objeto insertado.
        """
        try:
            collection = self.get_collection(CodeObjectsSchema.COLLECTION_NAME)
            
            # Preparar datos para inserción
            properties = self._prepare_code_object_properties(code_data)
            
            # Insertar objeto
            uuid = collection.data.insert(properties)
            logger.debug("Objeto de código insertado: %s", uuid)
            
            return str(uuid)
            
        except Exception as e:
            logger.error("Error insertando objeto de código: %s", e)
            raise

    def search_code_objects_by_vector(
        self,
        vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca objetos de código usando vector específico.
        
        Args:
            vector: Vector embedding para búsqueda.
            limit: Límite de resultados.
            filters: Filtros adicionales.
            
        Returns:
            Lista de objetos encontrados.
        """
        try:
            collection = self.get_collection("CodeObjects")
            
            # Preparar filtros
            where_filter = self._build_where_filter(filters) if filters else None
            
            # Ejecutar búsqueda vectorial
            response = collection.query.near_vector(
                near_vector=vector,
                limit=limit,
                where=where_filter,
            )
            
            # Procesar resultados
            results = []
            for obj in response.objects:
                result = {
                    "uuid": str(obj.uuid),
                    "score": getattr(obj.metadata, "distance", None),
                    **obj.properties,
                }
                results.append(result)
            
            logger.info("Búsqueda vectorial ejecutada: %d resultados", len(results))
            return results
            
        except Exception as e:
            logger.error("Error en búsqueda vectorial: %s", e)
            return []

    def _prepare_code_object_properties(self, code_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara las propiedades del objeto de código para Weaviate."""
        return {
            "server": code_data.get("server", ""),
            "database": code_data.get("database", ""),
            "schema": code_data.get("schema", ""),
            "object_name": code_data.get("object_name", ""),
            "object_type": code_data.get("object_type", ""),
            "sql_code": code_data.get("sql_code", ""),
            "code_summary": code_data.get("code_summary", ""),
            "business_context": code_data.get("business_context", ""),
            "complexity_score": code_data.get("complexity_score", 0),
            "code_length": len(code_data.get("sql_code", "")),
            "last_modified": code_data.get("last_modified"),
            "content_hash": code_data.get("content_hash", ""),
            "tags": code_data.get("tags", []),
            "bigquery_id": code_data.get("bigquery_id", ""),
        }

    def search_code_objects(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        hybrid: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Busca objetos de código usando búsqueda híbrida.
        
        Args:
            query: Consulta de búsqueda.
            limit: Límite de resultados.
            filters: Filtros adicionales.
            hybrid: Si usar búsqueda híbrida o solo vectorial.
            
        Returns:
            Lista de objetos encontrados.
        """
        try:
            collection = self.get_collection(CodeObjectsSchema.COLLECTION_NAME)
            
            # Preparar filtros
            where_filter = self._build_where_filter(filters) if filters else None
            
            # Ejecutar búsqueda
            if hybrid:
                response = collection.query.hybrid(
                    query=query,
                    limit=limit,
                    where=where_filter,
                    alpha=self.config.HYBRID_SEARCH_ALPHA,
                )
            else:
                response = collection.query.near_text(
                    query=query,
                    limit=limit,
                    where=where_filter,
                )
            
            # Procesar resultados
            results = []
            for obj in response.objects:
                result = {
                    "uuid": str(obj.uuid),
                    "score": getattr(obj.metadata, "score", None),
                    **obj.properties,
                }
                results.append(result)
            
            logger.info("Búsqueda ejecutada: %d resultados para '%s'", len(results), query)
            return results
            
        except Exception as e:
            logger.error("Error en búsqueda: %s", e)
            return []

    def _build_where_filter(self, filters: Dict[str, Any]) -> wvc.query.Filter:
        """Construye filtros Where para Weaviate."""
        conditions = []
        
        for field, value in filters.items():
            if isinstance(value, list):
                # Filtro IN para listas
                or_conditions = [
                    wvc.query.Filter.by_property(field).equal(v) for v in value
                ]
                conditions.append(wvc.query.Filter.any_of(or_conditions))
            else:
                # Filtro simple
                conditions.append(wvc.query.Filter.by_property(field).equal(value))
        
        if len(conditions) == 1:
            return conditions[0]
        elif len(conditions) > 1:
            return wvc.query.Filter.all_of(conditions)
        else:
            return None

    def insert_dependency(self, dependency_data: Dict[str, Any]) -> str:
        """
        Inserta una dependencia en Weaviate.
        
        Args:
            dependency_data: Datos de la dependencia.
            
        Returns:
            UUID de la dependencia insertada.
        """
        try:
            collection = self.get_collection(DependenciesSchema.COLLECTION_NAME)
            uuid = collection.data.insert(dependency_data)
            return str(uuid)
        except Exception as e:
            logger.error("Error insertando dependencia: %s", e)
            raise

    def get_object_dependencies(self, object_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todas las dependencias de un objeto.
        
        Args:
            object_id: ID del objeto en BigQuery.
            
        Returns:
            Lista de dependencias.
        """
        try:
            collection = self.get_collection(DependenciesSchema.COLLECTION_NAME)
            
            response = collection.query.fetch_objects(
                where=wvc.query.Filter.by_property("source_object_id").equal(object_id),
                limit=1000,
            )
            
            return [
                {
                    "uuid": str(obj.uuid),
                    **obj.properties,
                }
                for obj in response.objects
            ]
            
        except Exception as e:
            logger.error("Error obteniendo dependencias: %s", e)
            return []

    def get_collection_stats(self) -> Dict[str, int]:
        """
        Obtiene estadísticas de todas las collections.
        
        Returns:
            Diccionario con conteos por collection.
        """
        stats = {}
        
        collections = [
            CodeObjectsSchema.COLLECTION_NAME,
            DependenciesSchema.COLLECTION_NAME,
            MetadataSchema.COLLECTION_NAME,
            PatternsSchema.COLLECTION_NAME,
        ]
        
        for collection_name in collections:
            try:
                collection = self.get_collection(collection_name)
                # Usar aggregate para obtener count
                response = collection.aggregate.over_all(total_count=True)
                stats[collection_name] = response.total_count or 0
            except Exception as e:
                logger.warning("Error obteniendo stats de %s: %s", collection_name, e)
                stats[collection_name] = 0
        
        return stats

    def health_check(self) -> Dict[str, Any]:
        """
        Verifica la salud del sistema Weaviate.
        
        Returns:
            Diccionario con información de salud.
        """
        try:
            # Verificar conexión básica
            is_ready = self.client.is_ready()
            
            # Obtener estadísticas
            stats = self.get_collection_stats() if is_ready else {}
            
            # Verificar configuración de Gemini
            gemini_configured = bool(self.config.GEMINI_API_KEY)
            
            return {
                "status": "healthy" if is_ready else "unhealthy",
                "weaviate_ready": is_ready,
                "gemini_configured": gemini_configured,
                "collections": stats,
                "url": self.config.WEAVIATE_URL,
            }
            
        except Exception as e:
            logger.error("Error en health check: %s", e)
            return {
                "status": "error",
                "error": str(e),
                "weaviate_ready": False,
                "gemini_configured": False,
                "collections": {},
            }

    def close(self) -> None:
        """Cierra la conexión con Weaviate."""
        if self._client:
            self._client.close()
            logger.info("Conexión con Weaviate cerrada")
