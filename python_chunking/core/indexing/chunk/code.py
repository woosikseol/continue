"""
Code chunker using Tree-sitter for structured code parsing.
"""
from typing import AsyncGenerator, Dict, Callable, Optional
from tree_sitter import Node
from dataclasses import dataclass
from core.index import ChunkWithoutID
from core.llm.count_tokens import count_tokens_async
from core.util.tree_sitter import get_parser_for_file
from .metadata import get_language_from_filepath


def collapsed_replacement(node: Node) -> str:
    """Get collapsed replacement text for a node"""
    if node.type == "statement_block":
        return "{ ... }"
    return "..."


def first_child(node: Node, grammar_names: list) -> Optional[Node]:
    """Find first child with matching grammar name"""
    for child in node.children:
        if child.type in grammar_names:
            return child
    return None


def extract_node_text(node: Node, code: str) -> str:
    """Extract text content of a node"""
    return code[node.start_byte:node.end_byte]


def get_signature_text(node: Node, code: str) -> str:
    """
    Extract the signature of a function/method (everything before the body block).
    For example: 'async def initialize(self):'
    
    Handles multi-line signatures properly.
    """
    # 본문 블록을 찾아서 그 이전까지가 시그니처
    block = first_child(node, ["block", "statement_block"])
    if block:
        # 시그니처는 노드 시작부터 블록 시작 직전까지
        signature_end = block.start_byte
        signature = code[node.start_byte:signature_end]
        
        # ':' 이후의 공백/개행 제거
        if ':' in signature:
            colon_idx = signature.rfind(':')
            signature = signature[:colon_idx + 1]
        
        return signature.rstrip()
    
    # 블록이 없으면 전체를 반환
    return extract_node_text(node, code)


async def collapse_children(
    node: Node,
    code: str,
    block_types: list,
    collapse_types: list,
    collapse_block_types: list,
    max_chunk_size: int,
) -> str:
    """Collapse children nodes to fit within chunk size
    
    메서드를 간단한 한 줄 형태로 축소합니다: 'def method(...): ...'
    깔끔하고 읽기 쉬우며, 모든 메서드를 한눈에 볼 수 있습니다.
    """
    block = first_child(node, block_types)
    
    if not block:
        return code[node.start_byte:node.end_byte]
    
    children_to_collapse = [
        child for child in block.children 
        if child.type in collapse_types
    ]
    
    if not children_to_collapse:
        return code[node.start_byte:node.end_byte]
    
    # 클래스/파일의 시작 부분 (첫 메서드 전까지)
    first_child_start = children_to_collapse[0].start_byte
    
    # 메서드 앞의 들여쓰기 포함하여 시작 위치 조정
    while first_child_start > node.start_byte and code[first_child_start - 1] in ' \t':
        first_child_start -= 1
    
    # 줄 시작으로 이동 (개행 문자 포함)
    while first_child_start > node.start_byte and code[first_child_start - 1] != '\n':
        first_child_start -= 1
    
    preamble = code[node.start_byte:first_child_start].rstrip()
    
    result_lines = [preamble, '']
    
    # 각 메서드를 한 줄로 축소
    processed_methods = set()  # 중복 방지
    
    for child in children_to_collapse:
        # 메서드 앞의 들여쓰기 포함하여 추출
        # Tree-sitter는 들여쓰기를 포함하지 않으므로, 앞쪽으로 확장
        child_start = child.start_byte
        
        # 1. 먼저 줄 시작으로 이동 (개행 문자 바로 다음)
        while (child_start > node.start_byte and 
               child_start > 0 and 
               child_start - 1 < len(code) and 
               code[child_start - 1] != '\n'):
            child_start -= 1
        
        # 2. 현재 줄 확인
        line_end_pos = child_start
        while (line_end_pos < child.end_byte and 
               line_end_pos < len(code) and 
               code[line_end_pos] != '\n'):
            line_end_pos += 1
        
        current_line = code[child_start:line_end_pos].strip()
        
        # 3. 현재 줄이 def/async def로 시작하지 않으면 역방향 검색
        if not (current_line.startswith('def ') or current_line.startswith('async def ')):
            # 역방향으로 def/async def 찾기
            search_start = child_start
            found_def = False
            
            # 최대 10줄 역방향 검색
            for _ in range(10):
                if search_start <= node.start_byte:
                    break
                
                # 이전 줄로 이동
                search_start -= 1  # 개행 문자 건너뛰기
                while (search_start > node.start_byte and 
                       search_start > 0 and 
                       search_start - 1 < len(code) and 
                       code[search_start - 1] != '\n'):
                    search_start -= 1
                
                # 이 줄 확인
                line_end = search_start
                while (line_end < child.end_byte and 
                       line_end < len(code) and 
                       code[line_end] != '\n'):
                    line_end += 1
                
                line_text = code[search_start:line_end].strip()
                
                if line_text.startswith('def ') or line_text.startswith('async def '):
                    child_start = search_start
                    found_def = True
                    break
            
            if not found_def:
                continue
        
        # 중복 확인
        if child_start in processed_methods:
            continue
        processed_methods.add(child_start)
        
        child_text = code[child_start:child.end_byte]
        
        # 메서드 시그니처 추출 (여러 줄일 수 있음)
        # ':' 위치 찾기
        colon_idx = child_text.find(':')
        if colon_idx <= 0:
            continue
        
        # 시그니처 전체 가져오기 (: 이전까지)
        signature = child_text[:colon_idx]
        
        # 들여쓰기 추출 (첫 줄에서)
        first_line = signature.split('\n')[0]
        indent = ' ' * (len(first_line) - len(first_line.lstrip()))
        
        # 여러 줄 시그니처를 한 줄로 압축
        signature_parts = []
        for line in signature.split('\n'):
            signature_parts.append(line.strip())
        
        # 간단한 시그니처 생성
        full_sig = ' '.join(signature_parts)
        
        # 파라미터가 너무 길면 '...'로 축약
        if len(full_sig) > 60 and '(' in full_sig and ')' in full_sig:
            method_name_part = full_sig[:full_sig.find('(') + 1]
            # 파라미터 부분 확인
            params_end = full_sig.rfind(')')
            return_part = full_sig[params_end:]
            
            # 파라미터 축약
            collapsed_sig = f"{method_name_part}...{return_part}"
        else:
            collapsed_sig = full_sig
        
        # 최종 한 줄 메서드
        result_lines.append(f"{indent}{collapsed_sig}: ...")
    
    result = '\n'.join(result_lines)
    
    # 토큰 수가 초과하면 뒤에서부터 메서드 제거
    while await count_tokens_async(result) > max_chunk_size and len(result_lines) > 3:
        result_lines.pop()  # 마지막 메서드 제거
        result = '\n'.join(result_lines)
    
    return result


