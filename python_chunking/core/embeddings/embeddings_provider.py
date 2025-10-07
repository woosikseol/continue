"""
Real embeddings provider using sentence-transformers
"""
from typing import List, Optional
import numpy as np

from sentence_transformers import SentenceTransformer
SENTENCE_TRANSFORMERS_AVAILABLE = True

# try:
#     from sentence_transformers import SentenceTransformer
#     SENTENCE_TRANSFORMERS_AVAILABLE = True
# except ImportError:
#     SENTENCE_TRANSFORMERS_AVAILABLE = False
#     SentenceTransformer = None

from core.index import Chunk


class EmbeddingsProvider:
    """Real embeddings provider using sentence-transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", max_embedding_chunk_size: int = 1000):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is not available. "
                "Please install it with: pip install sentence-transformers>=2.5.0 huggingface_hub>=0.19.0,<0.25.0"
            )
        self.model_name = model_name
        self.max_embedding_chunk_size = max_embedding_chunk_size
        self._model: Optional[SentenceTransformer] = None
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the model"""
        if self._model is None:
            print(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            print("Embedding model loaded successfully")
        return self._model
    
    async def get_embeddings(self, chunks: List[Chunk]) -> List[List[float]]:
        """Get embeddings for chunks"""
        if not chunks:
            return []
        
        # Extract content from chunks
        texts = [chunk.content for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        
        # Convert to list of lists
        return [embedding.tolist() for embedding in embeddings]
    
    async def get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for a query"""
        embedding = self.model.encode([query], convert_to_tensor=False)
        return embedding[0].tolist()
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return self.model.get_sentence_embedding_dimension()
