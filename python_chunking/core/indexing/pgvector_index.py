"""
pgvector index implementation for vector storage and retrieval.
"""
import asyncio
import json
import os
from typing import List, Dict, Optional, AsyncGenerator
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from core.index import (
    Chunk, ChunkWithoutID, ChunkMetadata, ILLM, IndexingProgressUpdate, 
    PathAndCacheKey, RefreshIndexResults, MarkCompleteCallback,
    IndexResultType, BranchAndDir
)
from core.indexing.chunk.chunk import chunk_document, should_chunk
from core.embeddings.embeddings_provider import EmbeddingsProvider


class PgVectorIndex:
    """pgvector-based vector index for code chunks"""
    
    def __init__(self, embeddings_provider: Optional[EmbeddingsProvider] = None, 
                 connection_string: str = "postgresql://localhost/code_chunks",
                 base_path: Optional[str] = None):
        self.embeddings_provider = embeddings_provider or EmbeddingsProvider()
        self.connection_string = connection_string
        self.conn = None
        self.base_path = Path(base_path).resolve() if base_path else None
    
    async def initialize(self):
        """Initialize PostgreSQL connection"""
        if self.conn is None:
            try:
                self.conn = psycopg2.connect(self.connection_string)
                print(f"PostgreSQL connected: {self.connection_string}")
            except Exception as e:
                print(f"Failed to connect to PostgreSQL: {e}")
                raise
    
    async def get_chunks(
        self,
        item: PathAndCacheKey,
        content: str,
    ) -> List[Chunk]:
        """Get chunks for a file"""
        if not should_chunk(item.path, content):
            return []
        
        chunks = []
        async for chunk in chunk_document(item.path, content, 1000, item.cache_key):
            chunks.append(chunk)
        
        return chunks
    
    async def get_embeddings(self, chunks: List[Chunk]) -> List[List[float]]:
        """Get embeddings for chunks"""
        return await self.embeddings_provider.get_embeddings(chunks)
    
    def _get_relative_path(self, filepath: str) -> str:
        """Convert absolute path to relative path based on base_path"""
        if self.base_path is None:
            return filepath
        
        try:
            file_path = Path(filepath).resolve()
            relative_path = file_path.relative_to(self.base_path)
            return str(relative_path)
        except ValueError:
            # 파일이 base_path 외부에 있는 경우 절대 경로 반환
            return filepath
    
    def _get_absolute_path(self, filepath: str) -> str:
        """Convert relative path to absolute path based on base_path"""
        if self.base_path is None:
            return filepath
        
        file_path = Path(filepath)
        if file_path.is_absolute():
            return filepath
        
        return str(self.base_path / file_path)
    
    async def insert_chunks(self, chunks: List[Chunk], embeddings: List[List[float]]):
        """Insert chunks with embeddings into PostgreSQL"""
        await self.initialize()
        
        if not chunks or not embeddings:
            print("No chunks or embeddings to insert")
            return
        
        try:
            with self.conn.cursor() as cur:
                for chunk, embedding in zip(chunks, embeddings):
                    # 메타데이터를 JSON으로 직렬화
                    metadata_json = None
                    if chunk.metadata:
                        metadata_dict = {
                            "symbol_type": chunk.metadata.symbol_type,
                            "symbol_name": chunk.metadata.symbol_name,
                            "imports": chunk.metadata.imports,
                            "exports": chunk.metadata.exports,
                            "references_to": chunk.metadata.references_to,
                            "referenced_by": chunk.metadata.referenced_by,
                            "symbol_definitions": chunk.metadata.symbol_definitions,
                            "extends": chunk.metadata.extends,
                            "implements": chunk.metadata.implements,
                            "subclasses": chunk.metadata.subclasses,
                            "dependencies": chunk.metadata.dependencies,
                            "dependents": chunk.metadata.dependents,
                        }
                        metadata_json = json.dumps(metadata_dict, ensure_ascii=False)
                    
                    # 벡터를 PostgreSQL 배열 형태로 변환
                    embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                    
                    # 경로를 상대 경로로 변환
                    relative_path = self._get_relative_path(chunk.filepath)
                    
                    cur.execute("""
                        INSERT INTO chunks (uuid, path, cachekey, content, start_line, end_line, index, metadata, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (uuid) DO UPDATE SET
                            content = EXCLUDED.content,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding
                    """, (
                        f"chunk_{chunk.index}_{hash(chunk.content)}",
                        relative_path,
                        chunk.digest,
                        chunk.content,
                        chunk.start_line,
                        chunk.end_line,
                        chunk.index,
                        metadata_json,
                        embedding_str
                    ))
            
            self.conn.commit()
            print(f"Inserted {len(chunks)} chunks into PostgreSQL (relative paths from {self.base_path})")
            
        except Exception as e:
            self.conn.rollback()
            print(f"Error inserting data: {e}")
            raise
    
    async def retrieve(
        self,
        query: str,
        n_retrieve: int = 10,
        filters: Optional[Dict] = None,
    ) -> List[Chunk]:
        """Retrieve similar chunks"""
        await self.initialize()
        
        # Get query embedding
        query_embedding = await self.embeddings_provider.get_query_embedding(query)
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Build the query
                sql = """
                    SELECT uuid, path, cachekey, content, start_line, end_line, index, metadata,
                           1 - (embedding <=> %s::vector) as similarity
                    FROM chunks
                """
                params = [embedding_str]
                
                # Add filters if provided
                if filters:
                    filter_conditions = []
                    for key, value in filters.items():
                        if key == "path":
                            filter_conditions.append("path = %s")
                            params.append(value)
                        elif key == "metadata":
                            filter_conditions.append("metadata @> %s")
                            params.append(json.dumps(value))
                    
                    if filter_conditions:
                        sql += " WHERE " + " AND ".join(filter_conditions)
                
                sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
                params.extend([embedding_str, n_retrieve])
                
                cur.execute(sql, params)
                rows = cur.fetchall()
                
                chunks = []
                for row in rows:
                    # 메타데이터 역직렬화
                    metadata = None
                    if row['metadata']:
                        try:
                            metadata_dict = json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata']
                            metadata = ChunkMetadata(**metadata_dict)
                        except Exception as e:
                            print(f"Failed to deserialize metadata: {e}")
                    
                    # 상대 경로를 절대 경로로 변환 (필요한 경우)
                    filepath = self._get_absolute_path(row['path'])
                    
                    chunk = Chunk(
                        content=row['content'],
                        start_line=row['start_line'],
                        end_line=row['end_line'],
                        filepath=filepath,
                        index=row['index'],
                        digest=row['cachekey'],
                        metadata=metadata,
                    )
                    chunks.append(chunk)
                
                return chunks
                
        except Exception as e:
            print(f"Error retrieving chunks: {e}")
            return []
    
    async def update(
        self,
        tag: str,
        results: RefreshIndexResults,
        mark_complete: MarkCompleteCallback,
    ) -> AsyncGenerator[IndexingProgressUpdate, None]:
        """Update the index with new chunks"""
        await self.initialize()
        
        total_items = len(results.compute) + len(results.add_tag) + len(results.delete)
        processed = 0
        
        # Process compute items
        for item in results.compute:
            try:
                with open(item.path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                chunks = await self.get_chunks(item, content)
                if chunks:
                    embeddings = await self.get_embeddings(chunks)
                    await self.insert_chunks(chunks, embeddings)
                
                mark_complete([item], IndexResultType.COMPUTE)
                processed += 1
                
                yield IndexingProgressUpdate(
                    desc=f"Processed {item.path}",
                    status="success",
                    progress=processed / total_items
                )
                
            except Exception as e:
                print(f"Error processing {item.path}: {e}")
                mark_complete([item], IndexResultType.COMPUTE)
                processed += 1
                yield IndexingProgressUpdate(
                    desc=f"Error processing {item.path}",
                    status="error",
                    progress=processed / total_items
                )
        
        # Process add_tag items
        for item in results.add_tag:
            # Add tag logic here if needed
            mark_complete([item], IndexResultType.ADD_TAG)
            processed += 1
        
        # Process delete items
        for item in results.delete:
            # Delete logic here if needed
            mark_complete([item], IndexResultType.DELETE)
            processed += 1
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()