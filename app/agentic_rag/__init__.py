"""
Agentic RAG System for SQL Code Analysis.

Este módulo implementa un sistema de Agentic RAG para analizar
y entender código SQL legacy usando Weaviate como vector database.
"""

__version__ = "1.0.0"
__author__ = "Grupo DeAcero"

from .weaviate_client import WeaviateClient
from .schema_gemini import CodeObjectsSchema, DependenciesSchema, MetadataSchema, PatternsSchema
from .agents_gemini import CodeSearchAgent, DependencyAnalysisAgent, MasterAgent
from .pipeline_gemini import GeminiIngestionPipeline as IngestionPipeline

__all__ = [
    "WeaviateClient",
    "CodeObjectsSchema", 
    "DependenciesSchema",
    "MetadataSchema",
    "PatternsSchema",
    "CodeSearchAgent",
    "DependencyAnalysisAgent", 
    "MasterAgent",
    "IngestionPipeline",
]
