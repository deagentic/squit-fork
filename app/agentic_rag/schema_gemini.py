"""
Schema definitions para Weaviate collections usando Gemini.

Este módulo define las estructuras de datos para almacenar
objetos de código, dependencias y metadata en Weaviate
usando modelos de Gemini para embeddings y generación.
"""

from typing import Dict
import weaviate.classes as wvc


class CodeObjectsSchema:
    """Schema para la collection de objetos de código SQL con Gemini."""
    
    COLLECTION_NAME = "CodeObjects"
    
    @classmethod
    def get_collection_config(cls) -> Dict:
        """Retorna la configuración de la collection usando Gemini."""
        return {
            "name": cls.COLLECTION_NAME,
            "description": "Objetos de código SQL con embeddings semánticos de Gemini",
            "properties": [
                wvc.config.Property(
                    name="server",
                    data_type=wvc.config.DataType.TEXT,
                    description="Servidor SQL donde reside el objeto",
                    index_filterable=True,
                    index_searchable=True,
                ),
                wvc.config.Property(
                    name="database",
                    data_type=wvc.config.DataType.TEXT,
                    description="Base de datos que contiene el objeto",
                    index_filterable=True,
                    index_searchable=True,
                ),
                wvc.config.Property(
                    name="schema",
                    data_type=wvc.config.DataType.TEXT,
                    description="Schema de la base de datos",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="object_name",
                    data_type=wvc.config.DataType.TEXT,
                    description="Nombre del objeto SQL",
                    index_filterable=True,
                    index_searchable=True,
                ),
                wvc.config.Property(
                    name="object_type",
                    data_type=wvc.config.DataType.TEXT,
                    description="Tipo de objeto (PROCEDURE, TABLE, VIEW, etc.)",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="sql_code",
                    data_type=wvc.config.DataType.TEXT,
                    description="Código SQL completo del objeto",
                    index_searchable=True,
                ),
                wvc.config.Property(
                    name="code_summary",
                    data_type=wvc.config.DataType.TEXT,
                    description="Resumen generado por Gemini del propósito del código",
                    index_searchable=True,
                ),
                wvc.config.Property(
                    name="business_context",
                    data_type=wvc.config.DataType.TEXT,
                    description="Contexto de negocio extraído del código",
                    index_searchable=True,
                ),
                wvc.config.Property(
                    name="complexity_score",
                    data_type=wvc.config.DataType.NUMBER,
                    description="Score de complejidad del código (0-100)",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="code_length",
                    data_type=wvc.config.DataType.INT,
                    description="Longitud del código en caracteres",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="last_modified",
                    data_type=wvc.config.DataType.DATE,
                    description="Fecha de última modificación",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="content_hash",
                    data_type=wvc.config.DataType.TEXT,
                    description="Hash del contenido para detectar cambios",
                    index_filterable=True,
                ),
                # Propiedades para chunking inteligente
                wvc.config.Property(
                    name="is_chunk",
                    data_type=wvc.config.DataType.BOOLEAN,
                    description="Indica si este objeto es un chunk de un objeto más grande",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="parent_object_id",
                    data_type=wvc.config.DataType.TEXT,
                    description="ID del objeto padre (para chunks)",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="chunk_type",
                    data_type=wvc.config.DataType.TEXT,
                    description="Tipo de chunk (header, body, procedure_section, etc.)",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="chunk_index",
                    data_type=wvc.config.DataType.INT,
                    description="Índice del chunk dentro del objeto padre",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="total_chunks",
                    data_type=wvc.config.DataType.INT,
                    description="Número total de chunks del objeto padre",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="semantic_summary",
                    data_type=wvc.config.DataType.TEXT,
                    description="Resumen semántico específico del chunk",
                    index_searchable=True,
                ),
                wvc.config.Property(
                    name="references_to",
                    data_type=wvc.config.DataType.TEXT_ARRAY,
                    description="Lista de objetos que este chunk referencia",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="char_count",
                    data_type=wvc.config.DataType.INT,
                    description="Número de caracteres en el chunk",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="line_count",
                    data_type=wvc.config.DataType.INT,
                    description="Número de líneas en el chunk",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="estimated_tokens",
                    data_type=wvc.config.DataType.INT,
                    description="Número estimado de tokens en el chunk",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="tags",
                    data_type=wvc.config.DataType.TEXT_ARRAY,
                    description="Tags automáticos basados en análisis del código",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="bigquery_id",
                    data_type=wvc.config.DataType.TEXT,
                    description="ID único en BigQuery para referencia",
                    index_filterable=True,
                ),
            ],
            # Usar vectorización manual con Gemini
            "vectorizer_config": wvc.config.Configure.Vectorizer.none(),
            "generative_config": wvc.config.Configure.Generative.google(
                project_id="dfor-prj-dev",
                model_id="gemini-2.5-flash"  # Modelo estable y correcto
            ),
        }


