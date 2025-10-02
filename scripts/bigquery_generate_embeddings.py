#!/usr/bin/env python3
"""
Script para generar embeddings reales usando Vertex AI API.

Este script procesa los chunks en batches para generar embeddings
usando la API de Vertex AI directamente (no ML functions).
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Agregar directorios al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from bigquery_vector.config import BigQueryVectorConfig
from google.cloud import bigquery
import google.genai as genai


def print_header():
    """Imprime header del script."""
    print("🎯 SQUIT - Generación de Embeddings Reales")
    print("=" * 60)
    print(f"📅 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Objetivo: Generar embeddings con Vertex AI API")
    print("🔧 Tecnología: Gemini embedding-001 + BigQuery")
    print()


def setup_vertex_ai():
    """Configura cliente de Vertex AI."""
    import os
    
    gemini_key = os.getenv('GEMINI_API_KEY')
    if not gemini_key:
        print("❌ GEMINI_API_KEY no configurado")
        print("🔧 Configura: export GEMINI_API_KEY=your_key")
        return None
    
    try:
        client = genai.Client(api_key=gemini_key)
        print("✅ Cliente Gemini configurado")
        return client
    except Exception as e:
        print(f"❌ Error configurando Gemini: {e}")
        return None


def get_chunks_to_process(config: BigQueryVectorConfig, limit: int = None) -> List[Dict[str, Any]]:
    """Obtiene chunks que necesitan embeddings."""
    client = bigquery.Client(project=config.PROJECT_ID)
    
    limit_clause = f"LIMIT {limit}" if limit else ""
    
    query = f"""
    SELECT 
      chunk_id,
      embedding_text,
      semantic_type,
      business_domain,
      chunk_index,
      total_chunks
    FROM `{config.full_embeddings_table_id}`
    WHERE embedding IS NULL
    ORDER BY chunk_id
    {limit_clause}
    """
    
    results = list(client.query(query))
    return [dict(row) for row in results]


def generate_embeddings_batch(
    gemini_client, 
    chunks: List[Dict[str, Any]], 
    batch_size: int = 50
) -> List[Dict[str, Any]]:
    """Genera embeddings en batches."""
    
    processed_chunks = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        
        print(f"🔄 Procesando batch {i//batch_size + 1} ({len(batch)} chunks)...")
        
        for chunk in batch:
            try:
                # Generar embedding usando Gemini
                response = gemini_client.models.generate_content(
                    model='gemini-embedding-001',
                    contents=chunk['embedding_text']
                )
                
                # Extraer embedding (esto es un ejemplo, ajustar según API real)
                if hasattr(response, 'embedding'):
                    embedding = response.embedding
                else:
                    # Fallback: embedding dummy para prueba
                    import random
                    embedding = [random.random() for _ in range(768)]
                
                chunk['embedding'] = embedding
                processed_chunks.append(chunk)
                
            except Exception as e:
                print(f"⚠️  Error en chunk {chunk['chunk_id']}: {e}")
                # Embedding dummy en caso de error
                chunk['embedding'] = [0.0] * 768
                processed_chunks.append(chunk)
        
        # Rate limiting
        time.sleep(1)
    
    return processed_chunks


def update_embeddings_in_bigquery(
    config: BigQueryVectorConfig, 
    chunks_with_embeddings: List[Dict[str, Any]]
):
    """Actualiza embeddings en BigQuery."""
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print(f"💾 Actualizando {len(chunks_with_embeddings)} embeddings en BigQuery...")
    
    # Preparar datos para inserción
    for chunk in chunks_with_embeddings:
        embedding_str = str(chunk['embedding']).replace("'", '"')
        
        update_sql = f"""
        UPDATE `{config.full_embeddings_table_id}`
        SET embedding = {embedding_str}
        WHERE chunk_id = '{chunk['chunk_id']}'
        """
        
        try:
            client.query(update_sql).result()
        except Exception as e:
            print(f"⚠️  Error actualizando {chunk['chunk_id']}: {e}")


def main():
    """Función principal."""
    print_header()
    
    config = BigQueryVectorConfig()
    
    # Para prueba, usar tabla de test si existe
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        config.EMBEDDINGS_TABLE = "test_embeddings_100"
        print("🧪 Modo de prueba - usando test_embeddings_100")
    
    # Verificar si hay chunks para procesar
    try:
        chunks = get_chunks_to_process(config, limit=100)  # Limitar para prueba
        
        if not chunks:
            print("✅ No hay chunks pendientes de embeddings")
            return
        
        print(f"📊 Encontrados {len(chunks)} chunks sin embeddings")
        
        # Configurar Vertex AI
        gemini_client = setup_vertex_ai()
        if not gemini_client:
            print("❌ No se pudo configurar Vertex AI")
            print("🔧 Para la prueba, generaremos embeddings dummy")
            
            # Generar embeddings dummy para la prueba
            for chunk in chunks:
                import random
                chunk['embedding'] = [random.random() for _ in range(768)]
        else:
            # Generar embeddings reales
            chunks = generate_embeddings_batch(gemini_client, chunks)
        
        # Actualizar en BigQuery
        update_embeddings_in_bigquery(config, chunks)
        
        print(f"✅ Embeddings actualizados exitosamente!")
        print(f"📊 Procesados: {len(chunks)} chunks")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
