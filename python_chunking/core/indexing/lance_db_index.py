"""
LanceDB index implementation for vector storage and retrieval.
"""
import asyncio
from typing import List, Dict, Optional, AsyncGenerator
import lancedb
import numpy as np
import json
from pathlib import Path
from core.index import (
    Chunk, ChunkWithoutID, ChunkMetadata, ILLM, IndexingProgressUpdate, 
    PathAndCacheKey, RefreshIndexResults, MarkCompleteCallback,
    IndexResultType, BranchAndDir
)
from core.indexing.chunk.chunk import chunk_document, should_chunk

from core.embeddings.embeddings_provider import EmbeddingsProvider

# try:
#     from core.embeddings.embeddings_provider import EmbeddingsProvider
# except ImportError:
#     print("Warning: sentence-transformers not available, using simple embeddings")
#     from core.embeddings.simple_embeddings import SimpleEmbeddingsProvider as EmbeddingsProvider


class LanceDbIndex:
    """LanceDB-based vector index for code chunks"""
    
    def __init__(self, embeddings_provider: Optional[EmbeddingsProvider] = None):
        self.embeddings_provider = embeddings_provider or EmbeddingsProvider()
        self.db = None
        self.table = None
    
    async def initialize(self):
        """Initialize LanceDB connection"""
        if self.db is None:
            try:
                # 절대 경로 사용
                db_path = Path(__file__).parent.parent.parent / "data" / "lancedb"
                db_path.mkdir(parents=True, exist_ok=True)
                self.db = lancedb.connect(str(db_path))
                print(f"LanceDB initialized at: {db_path}")
            except Exception as e:
                print(f"Failed to initialize LanceDB: {e}")
                raise
    
    async def get_chunks(
        self,
        item: PathAndCacheKey,
        content: str,
    ) -> List[Chunk]:
        """Get chunks for a file"""
        chunks = []
        
        chunk_params = {
            "filepath": item.path,
            "contents": content,
            "max_chunk_size": self.embeddings_provider.max_embedding_chunk_size,
            "digest": item.cache_key,
        }
        
        async for chunk in chunk_document(**chunk_params):
            if len(chunk.content) == 0:
                raise ValueError("did not chunk properly")
            chunks.append(chunk)
        
        return chunks
    
    async def get_embeddings(self, chunks: List[Chunk]) -> List[List[float]]:
        """Get embeddings for chunks"""
        return await self.embeddings_provider.get_embeddings(chunks)
    
    async def insert_chunks(self, chunks: List[Chunk], embeddings: List[List[float]]):
        """Insert chunks with embeddings into LanceDB"""
        await self.initialize()
        
        print(f"DB state: {self.db is not None}, DB type: {type(self.db)}, DB value: {self.db}")
        print(f"chunks: {len(chunks)}, embeddings: {len(embeddings)}")
        
        if self.db is None:
            raise RuntimeError("Database not initialized")
        
        if not chunks or not embeddings:
            print("No chunks or embeddings to insert")
            return
        
        # Prepare data for insertion
        data = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
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
            
            data.append({
                "uuid": f"chunk_{i}_{hash(chunk.content)}",
                "path": chunk.filepath,
                "cachekey": chunk.digest,
                "vector": embedding,
                "content": chunk.content,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "index": chunk.index,
                "metadata": metadata_json,
            })
        
        if data:
            try:
                if self.table is None:
                    # Try to open existing table first
                    try:
                        self.table = self.db.open_table("chunks")
                        print("Opened existing chunks table")
                    except:
                        # Create new table if it doesn't exist
                        self.table = self.db.create_table("chunks", data)
                        print("Created new chunks table")
                        return  # Data already inserted during creation
                
                # Add data to existing table
                self.table.add(data)
                print(f"Added {len(data)} chunks to table")
            except Exception as e:
                print(f"Error inserting data: {e}")
    
    async def retrieve(
        self,
        query: str,
        n_retrieve: int = 10,
        filters: Optional[Dict] = None,
    ) -> List[Chunk]:
        """Retrieve similar chunks"""
        await self.initialize()
        
        # Ensure table is opened when running in a fresh process
        if self.table is None:
            try:
                self.table = self.db.open_table("chunks")
            except Exception:
                return []
        
        # Get real query embedding
        query_embedding = await self.embeddings_provider.get_query_embedding(query)
        
        try:
            # Search for similar vectors
            results = self.table.search(query_embedding).limit(n_retrieve)
            
            if filters:
                for key, value in filters.items():
                    results = results.where(f"{key} = '{value}'")
            
            # Execute the search and get results
            docs = results.to_arrow().to_pylist()
            
            chunks = []
            for row in docs:
                # 메타데이터 역직렬화
                metadata = None
                if "metadata" in row and row["metadata"]:
                    try:
                        metadata_dict = json.loads(row["metadata"])
                        metadata = ChunkMetadata(**metadata_dict)
                    except Exception as e:
                        print(f"Failed to deserialize metadata: {e}")
                
                chunk = Chunk(
                    content=row["content"],
                    start_line=row["start_line"],
                    end_line=row["end_line"],
                    filepath=row["path"],
                    index=row["index"],
                    digest=row["cachekey"],
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
        repo_name: Optional[str] = None,
    ) -> AsyncGenerator[IndexingProgressUpdate, None]:
        """Update index with new data"""
        accumulated_progress = 0
        
        if results.compute:
            filepath = results.compute[0].path # 첫 번째 파일의 경로에서 폴더명 추출
            folder_name = filepath.split("/")[-2] if "/" in filepath else "root" # 진행 상황 표시용 폴더명 설정
            
            yield IndexingProgressUpdate(
                desc=f"Chunking files in {folder_name}",
                status="indexing",
                progress=accumulated_progress,
            )
            
            # Process compute items
            for item in results.compute:
                # Read actual file content
                try:
                    file_path = Path(item.path)
                    if file_path.exists():
                        content = file_path.read_text(encoding='utf-8')
                        
                        if should_chunk(item.path, content):
                            chunks = await self.get_chunks(item, content)
                            if chunks:  # Only process if chunks were created
                                embeddings = await self.get_embeddings(chunks)
                                await self.insert_chunks(chunks, embeddings)
                                print(f"Processed {len(chunks)} chunks from {item.path}")
                    else:
                        print(f"File not found: {item.path}")
                except Exception as e:
                    import traceback
                    print(f"Error processing file {item.path}: {e}")
                    print(f"Full traceback: {traceback.format_exc()}")
            
            mark_complete(results.compute, IndexResultType.COMPUTE)
        
        # Add tag items
        for item in results.add_tag:
            # Process add_tag items
            pass
        
        # Delete items
        for item in results.delete:
            # Process delete items
            mark_complete([item], IndexResultType.DELETE)
