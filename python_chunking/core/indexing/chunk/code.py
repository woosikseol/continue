"""
Code chunker using Tree-sitter for structured code parsing.
"""
from typing import AsyncGenerator, Dict, Callable, Optional
from tree_sitter import Node
from dataclasses import dataclass
from core.index import ChunkWithoutID
from core.llm.count_tokens import count_tokens_async
from core.util.tree_sitter import get_parser_for_file


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


async def collapse_children(
    node: Node,
    code: str,
    block_types: list,
    collapse_types: list,
    collapse_block_types: list,
    max_chunk_size: int,
) -> str:
    """Collapse children nodes to fit within chunk size"""
    code = code[:node.end_byte]
    block = first_child(node, block_types)
    collapsed_children = []
    
    if block:
        children_to_collapse = [
            child for child in block.children 
            if child.type in collapse_types
        ]
        
        for child in reversed(children_to_collapse):
            grand_child = first_child(child, collapse_block_types)
            if grand_child:
                start = grand_child.start_byte
                end = grand_child.end_byte
                collapsed_child = (
                    code[child.start_byte:start] +
                    collapsed_replacement(grand_child)
                )
                code = (
                    code[:start] +
                    collapsed_replacement(grand_child) +
                    code[end:]
                )
                collapsed_children.insert(0, collapsed_child)
    
    code = code[node.start_byte:]
    removed_child = False
    
    while (
        await count_tokens_async(code.strip()) > max_chunk_size and
        collapsed_children
    ):
        removed_child = True
        # Remove children starting at the end
        child_code = collapsed_children.pop()
        index = code.rfind(child_code)
        if index > 0:
            code = code[:index] + code[index + len(child_code):]
    
    if removed_child:
        # Remove extra blank lines
        lines = code.split("\n")
        lines = [line for line in lines if line.strip()]
        code = "\n".join(lines)
    
    return code


async def construct_class_definition_chunk(
    node: Node,
    code: str,
    max_chunk_size: int,
) -> str:
    """Construct chunk for class definition"""
    collapsed_body = await collapse_children(
        node,
        code,
        ["class_body", "declaration_list"],
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


# Node constructors for different node types
COLLAPSED_NODE_CONSTRUCTORS: Dict[str, Callable] = {
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

# 클래스 타입만 별도로 정의
CLASS_NODE_TYPES = {
    "class_definition",
    "class_declaration",
    "impl_item",
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
) -> AsyncGenerator[ChunkWithoutID, None]:
    """Get smart collapsed chunks for a node"""
    
    # 현재 구현에서는 source_file type 에 해당하는 root 노드는 Collapse 처리하지 않음
    
    # 클래스 노드는 항상 축소 청크 생성 + 자식 재귀
    # 이를 통해 일관성 있는 메타데이터 추출 가능
    if node.type in CLASS_NODE_TYPES:
        # 1. 축소된 요약 청크 생성 (크기와 무관하게 항상 실행)
        collapsed_content = await COLLAPSED_NODE_CONSTRUCTORS[node.type](
            node, code, max_chunk_size
        )
        yield ChunkWithoutID(
            content=collapsed_content,
            start_line=node.start_point[0],
            end_line=node.end_point[0],
        )
        
        # 2. 자식 노드로 재귀 (크기와 무관하게 항상 실행)
        # 각 메서드를 개별 청크로 생성
        for child in node.children:
            async for child_chunk in get_smart_collapsed_chunks(
                child, code, max_chunk_size, False
            ):
                yield child_chunk
        return
    
    # 함수/메서드 등 일반 노드: 토큰 수에 따라 처리
    chunk = await maybe_yield_chunk(node, code, max_chunk_size, root)
    if chunk:
        # 토큰 수가 한도 이하 → 노드 전체를 청크로 채택
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
            )
        
        # 자식 노드로 재귀
        for child in node.children:
            async for child_chunk in get_smart_collapsed_chunks(
                child, code, max_chunk_size, False
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
        tree.root_node, contents, max_chunk_size
    ):
        yield chunk

# node.type          # 노드 타입 (예: "module", "class_declaration", "function_definition")
# node.text          # 노드의 원본 텍스트 (bytes)

# node.start_point   # 시작 위치 (행, 열) 튜플
# node.end_point     # 끝 위치 (행, 열) 튜플

# node.parent        # 부모 노드
# node.children      # 자식 노드들의 리스트
# node.named_children # 의미있는 자식 노드들만 (토큰 제외)
