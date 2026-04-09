"""
Configuración para BigQuery Vector Search.
"""

import os
from typing import Dict, List


class BigQueryVectorConfig:
    """Configuración para el sistema BigQuery Vector Search."""
    
    # Configuración de BigQuery
    PROJECT_ID: str = os.getenv("GOOGLE_CLOUD_PROJECT", "dfor-prj-dev")
    DATASET_ID: str = "deacero_sql_objects"
    
    # Tablas del sistema
    SOURCE_TABLE: str = "sql_objects_code"
    CHUNKS_TABLE: str = "intelligent_chunks"
    EMBEDDINGS_TABLE: str = "chunk_embeddings"
    VECTOR_INDEX_NAME: str = "chunks_vector_index"
    
    # Configuración de chunking
    MEGA_OBJECT_THRESHOLD: int = 1000000  # 1M caracteres
    LARGE_OBJECT_THRESHOLD: int = 50000   # 50K caracteres
    MEDIUM_OBJECT_THRESHOLD: int = 15000  # 15K caracteres
    MIN_CHUNK_SIZE: int = 500            # Mínimo viable
    MAX_CHUNK_SIZE: int = 8000           # Óptimo para embeddings
    MAX_CHUNKS_PER_OBJECT: int = 100     # Límite de chunks por objeto
    
    # Configuración de embeddings optimizada
    EMBEDDING_MODEL: str = "gemini-embedding-001"  # Endpoint de Vertex AI
    EMBEDDING_MODEL_NAME: str = "gemini_embedding_model"  # Nombre del modelo en BigQuery
    EMBEDDING_DIMENSIONS: int = 768  # Optimizado: 768 dims = 75% menos storage, 3x más rápido
    
    # Configuración de índices vectoriales
    VECTOR_INDEX_TYPE: str = "IVF"
    DISTANCE_TYPE: str = "COSINE"
    IVF_NUM_LISTS: int = 1000  # Optimizado para ~3M objetos
    
    # Configuración de procesamiento
    BATCH_SIZE: int = 1000
    MAX_PARALLEL_JOBS: int = 10
    
    # Patrones SQL para clasificación semántica
    SEMANTIC_PATTERNS: Dict[str, List[str]] = {
        "complex_query": [
            r"SELECT.*FROM.*JOIN",
            r"WITH.*AS.*SELECT",
            r"UNION.*SELECT",
        ],
        "stored_procedure": [
            r"CREATE\s+PROCEDURE",
            r"ALTER\s+PROCEDURE",
            r"BEGIN.*END",
        ],
        "function": [
            r"CREATE\s+FUNCTION",
            r"ALTER\s+FUNCTION",
            r"RETURNS\s+",
        ],
        "view": [
            r"CREATE\s+VIEW",
            r"ALTER\s+VIEW",
        ],
        "trigger": [
            r"CREATE\s+TRIGGER",
            r"ALTER\s+TRIGGER",
        ],
        "ddl": [
            r"CREATE\s+TABLE",
            r"ALTER\s+TABLE",
            r"CREATE\s+INDEX",
        ],
        "dml": [
            r"INSERT\s+INTO",
            r"UPDATE.*SET",
            r"DELETE\s+FROM",
        ],
    }
    
    # Configuración de business context
    BUSINESS_DOMAINS: Dict[str, List[str]] = {
        "ventas": ["venta", "sale", "factura", "invoice", "cliente", "customer"],
        "inventario": ["inventario", "inventory", "stock", "almacen", "warehouse"],
        "finanzas": ["pago", "payment", "cuenta", "account", "balance", "finanz"],
        "produccion": ["produccion", "production", "manufactura", "process"],
        "logistica": ["envio", "shipping", "transporte", "delivery", "logistic"],
        "recursos_humanos": ["empleado", "employee", "nomina", "payroll", "hr"],
        "compras": ["compra", "purchase", "proveedor", "supplier", "vendor"],
    }
    
    @property
    def full_source_table_id(self) -> str:
        """ID completo de la tabla fuente."""
        return f"{self.PROJECT_ID}.{self.DATASET_ID}.{self.SOURCE_TABLE}"
    
    @property
    def full_chunks_table_id(self) -> str:
        """ID completo de la tabla de chunks."""
        return f"{self.PROJECT_ID}.{self.DATASET_ID}.{self.CHUNKS_TABLE}"
    
    @property
    def full_embeddings_table_id(self) -> str:
        """ID completo de la tabla de embeddings."""
        return f"{self.PROJECT_ID}.{self.DATASET_ID}.{self.EMBEDDINGS_TABLE}"
    
    @property
    def full_embedding_model_id(self) -> str:
        """ID completo del modelo de embeddings en BigQuery."""
        return f"{self.PROJECT_ID}.{self.DATASET_ID}.{self.EMBEDDING_MODEL_NAME}"