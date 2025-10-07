"""
Simple embeddings provider without heavy dependencies
"""
from typing import List
import hashlib
import numpy as np
from core.index import Chunk


class SimpleEmbeddingsProvider:
    """Simple embeddings provider using hash-based embeddings"""
    
    def __init__(self, max_embedding_chunk_size: int = 1000):
        self.max_embedding_chunk_size = max_embedding_chunk_size
        self.embedding_dim = 384
    
    def _text_to_embedding(self, text: str) -> List[float]:
        """Convert text to a simple hash-based embedding"""
        # Create a deterministic hash-based embedding
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert bytes to normalized float values
        embedding = []
        for i in range(0, min(len(hash_bytes), self.embedding_dim // 8), 8):
            chunk = hash_bytes[i:i+8]
            # Convert 8 bytes to int and normalize
            val = int.from_bytes(chunk + b'\x00' * (8 - len(chunk)), 'big')
            # Normalize to [-1, 1] range
            normalized = (val / (2**63 - 1)) * 2 - 1
            embedding.append(normalized)
        
        # Pad or truncate to desired dimension
        while len(embedding) < self.embedding_dim:
            embedding.append(0.0)
        
        return embedding[:self.embedding_dim]
    
    async def get_embeddings(self, chunks: List[Chunk]) -> List[List[float]]:
        """Get embeddings for chunks"""
        if not chunks:
            return []
        
        embeddings = []
        for chunk in chunks:
            embedding = self._text_to_embedding(chunk.content)
            embeddings.append(embedding)
        
        return embeddings
    
    async def get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for a query"""
        return self._text_to_embedding(query)
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return self.embedding_dim
