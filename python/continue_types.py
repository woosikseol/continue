"""
Continue Python Types
원본 TypeScript index.d.ts의 Python 포팅
핵심 타입 정의들
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union, Set
from enum import Enum
import tree_sitter

class LanguageName(Enum):
    """지원하는 프로그래밍 언어 - 원본 LanguageName enum 포팅"""
    CPP = "cpp"
    C_SHARP = "c_sharp"
    C = "c"
    CSS = "css"
    PHP = "php"
    BASH = "bash"
    JSON = "json"
    TYPESCRIPT = "typescript"
    TSX = "tsx"
    ELM = "elm"
    JAVASCRIPT = "javascript"
    PYTHON = "python"
    ELISP = "elisp"
    ELIXIR = "elixir"
    GO = "go"
    EMBEDDED_TEMPLATE = "embedded_template"
    HTML = "html"
    JAVA = "java"
    LUA = "lua"
    OCAML = "ocaml"
    QL = "ql"
    RESCRIPT = "rescript"
    RUBY = "ruby"
    RUST = "rust"
    SYSTEMRDL = "systemrdl"
    TOML = "toml"
    SOLIDITY = "solidity"

# 파일 확장자와 언어 매핑 - 원본 supportedLanguages 포팅
SUPPORTED_LANGUAGES = {
    'cpp': LanguageName.CPP,
    'hpp': LanguageName.CPP,
    'cc': LanguageName.CPP,
    'cxx': LanguageName.CPP,
    'hxx': LanguageName.CPP,
    'cp': LanguageName.CPP,
    'hh': LanguageName.CPP,
    'inc': LanguageName.CPP,
    'cs': LanguageName.C_SHARP,
    'c': LanguageName.C,
    'h': LanguageName.C,
    'css': LanguageName.CSS,
    'php': LanguageName.PHP,
    'phtml': LanguageName.PHP,
    'php3': LanguageName.PHP,
    'php4': LanguageName.PHP,
    'php5': LanguageName.PHP,
    'php7': LanguageName.PHP,
    'phps': LanguageName.PHP,
    'php-s': LanguageName.PHP,
    'bash': LanguageName.BASH,
    'sh': LanguageName.BASH,
    'json': LanguageName.JSON,
    'ts': LanguageName.TYPESCRIPT,
    'mts': LanguageName.TYPESCRIPT,
    'cts': LanguageName.TYPESCRIPT,
    'tsx': LanguageName.TSX,
    'elm': LanguageName.ELM,
    'js': LanguageName.JAVASCRIPT,
    'jsx': LanguageName.JAVASCRIPT,
    'mjs': LanguageName.JAVASCRIPT,
    'cjs': LanguageName.JAVASCRIPT,
    'py': LanguageName.PYTHON,
    'pyw': LanguageName.PYTHON,
    'pyi': LanguageName.PYTHON,
    'el': LanguageName.ELISP,
    'emacs': LanguageName.ELISP,
    'ex': LanguageName.ELIXIR,
    'exs': LanguageName.ELIXIR,
    'go': LanguageName.GO,
    'eex': LanguageName.EMBEDDED_TEMPLATE,
    'heex': LanguageName.EMBEDDED_TEMPLATE,
    'leex': LanguageName.EMBEDDED_TEMPLATE,
    'html': LanguageName.HTML,
    'htm': LanguageName.HTML,
    'java': LanguageName.JAVA,
    'lua': LanguageName.LUA,
    'luau': LanguageName.LUA,
    'ocaml': LanguageName.OCAML,
    'ml': LanguageName.OCAML,
    'mli': LanguageName.OCAML,
    'ql': LanguageName.QL,
    'res': LanguageName.RESCRIPT,
    'resi': LanguageName.RESCRIPT,
    'rb': LanguageName.RUBY,
    'erb': LanguageName.RUBY,
    'rs': LanguageName.RUST,
    'rdl': LanguageName.SYSTEMRDL,
    'toml': LanguageName.TOML,
    'sol': LanguageName.SOLIDITY,
}

@dataclass
class Position:
    """위치 정보 - 원본 Position 인터페이스 포팅"""
    line: int
    character: int

@dataclass
class Range:
    """범위 정보 - 원본 Range 인터페이스 포팅"""
    start: Position
    end: Position

@dataclass
class RangeInFile:
    """파일 내 범위 - 원본 RangeInFile 인터페이스 포팅"""
    filepath: str
    range: Range

@dataclass
class RangeInFileWithContents:
    """내용이 포함된 파일 내 범위 - 원본 RangeInFileWithContents 인터페이스 포팅"""
    filepath: str
    range: Range
    contents: str

@dataclass
class SymbolWithRange:
    """심볼과 범위 정보 - 원본 SymbolWithRange 인터페이스 포팅"""
    filepath: str
    type: str
    name: str
    range: Range
    content: str

@dataclass
class ChunkWithoutID:
    """ID 없는 청크 - 원본 ChunkWithoutID 인터페이스 포팅"""
    content: str
    start_line: int
    end_line: int
    signature: Optional[str] = None
    other_metadata: Optional[Dict[str, Any]] = None

@dataclass
class Chunk:
    """청크 - 원본 Chunk 인터페이스 포팅"""
    content: str
    start_line: int
    end_line: int
    digest: str
    filepath: str
    index: int
    signature: Optional[str] = None
    other_metadata: Optional[Dict[str, Any]] = None

@dataclass
class ContextItem:
    """컨텍스트 아이템 - 원본 ContextItem 인터페이스 포팅"""
    content: str
    name: str
    description: str
    editing: Optional[bool] = None
    editable: Optional[bool] = None
    icon: Optional[str] = None
    uri: Optional[Dict[str, str]] = None
    hidden: Optional[bool] = None

@dataclass
class ContextItemId:
    """컨텍스트 아이템 ID - 원본 ContextItemId 인터페이스 포팅"""
    provider_title: str
    item_id: str

@dataclass
class ContextItemWithId:
    """ID가 있는 컨텍스트 아이템 - 원본 ContextItemWithId 인터페이스 포팅"""
    content: str
    name: str
    description: str
    id: ContextItemId
    editing: Optional[bool] = None
    editable: Optional[bool] = None
    icon: Optional[str] = None
    uri: Optional[Dict[str, str]] = None
    hidden: Optional[bool] = None

@dataclass
class ChatMessage:
    """채팅 메시지 - 원본 ChatMessage 타입 포팅"""
    role: str  # "user" | "assistant" | "system" | "tool"
    content: Union[str, List[Dict[str, Any]]]

@dataclass
class CompletionOptions:
    """완성 옵션 - 원본 CompletionOptions 인터페이스 포팅"""
    model: str
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    stop: Optional[List[str]] = None

@dataclass
class LLMOptions:
    """LLM 옵션 - 원본 LLMOptions 인터페이스 포팅"""
    model: str
    title: Optional[str] = None
    unique_id: Optional[str] = None
    system_message: Optional[str] = None
    context_length: Optional[int] = None
    completion_options: Optional[CompletionOptions] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    embedding_id: Optional[str] = None
    max_embedding_chunk_size: Optional[int] = None
    max_embedding_batch_size: Optional[int] = None

@dataclass
class IDE:
    """IDE 인터페이스 - 원본 IDE 인터페이스 포팅"""
    async def read_file(self, filepath: str) -> str:
        """파일 읽기"""
        pass
    
    async def write_file(self, filepath: str, contents: str) -> None:
        """파일 쓰기"""
        pass
    
    async def get_workspace_dirs(self) -> List[str]:
        """워크스페이스 디렉토리들 반환"""
        pass
    
    async def get_open_files(self) -> List[str]:
        """열린 파일들 반환"""
        pass

@dataclass
class AstPath:
    """AST 경로 - 원본 AstPath 타입 포팅"""
    nodes: List[tree_sitter.Node]

# 파일 심볼 맵 - 원본 FileSymbolMap 타입 포팅
FileSymbolMap = Dict[str, List[SymbolWithRange]]

# LSP 정의 함수 타입 - 원본 GetLspDefinitionsFunction 타입 포팅
GetLspDefinitionsFunction = Any  # 실제 구현에서 구체화

# 인덱싱 진행 상태 - 원본 IndexingProgressUpdate 인터페이스 포팅
@dataclass
class IndexingProgressUpdate:
    progress: float
    desc: str
    should_clear_indexes: Optional[bool] = None
    status: str = "loading"  # "loading" | "indexing" | "done" | "failed" | "paused" | "disabled" | "cancelled"
    debug_info: Optional[str] = None
    warnings: Optional[List[str]] = None

# 인덱싱 상태 - 원본 IndexingStatus 인터페이스 포팅
@dataclass
class IndexingStatus:
    id: str
    type: str  # "docs"
    progress: float
    description: str
    status: str  # "indexing" | "complete" | "paused" | "failed" | "aborted" | "pending"
    embeddings_provider_id: Optional[str] = None
    is_reindexing: Optional[bool] = None
    debug_info: Optional[str] = None
    title: str = ""
    icon: Optional[str] = None
    url: Optional[str] = None