class DependenciesSchema:
    """Schema para la collection de dependencias usando Gemini."""
    
    COLLECTION_NAME = "Dependencies"
    
    @classmethod
    def get_collection_config(cls) -> Dict:
        """Retorna la configuración de la collection."""
        return {
            "name": cls.COLLECTION_NAME,
            "description": "Dependencias y relaciones entre objetos de código",
            "properties": [
                wvc.config.Property(
                    name="source_object_id",
                    data_type=wvc.config.DataType.TEXT,
                    description="ID del objeto que depende",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="target_object_id", 
                    data_type=wvc.config.DataType.TEXT,
                    description="ID del objeto del cual depende",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="dependency_type",
                    data_type=wvc.config.DataType.TEXT,
                    description="Tipo de dependencia (FK, VIEW, CALL, etc.)",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="relationship_strength",
                    data_type=wvc.config.DataType.NUMBER,
                    description="Fuerza de la relación (0.0-1.0)",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="context",
                    data_type=wvc.config.DataType.TEXT,
                    description="Contexto de la dependencia",
                    index_searchable=True,
                ),
                wvc.config.Property(
                    name="is_critical",
                    data_type=wvc.config.DataType.BOOL,
                    description="Si la dependencia es crítica para el negocio",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="discovered_by",
                    data_type=wvc.config.DataType.TEXT,
                    description="Método usado para descubrir la dependencia",
                    index_filterable=True,
                ),
            ],
            "vectorizer_config": wvc.config.Configure.Vectorizer.none(),
        }


class MetadataSchema:
    """Schema para metadata y contexto adicional usando Gemini."""
    
    COLLECTION_NAME = "Metadata"
    
    @classmethod  
    def get_collection_config(cls) -> Dict:
        """Retorna la configuración de la collection."""
        return {
            "name": cls.COLLECTION_NAME,
            "description": "Metadata y contexto adicional del sistema",
            "properties": [
                wvc.config.Property(
                    name="entity_type",
                    data_type=wvc.config.DataType.TEXT,
                    description="Tipo de entidad (server, database, schema)",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="entity_name",
                    data_type=wvc.config.DataType.TEXT,
                    description="Nombre de la entidad",
                    index_filterable=True,
                    index_searchable=True,
                ),
                wvc.config.Property(
                    name="description",
                    data_type=wvc.config.DataType.TEXT,
                    description="Descripción de la entidad",
                    index_searchable=True,
                ),
                wvc.config.Property(
                    name="business_domain",
                    data_type=wvc.config.DataType.TEXT,
                    description="Dominio de negocio (ventas, finanzas, etc.)",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="criticality_level",
                    data_type=wvc.config.DataType.TEXT,
                    description="Nivel de criticidad (LOW, MEDIUM, HIGH, CRITICAL)",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="owner_team",
                    data_type=wvc.config.DataType.TEXT,
                    description="Equipo responsable",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="documentation_url",
                    data_type=wvc.config.DataType.TEXT,
                    description="URL a documentación relacionada",
                ),
                wvc.config.Property(
                    name="last_analyzed",
                    data_type=wvc.config.DataType.DATE,
                    description="Fecha del último análisis",
                    index_filterable=True,
                ),
            ],
            "vectorizer_config": wvc.config.Configure.Vectorizer.none(),
        }


class PatternsSchema:
    """Schema para patrones de código identificados usando Gemini."""
    
    COLLECTION_NAME = "CodePatterns"
    
    @classmethod
    def get_collection_config(cls) -> Dict:
        """Retorna la configuración de la collection."""
        return {
            "name": cls.COLLECTION_NAME,
            "description": "Patrones de código identificados automáticamente por Gemini",
            "properties": [
                wvc.config.Property(
                    name="pattern_name",
                    data_type=wvc.config.DataType.TEXT,
                    description="Nombre del patrón identificado",
                    index_filterable=True,
                    index_searchable=True,
                ),
                wvc.config.Property(
                    name="pattern_type",
                    data_type=wvc.config.DataType.TEXT,
                    description="Tipo de patrón (DESIGN_PATTERN, ANTI_PATTERN, etc.)",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="description",
                    data_type=wvc.config.DataType.TEXT,
                    description="Descripción del patrón",
                    index_searchable=True,
                ),
                wvc.config.Property(
                    name="code_examples",
                    data_type=wvc.config.DataType.TEXT_ARRAY,
                    description="Ejemplos de código que implementan el patrón",
                ),
                wvc.config.Property(
                    name="object_ids",
                    data_type=wvc.config.DataType.TEXT_ARRAY,
                    description="IDs de objetos que implementan este patrón",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="confidence_score",
                    data_type=wvc.config.DataType.NUMBER,
                    description="Confianza en la identificación del patrón",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="impact_level",
                    data_type=wvc.config.DataType.TEXT,
                    description="Nivel de impacto (LOW, MEDIUM, HIGH)",
                    index_filterable=True,
                ),
                wvc.config.Property(
                    name="recommendation",
                    data_type=wvc.config.DataType.TEXT,
                    description="Recomendación para el patrón",
                    index_searchable=True,
                ),
            ],
            "vectorizer_config": wvc.config.Configure.Vectorizer.none(),
            "generative_config": wvc.config.Configure.Generative.google(
                project_id="dfor-prj-dev",
                model_id="gemini-2.5-flash"  # Modelo estable y correcto
            ),
        }
