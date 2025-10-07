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
    
    async for chunk in basic_chunker(contents, max_chunk_size):
        yield chunk


async def chunk_document(
    filepath: str,
    contents: str,
    max_chunk_size: int,
    digest: str,
) -> AsyncGenerator[Chunk, None]:
    """Main chunk document function"""
    index = 0
    
    async for chunk_without_id in chunk_document_without_id(
        filepath, contents, max_chunk_size
    ):
        # Check token count
        token_count = await count_tokens_async(chunk_without_id.content)
        if token_count > max_chunk_size:
            print(f"Chunk with more than {max_chunk_size} tokens constructed: {filepath}")
            continue
        
        yield Chunk(
            content=chunk_without_id.content,
            start_line=chunk_without_id.start_line,
            end_line=chunk_without_id.end_line,
            filepath=filepath,
            index=index,
            digest=digest,
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
