"""
Smart Chunking para código SQL masivo.

Este módulo implementa estrategias inteligentes de chunking que optimizan
para embeddings semánticos en lugar de mapeo 1:1 con BigQuery.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CodeChunk:
    """Representa un chunk inteligente de código."""
    chunk_id: str
    parent_object_id: str
    object_name: str
    object_type: str
    server: str
    database: str
    schema: str
    
    # Contenido del chunk
    code_content: str
    chunk_type: str  # header, body, function, procedure, etc.
    chunk_index: int
    total_chunks: int
    
    # Metadatos semánticos
    semantic_summary: str
    business_context: str
    complexity_score: float
    tags: List[str]
    
    # Referencias
    references_to: List[str]  # Objetos que este chunk referencia
    referenced_by: List[str]  # Objetos que referencian este chunk
    
    # Información de tamaño
    char_count: int
    line_count: int
    estimated_tokens: int


class SQLSmartChunker:
    """
    Chunker inteligente para código SQL que optimiza para embeddings semánticos.
    
    Estrategias:
    1. Chunking por estructura semántica (no por tamaño fijo)
    2. Preservar contexto de negocio en cada chunk
    3. Identificar y separar funciones/procedimientos individuales
    4. Mantener coherencia semántica
    5. Optimizar para búsqueda por funcionalidad
    """
    
    def __init__(self):
        """Inicializa el chunker inteligente."""
        # Configuración de chunking optimizada para objetos masivos
        self.max_chunk_size = 6000  # Caracteres por chunk (óptimo para Gemini embeddings)
        self.min_chunk_size = 800   # Mínimo para mantener contexto semántico
        self.overlap_size = 300     # Overlap entre chunks para contexto
        self.mega_object_threshold = 1000000  # 1M chars = objeto mega (tratamiento especial)
        
        # Patrones SQL para identificar estructuras
        self.sql_patterns = {
            'procedure_start': re.compile(r'CREATE\s+PROCEDURE\s+(\[?[\w\.\]]+)', re.IGNORECASE),
            'function_start': re.compile(r'CREATE\s+FUNCTION\s+(\[?[\w\.\]]+)', re.IGNORECASE),
            'view_start': re.compile(r'CREATE\s+VIEW\s+(\[?[\w\.\]]+)', re.IGNORECASE),
            'trigger_start': re.compile(r'CREATE\s+TRIGGER\s+(\[?[\w\.\]]+)', re.IGNORECASE),
            'table_start': re.compile(r'CREATE\s+TABLE\s+(\[?[\w\.\]]+)', re.IGNORECASE),
            'begin_block': re.compile(r'\bBEGIN\b', re.IGNORECASE),
            'end_block': re.compile(r'\bEND\b', re.IGNORECASE),
            'go_separator': re.compile(r'^\s*GO\s*$', re.MULTILINE | re.IGNORECASE),
            'comment_block': re.compile(r'/\*.*?\*/', re.DOTALL),
            'comment_line': re.compile(r'--.*$', re.MULTILINE),
        }
    
    def should_chunk_object(self, sql_code: str, object_type: str) -> bool:
        """Determina si un objeto necesita chunking."""
        code_length = len(sql_code)
        
        # Chunking basado en tamaño y tipo (ajustado para objetos mega)
        if code_length > self.mega_object_threshold:  # Objetos mega (>1M chars)
            return True
        elif code_length > 50000:  # Objetos muy grandes siempre se chunkean
            return True
        elif code_length > 15000 and object_type in ['PROCEDURE', 'FUNCTION']:
            return True
        elif code_length > 25000:  # Otros tipos solo si son muy grandes
            return True
        
        return False
    
    def chunk_sql_object(self, obj: Dict[str, Any]) -> List[CodeChunk]:
        """
        Chunkea un objeto SQL de forma inteligente.
        
        Args:
            obj: Diccionario con datos del objeto SQL
            
        Returns:
            Lista de chunks semánticamente coherentes
        """
        sql_code = obj.get('sql_code', '')
        object_name = obj.get('object_name', '')
        object_type = obj.get('object_type', '')
        
        # Si no necesita chunking, retornar como chunk único
        if not self.should_chunk_object(sql_code, object_type):
            return self._create_single_chunk(obj)
        
        logger.info("Chunking objeto %s (%s) - %d chars", 
                   object_name, object_type, len(sql_code))
        
        # Estrategia de chunking basada en el tipo de objeto
        if object_type == 'PROCEDURE':
            return self._chunk_stored_procedure(obj)
        elif object_type == 'FUNCTION':
            return self._chunk_function(obj)
        elif object_type == 'VIEW':
            return self._chunk_view(obj)
        elif object_type == 'TRIGGER':
            return self._chunk_trigger(obj)
        else:
            return self._chunk_generic_sql(obj)
    
    def _create_single_chunk(self, obj: Dict[str, Any]) -> List[CodeChunk]:
        """Crea un chunk único para objetos pequeños."""
        sql_code = obj.get('sql_code', '')
        
        chunk = CodeChunk(
            chunk_id=f"{obj.get('bigquery_id', '')}_chunk_0",
            parent_object_id=obj.get('bigquery_id', ''),
            object_name=obj.get('object_name', ''),
            object_type=obj.get('object_type', ''),
            server=obj.get('server', ''),
            database=obj.get('database', ''),
            schema=obj.get('schema', ''),
            code_content=sql_code,
            chunk_type='complete',
            chunk_index=0,
            total_chunks=1,
            semantic_summary=self._generate_semantic_summary(sql_code, obj.get('object_name', '')),
            business_context=self._extract_business_context(sql_code, obj.get('object_name', '')),
            complexity_score=self._calculate_complexity_score(sql_code),
            tags=self._extract_semantic_tags(sql_code, obj.get('object_name', '')),
            references_to=self._extract_references(sql_code),
            referenced_by=[],  # Se completará después
            char_count=len(sql_code),
            line_count=len(sql_code.splitlines()),
            estimated_tokens=len(sql_code) // 4  # Estimación aproximada
        )
        
        return [chunk]
    
    def _chunk_stored_procedure(self, obj: Dict[str, Any]) -> List[CodeChunk]:
        """Chunkea un stored procedure por secciones lógicas."""
        sql_code = obj.get('sql_code', '')
        
        # Identificar secciones del procedure
        sections = self._identify_procedure_sections(sql_code)
        
        chunks = []
        for i, section in enumerate(sections):
            chunk = self._create_chunk_from_section(obj, section, i, len(sections), 'procedure_section')
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_function(self, obj: Dict[str, Any]) -> List[CodeChunk]:
        """Chunkea una función por lógica interna."""
        sql_code = obj.get('sql_code', '')
        
        # Las funciones suelen ser más compactas, chunking por bloques lógicos
        logical_blocks = self._identify_logical_blocks(sql_code)
        
        chunks = []
        for i, block in enumerate(logical_blocks):
            chunk = self._create_chunk_from_section(obj, block, i, len(logical_blocks), 'function_block')
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_view(self, obj: Dict[str, Any]) -> List[CodeChunk]:
        """Chunkea una vista por subconsultas o JOINs."""
        sql_code = obj.get('sql_code', '')
        
        # Identificar subconsultas y JOINs complejos
        query_parts = self._identify_query_parts(sql_code)
        
        chunks = []
        for i, part in enumerate(query_parts):
            chunk = self._create_chunk_from_section(obj, part, i, len(query_parts), 'query_part')
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_trigger(self, obj: Dict[str, Any]) -> List[CodeChunk]:
        """Chunkea un trigger por eventos y acciones."""
        sql_code = obj.get('sql_code', '')
        
        # Identificar eventos y acciones del trigger
        trigger_parts = self._identify_trigger_parts(sql_code)
        
        chunks = []
        for i, part in enumerate(trigger_parts):
            chunk = self._create_chunk_from_section(obj, part, i, len(trigger_parts), 'trigger_action')
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_generic_sql(self, obj: Dict[str, Any]) -> List[CodeChunk]:
        """Chunking genérico basado en separadores y tamaño."""
        sql_code = obj.get('sql_code', '')
        
        # Dividir por separadores GO o por tamaño si no hay estructura clara
        parts = self._split_by_separators_or_size(sql_code)
        
        chunks = []
        for i, part in enumerate(parts):
            chunk = self._create_chunk_from_section(obj, part, i, len(parts), 'sql_segment')
            chunks.append(chunk)
        
        return chunks
    
    def _identify_procedure_sections(self, sql_code: str) -> List[Dict[str, Any]]:
        """Identifica secciones lógicas en un stored procedure."""
        sections = []
        lines = sql_code.splitlines()
        
        current_section = {'type': 'header', 'lines': [], 'start_line': 0}
        in_block = False
        block_depth = 0
        
        for i, line in enumerate(lines):
            line_upper = line.upper().strip()
            
            # Detectar inicio de bloques
            if 'BEGIN' in line_upper:
                if current_section['lines']:
                    sections.append(current_section)
                current_section = {'type': 'logic_block', 'lines': [line], 'start_line': i}
                in_block = True
                block_depth += 1
                continue
            
            # Detectar fin de bloques
            if 'END' in line_upper and in_block:
                block_depth -= 1
                current_section['lines'].append(line)
                if block_depth == 0:
                    sections.append(current_section)
                    current_section = {'type': 'footer', 'lines': [], 'start_line': i + 1}
                    in_block = False
                continue
            
            # Detectar secciones especiales
            if any(keyword in line_upper for keyword in ['DECLARE', 'SET', 'SELECT', 'INSERT', 'UPDATE', 'DELETE']):
                if not in_block and current_section['type'] != 'sql_statement':
                    if current_section['lines']:
                        sections.append(current_section)
                    current_section = {'type': 'sql_statement', 'lines': [line], 'start_line': i}
                    continue
            
            current_section['lines'].append(line)
        
        # Agregar última sección
        if current_section['lines']:
            sections.append(current_section)
        
        return sections
    
    def _identify_logical_blocks(self, sql_code: str) -> List[Dict[str, Any]]:
        """Identifica bloques lógicos en el código."""
        # Implementación simplificada - dividir por BEGIN/END y statements principales
        return self._split_by_separators_or_size(sql_code)
    
    def _identify_query_parts(self, sql_code: str) -> List[Dict[str, Any]]:
        """Identifica partes de una consulta compleja."""
        parts = []
        
        # Buscar subconsultas, CTEs, JOINs complejos
        cte_pattern = re.compile(r'WITH\s+\w+\s+AS\s*\(', re.IGNORECASE)
        join_pattern = re.compile(r'(INNER|LEFT|RIGHT|FULL)\s+JOIN', re.IGNORECASE)
        
        lines = sql_code.splitlines()
        current_part = {'type': 'main_query', 'lines': [], 'start_line': 0}
        
        for i, line in enumerate(lines):
            if cte_pattern.search(line):
                if current_part['lines']:
                    parts.append(current_part)
                current_part = {'type': 'cte', 'lines': [line], 'start_line': i}
            elif join_pattern.search(line):
                if current_part['lines']:
                    parts.append(current_part)
                current_part = {'type': 'join_section', 'lines': [line], 'start_line': i}
            else:
                current_part['lines'].append(line)
        
        if current_part['lines']:
            parts.append(current_part)
        
        return parts
    
    def _identify_trigger_parts(self, sql_code: str) -> List[Dict[str, Any]]:
        """Identifica partes de un trigger."""
        # Simplificado - dividir por eventos y acciones principales
        return self._split_by_separators_or_size(sql_code)
    
    def _split_by_separators_or_size(self, sql_code: str) -> List[Dict[str, Any]]:
        """Divide código por separadores GO o por tamaño."""
        parts = []
        
        # Primero intentar dividir por GO
        go_parts = self.sql_patterns['go_separator'].split(sql_code)
        
        for part in go_parts:
            part = part.strip()
            if not part:
                continue
                
            # Si la parte es muy grande, dividir por tamaño
            if len(part) > self.max_chunk_size:
                size_parts = self._split_by_size_with_overlap(part)
                parts.extend(size_parts)
            else:
                parts.append({
                    'type': 'sql_segment',
                    'lines': part.splitlines(),
                    'start_line': 0,
                    'content': part
                })
        
        return parts
    
    def _split_by_size_with_overlap(self, code: str) -> List[Dict[str, Any]]:
        """Divide código por tamaño manteniendo overlap para contexto."""
        parts = []
        lines = code.splitlines()
        current_lines = []
        current_size = 0
        
        for line in lines:
            line_size = len(line) + 1  # +1 for newline
            
            if current_size + line_size > self.max_chunk_size and current_lines:
                # Crear parte actual
                parts.append({
                    'type': 'size_chunk',
                    'lines': current_lines.copy(),
                    'start_line': 0,
                    'content': '\n'.join(current_lines)
                })
                
                # Mantener overlap
                overlap_lines = self._get_overlap_lines(current_lines)
                current_lines = overlap_lines + [line]
                current_size = sum(len(l) + 1 for l in current_lines)
            else:
                current_lines.append(line)
                current_size += line_size
        
        # Agregar última parte
        if current_lines:
            parts.append({
                'type': 'size_chunk',
                'lines': current_lines,
                'start_line': 0,
                'content': '\n'.join(current_lines)
            })
        
        return parts
    
    def _get_overlap_lines(self, lines: List[str]) -> List[str]:
        """Obtiene líneas de overlap para mantener contexto."""
        if not lines:
            return []
        
        # Tomar las últimas líneas que sumen aproximadamente overlap_size
        overlap_lines = []
        current_size = 0
        
        for line in reversed(lines):
            line_size = len(line) + 1
            if current_size + line_size > self.overlap_size:
                break
            overlap_lines.insert(0, line)
            current_size += line_size
        
        return overlap_lines
    
    def _create_chunk_from_section(
        self, 
        obj: Dict[str, Any], 
        section: Dict[str, Any], 
        chunk_index: int, 
        total_chunks: int,
        chunk_type: str
    ) -> CodeChunk:
        """Crea un CodeChunk a partir de una sección."""
        
        if 'content' in section:
            content = section['content']
        else:
            content = '\n'.join(section['lines'])
        
        chunk_id = f"{obj.get('bigquery_id', '')}_chunk_{chunk_index}"
        
        return CodeChunk(
            chunk_id=chunk_id,
            parent_object_id=obj.get('bigquery_id', ''),
            object_name=obj.get('object_name', ''),
            object_type=obj.get('object_type', ''),
            server=obj.get('server', ''),
            database=obj.get('database', ''),
            schema=obj.get('schema', ''),
            code_content=content,
            chunk_type=chunk_type,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            semantic_summary=self._generate_semantic_summary(content, obj.get('object_name', '')),
            business_context=self._extract_business_context(content, obj.get('object_name', '')),
            complexity_score=self._calculate_complexity_score(content),
            tags=self._extract_semantic_tags(content, obj.get('object_name', '')),
            references_to=self._extract_references(content),
            referenced_by=[],
            char_count=len(content),
            line_count=len(content.splitlines()),
            estimated_tokens=len(content) // 4
        )
    
    def _generate_semantic_summary(self, code: str, object_name: str) -> str:
        """Genera resumen semántico del código."""
        # Análisis básico de patrones
        code_upper = code.upper()
        
        operations = []
        if 'SELECT' in code_upper:
            operations.append('consulta')
        if 'INSERT' in code_upper:
            operations.append('inserción')
        if 'UPDATE' in code_upper:
            operations.append('actualización')
        if 'DELETE' in code_upper:
            operations.append('eliminación')
        if 'CREATE' in code_upper:
            operations.append('creación')
        
        if operations:
            return f"Código que realiza {', '.join(operations)} en {object_name}"
        else:
            return f"Lógica de negocio en {object_name}"
    
    def _extract_business_context(self, code: str, object_name: str) -> str:
        """Extrae contexto de negocio del código."""
        # Buscar patrones de negocio en nombres y comentarios
        business_terms = []
        
        # Términos comunes de negocio en el código
        patterns = {
            'ventas': ['venta', 'sale', 'factura', 'invoice', 'cliente', 'customer'],
            'inventario': ['inventario', 'inventory', 'stock', 'almacen', 'warehouse'],
            'finanzas': ['pago', 'payment', 'cuenta', 'account', 'balance'],
            'produccion': ['produccion', 'production', 'manufactura', 'process'],
            'logistica': ['envio', 'shipping', 'transporte', 'delivery'],
        }
        
        code_lower = code.lower()
        for domain, terms in patterns.items():
            if any(term in code_lower or term in object_name.lower() for term in terms):
                business_terms.append(domain)
        
        if business_terms:
            return f"Relacionado con: {', '.join(business_terms)}"
        else:
            return "Lógica de aplicación"
    
    def _calculate_complexity_score(self, code: str) -> float:
        """Calcula score de complejidad del código."""
        lines = len(code.splitlines())
        chars = len(code)
        
        # Contar estructuras complejas
        complexity_patterns = {
            'joins': len(re.findall(r'\bJOIN\b', code, re.IGNORECASE)),
            'subqueries': len(re.findall(r'\(\s*SELECT', code, re.IGNORECASE)),
            'conditions': len(re.findall(r'\bWHERE\b|\bHAVING\b', code, re.IGNORECASE)),
            'loops': len(re.findall(r'\bWHILE\b|\bFOR\b', code, re.IGNORECASE)),
            'cursors': len(re.findall(r'\bCURSOR\b', code, re.IGNORECASE)),
        }
        
        # Calcular score basado en múltiples factores
        base_score = min(lines / 100, 5.0)  # Score base por líneas
        complexity_bonus = sum(complexity_patterns.values()) * 0.5
        
        return min(base_score + complexity_bonus, 10.0)
    
    def _extract_semantic_tags(self, code: str, object_name: str) -> List[str]:
        """Extrae tags semánticos del código."""
        tags = []
        code_upper = code.upper()
        
        # Tags por operaciones SQL
        if 'SELECT' in code_upper:
            tags.append('query')
        if 'INSERT' in code_upper:
            tags.append('insert')
        if 'UPDATE' in code_upper:
            tags.append('update')
        if 'DELETE' in code_upper:
            tags.append('delete')
        if 'CREATE' in code_upper:
            tags.append('ddl')
        
        # Tags por complejidad
        if 'JOIN' in code_upper:
            tags.append('joins')
        if 'CURSOR' in code_upper:
            tags.append('cursor')
        if 'WHILE' in code_upper or 'FOR' in code_upper:
            tags.append('loops')
        if 'TRANSACTION' in code_upper:
            tags.append('transactional')
        
        # Tags por dominio de negocio (basado en nombres)
        name_lower = object_name.lower()
        if any(term in name_lower for term in ['venta', 'sale', 'factura', 'cliente']):
            tags.append('sales')
        if any(term in name_lower for term in ['inventario', 'stock', 'almacen']):
            tags.append('inventory')
        if any(term in name_lower for term in ['pago', 'payment', 'cuenta']):
            tags.append('finance')
        
        return list(set(tags))  # Remover duplicados
    
    def _extract_references(self, code: str) -> List[str]:
        """Extrae referencias a otros objetos en el código."""
        references = []
        
        # Patrones para encontrar referencias a objetos
        patterns = [
            r'FROM\s+(\[?[\w\.\]]+)',
            r'JOIN\s+(\[?[\w\.\]]+)',
            r'EXEC\s+(\[?[\w\.\]]+)',
            r'EXECUTE\s+(\[?[\w\.\]]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, code, re.IGNORECASE)
            references.extend(matches)
        
        # Limpiar y deduplicar referencias
        cleaned_refs = []
        for ref in references:
            ref = ref.strip('[]').strip()
            if ref and ref not in cleaned_refs:
                cleaned_refs.append(ref)
        
        return cleaned_refs