async def construct_class_definition_chunk(
    node: Node,
    code: str,
    max_chunk_size: int,
) -> str:
    """Construct chunk for class definition"""
    collapsed_body = await collapse_children(
        node,
        code,
        ["class_body", "declaration_list", "block"],  # Python uses "block"
        ["method_definition", "function_definition", "method_declaration"],
        ["block", "statement_block"],
        max_chunk_size,
    )
    return collapsed_body


async def construct_function_definition_chunk(
    node: Node,
    code: str,
    max_chunk_size: int,
) -> str:
    """Construct chunk for function definition"""
    collapsed_body = await collapse_children(
        node,
        code,
        ["block", "statement_block"],
        ["statement"],
        ["block", "statement_block"],
        max_chunk_size,
    )
    return collapsed_body


async def construct_root_definition_chunk(
    node: Node,
    code: str,
    max_chunk_size: int,
) -> str:
    """Construct chunk for root node (module/source_file)"""
    # 루트 노드는 최상위 정의들만 포함하는 축소 청크 생성
    collapsed_body = await collapse_children(
        node,
        code,
        ["module", "source_file", "program"],  # 루트 컨테이너
        ["class_definition", "function_definition", "class_declaration", "function_declaration"],  # 축소할 항목
        ["class_body", "block", "statement_block", "declaration_list"],  # 블록 타입
        max_chunk_size,
    )
    return collapsed_body


# Node constructors for different node types
COLLAPSED_NODE_CONSTRUCTORS: Dict[str, Callable] = {
    # Root nodes
    "module": construct_root_definition_chunk,
    "source_file": construct_root_definition_chunk,
    "program": construct_root_definition_chunk,
    # Classes, structs, etc
    "class_definition": construct_class_definition_chunk,
    "class_declaration": construct_class_definition_chunk,
    "impl_item": construct_class_definition_chunk,
    # Functions
    "function_definition": construct_function_definition_chunk,
    "function_declaration": construct_function_definition_chunk,
    "function_item": construct_function_definition_chunk,
    # Methods
    "method_declaration": construct_function_definition_chunk,
}

# 구조적 노드: 루트 + 클래스 (항상 축소 청크 생성 + 자식 재귀)
STRUCTURAL_NODE_TYPES = {
    # Root nodes
    "module",  # Python
    "source_file",  # Java, C, etc
    "program",  # JavaScript, TypeScript
    # Class nodes
    "class_definition",  # Python
    "class_declaration",  # Java, JavaScript, TypeScript
    "impl_item",  # Rust
}


