"""
Core index types and interfaces for the Python chunking system.
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum


class IndexTag(Enum):
    """Index tag types"""
    BRANCH = "branch"
    DIR = "dir"


@dataclass
class Chunk:
    """Represents a code chunk with metadata"""
    content: str
    start_line: int
    end_line: int
    filepath: str
    index: int
    digest: str     # 동일한 소스코드 파일에서 청킹된 각 chunk의 digest는 모두 동일 (파일 식별 목적, 청크별 차이 없음)


@dataclass
class ChunkWithoutID:
    """Represents a chunk without ID for internal processing"""
    content: str
    start_line: int
    end_line: int


@dataclass
class BranchAndDir:
    """Represents branch and directory information"""
    branch: str
    dir: str


@dataclass
class IndexingProgressUpdate:
    """Progress update for indexing operations"""
    desc: str
    status: str
    progress: float


class IndexResultType(Enum):
    """Index result types"""
    COMPUTE = "compute"
    ADD_TAG = "add_tag"
    DELETE = "delete"


@dataclass
class PathAndCacheKey:
    """Represents a file path with cache key"""
    path: str
    cache_key: str


@dataclass
class RefreshIndexResults:
    """Results from index refresh operation"""
    compute: List[PathAndCacheKey]
    add_tag: List[PathAndCacheKey]
    delete: List[PathAndCacheKey]


@dataclass
class RetrieveConfig:
    """Configuration for retrieval operations"""
    query: str
    n_retrieve: int = 10
    bm25_threshold: Optional[float] = None


class ILLM:
    """Interface for LLM operations"""
    def __init__(self, max_embedding_chunk_size: int = 1000):
        self.max_embedding_chunk_size = max_embedding_chunk_size


class MarkCompleteCallback:
    """Callback for marking operations as complete"""
    def __call__(self, items: List[PathAndCacheKey], result_type: IndexResultType):
        pass
