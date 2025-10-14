"""
Core index types and interfaces for the Python chunking system.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class IndexTag(Enum):
    """Index tag types"""
    BRANCH = "branch"
    DIR = "dir"


@dataclass
class ChunkMetadata:
    """메타데이터 정보 (3단계: 고급 크로스 파일 관계 분석)"""
    # 심볼 정보
    symbol_type: Optional[str] = None  # "class", "function", "method", "variable" 등
    symbol_name: Optional[str] = None  # 심볼의 이름
    symbol_definitions: Dict[str, str] = field(default_factory=dict)  # 정의된 심볼과 위치

    # Import/Export 분석
    imports: List[str] = field(default_factory=list)  # ["numpy", "pandas", "Calculator"]
    exports: List[str] = field(default_factory=list)  # ["Calculator", "add", "subtract"]
    
    # 참조 관계
    references_to: List[str] = field(default_factory=list)  # 이 청크가 참조하는 심볼들
    referenced_by: List[str] = field(default_factory=list)  # 이 청크를 참조하는 위치들
    
    # 상속 관계
    extends: Optional[str] = None  # 상속하는 부모 클래스
    implements: List[str] = field(default_factory=list)  # 구현하는 인터페이스들
    subclasses: List[str] = field(default_factory=list)  # 이를 상속하는 자식 클래스들
    
    # 의존성 분석
    dependencies: List[str] = field(default_factory=list)  # 직접 의존하는 파일들
    dependents: List[str] = field(default_factory=list)  # 이 파일에 의존하는 파일들


@dataclass
class Chunk:
    """Represents a code chunk with metadata"""
    content: str
    start_line: int
    end_line: int
    filepath: str
    index: int
    digest: str     # 동일한 소스코드 파일에서 청킹된 각 chunk의 digest는 모두 동일 (파일 식별 목적, 청크별 차이 없음)
    metadata: Optional[ChunkMetadata] = None  # 3단계 메타데이터


@dataclass
class ChunkWithoutID:
    """Represents a chunk without ID for internal processing"""
    content: str
    start_line: int
    end_line: int
    metadata: Optional[ChunkMetadata] = None  # 3단계 메타데이터
    # 메타데이터 추출을 위한 추가 정보
    node: Optional[Any] = None  # Tree-sitter Node (메타데이터 추출용)
    root_node: Optional[Any] = None  # 파일의 루트 노드
    language: str = ""  # 프로그래밍 언어
    filepath: str = ""  # 파일 경로


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