async def maybe_yield_chunk(
    node: Node,
    code: str,
    max_chunk_size: int,
    root: bool = True,
) -> Optional[ChunkWithoutID]:
    """Check if node can be yielded as a chunk"""
    # Keep entire text if not over size
    if root or node.type in COLLAPSED_NODE_CONSTRUCTORS:
        token_count = await count_tokens_async(node.text.decode('utf8'))
        if token_count < max_chunk_size:
            return ChunkWithoutID(
                content=node.text.decode('utf8'),
                start_line=node.start_point[0],
                end_line=node.end_point[0],
            )
    return None


async def get_smart_collapsed_chunks(
    node: Node,
    code: str,
    max_chunk_size: int,
    root: bool = True,
    root_node: Optional[Node] = None,
    filepath: str = "",
) -> AsyncGenerator[ChunkWithoutID, None]:
    """Get smart collapsed chunks for a node"""
    
    # root_node가 None이면 현재 노드를 root_node로 사용 (초기 호출 시)
    if root_node is None:
        root_node = node
    
    # 언어 추출
    language = get_language_from_filepath(filepath)
    
    # 구조적 노드(루트/클래스)는 항상 축소 청크 생성 + 자식 재귀
    # 이를 통해 계층적 메타데이터 추출 가능
    if node.type in STRUCTURAL_NODE_TYPES:
        # 1. 축소된 요약 청크 생성 (크기와 무관하게 항상 실행)
        collapsed_content = await COLLAPSED_NODE_CONSTRUCTORS[node.type](
            node, code, max_chunk_size
        )
        
        yield ChunkWithoutID(
            content=collapsed_content,
            start_line=node.start_point[0],
            end_line=node.end_point[0],
            node=node,
            root_node=root_node,
            language=language,
            filepath=filepath,
        )
        
        # 2. 자식 노드로 재귀 (크기와 무관하게 항상 실행)
        # 각 메서드를 개별 청크로 생성
        for child in node.children:
            async for child_chunk in get_smart_collapsed_chunks(
                child, code, max_chunk_size, False, root_node, filepath
            ):
                yield child_chunk
        return
    
    # 함수/메서드 등 일반 노드: 토큰 수에 따라 처리
    chunk = await maybe_yield_chunk(node, code, max_chunk_size, root)
    if chunk:
        # 토큰 수가 한도 이하 → 노드 전체를 청크로 채택
        # 노드 정보 저장 (메타데이터는 나중에 통합 추출)
        chunk.node = node
        chunk.root_node = root_node
        chunk.language = language
        chunk.filepath = filepath
        
        yield chunk
        # 재귀하지 않음 (중복 방지)
        return
    else:
        # 토큰 수 초과 → 스마트 축소 시도
        if node.type in COLLAPSED_NODE_CONSTRUCTORS:
            # 축소 가능한 노드면 축소 시도
            collapsed_content = await COLLAPSED_NODE_CONSTRUCTORS[node.type](
                node, code, max_chunk_size
            )
            
            yield ChunkWithoutID(
                content=collapsed_content,
                start_line=node.start_point[0],
                end_line=node.end_point[0],
                node=node,
                root_node=root_node,
                language=language,
                filepath=filepath,
            )
        
        # 자식 노드로 재귀
        for child in node.children:
            async for child_chunk in get_smart_collapsed_chunks(
                child, code, max_chunk_size, False, root_node, filepath
            ):
                yield child_chunk


async def code_chunker(
    filepath: str,
    contents: str,
    max_chunk_size: int,
) -> AsyncGenerator[ChunkWithoutID, None]:
    """Main code chunker using Tree-sitter"""
    if contents.strip() == "":
        return
    
    parser = await get_parser_for_file(filepath)
    if parser is None:
        raise ValueError(f"Failed to load parser for file {filepath}")
    
    tree = parser.parse(bytes(contents, "utf8"))
    
    async for chunk in get_smart_collapsed_chunks(
        tree.root_node, contents, max_chunk_size, True, tree.root_node, filepath
    ):
        yield chunk

# node.type          # 노드 타입 (예: "module", "class_declaration", "function_definition")
# node.text          # 노드의 원본 텍스트 (bytes)

# node.start_point   # 시작 위치 (행, 열) 튜플
# node.end_point     # 끝 위치 (행, 열) 튜플

# node.parent        # 부모 노드
# node.children      # 자식 노드들의 리스트
# node.named_children # 의미있는 자식 노드들만 (토큰 제외)
