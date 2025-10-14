"""
Main chunking logic that coordinates between code and basic chunkers.
"""
from typing import AsyncGenerator
from core.index import Chunk, ChunkWithoutID
from core.llm.count_tokens import count_tokens_async
from core.util.tree_sitter import SUPPORTED_LANGUAGES
from core.util.uri import get_uri_file_extension, get_uri_path_basename
from .basic import basic_chunker
from .code import code_chunker


# Files that should use basicChunker despite having tree-sitter support
NON_CODE_EXTENSIONS = [
    "css",
    "html", 
    "htm",
    "json",
    "toml",
    "yaml",
    "yml",
]


async def chunk_document_without_id(
    file_uri: str,
    contents: str,
    max_chunk_size: int,
) -> AsyncGenerator[ChunkWithoutID, None]:
    """Chunk document without ID"""
    if contents.strip() == "":
        return
    
    extension = get_uri_file_extension(file_uri)
    
    if (
        extension in SUPPORTED_LANGUAGES and
        extension not in NON_CODE_EXTENSIONS
    ):
        try:
            async for chunk in code_chunker(file_uri, contents, max_chunk_size):
                yield chunk
            return
        except Exception as e:
            print(f"Code chunker failed, falling back to basic chunker: {e}")
            # Falls back to basic_chunker
    
    async for chunk in basic_chunker(contents, max_chunk_size, file_uri):
        yield chunk


async def chunk_document(
    filepath: str,
    contents: str,
    max_chunk_size: int,
    digest: str,
) -> AsyncGenerator[Chunk, None]:
    """Main chunk document function"""
    from .metadata import extract_metadata_from_node
    
    index = 0
    
    async for chunk_without_id in chunk_document_without_id(
        filepath, contents, max_chunk_size
    ):
        content = chunk_without_id.content
        
        # Check token count
        token_count = await count_tokens_async(content)
        if token_count > max_chunk_size:
            # 모든 청크는 토큰 초과 시 자동 축소
            symbol_info = ""
            if chunk_without_id.node:
                from .metadata import SYMBOL_TYPE_MAPPING, extract_symbol_name
                if chunk_without_id.node.type in SYMBOL_TYPE_MAPPING:
                    symbol_type = SYMBOL_TYPE_MAPPING[chunk_without_id.node.type]
                    symbol_name = extract_symbol_name(chunk_without_id.node)
                    symbol_info = f" ({symbol_type}"
                    if symbol_name:
                        symbol_info += f": {symbol_name}"
                    symbol_info += ")"
            
            print(f"Chunk exceeds token limit, collapsing{symbol_info}: {filepath}")
            
            # 토큰이 맞을 때까지 뒷부분을 잘라내고 "..." 추가
            lines = content.split('\n')
            collapsed_content = ""
            
            for i, line in enumerate(lines):
                test_content = collapsed_content + line + '\n'
                if await count_tokens_async(test_content + "\n...") > max_chunk_size:
                    # 더 이상 추가할 수 없으면 중단
                    collapsed_content += "\n..."
                    break
                collapsed_content = test_content
            
            content = collapsed_content.strip()
        
        # 통합 메타데이터 추출
        metadata = None
        if chunk_without_id.node and chunk_without_id.root_node:
            # code_chunker를 사용한 경우: 완전한 메타데이터 추출
            metadata = extract_metadata_from_node(
                chunk_without_id.node,
                content,
                chunk_without_id.root_node,
                chunk_without_id.language,
                chunk_without_id.filepath,
            )
        elif chunk_without_id.filepath and index == 0:
            # basic_chunker를 사용한 경우: 첫 번째 청크만 파일 레벨 메타데이터 생성
            from core.index import ChunkMetadata
            import os
            metadata = ChunkMetadata(
                symbol_type="file",
                symbol_name=os.path.basename(chunk_without_id.filepath),
            )
        
        yield Chunk(
            content=content,
            start_line=chunk_without_id.start_line,
            end_line=chunk_without_id.end_line,
            filepath=filepath,
            index=index,
            digest=digest,
            metadata=metadata,
        )
        index += 1


def should_chunk(file_uri: str, contents: str) -> bool:
    """Check if file should be chunked"""
    if len(contents) > 1000000:  # 1M characters
        return False
    if len(contents) == 0:
        return False
    
    base_name = get_uri_path_basename(file_uri)
    return "." in base_name
