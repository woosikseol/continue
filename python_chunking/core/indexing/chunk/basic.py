"""
Basic chunker for non-code files.
"""
from typing import AsyncGenerator
from core.index import ChunkWithoutID
from core.llm.count_tokens import count_tokens_async


async def basic_chunker(
    contents: str,
    max_chunk_size: int,
    filepath: str = "",
) -> AsyncGenerator[ChunkWithoutID, None]:
    """Basic chunker for non-code files"""
    if contents.strip() == "":
        return
    
    chunk_content = ""
    chunk_tokens = 0
    start_line = 0
    curr_line = 0
    
    # Count tokens for each line
    lines = contents.split("\n")
    line_tokens = []
    for line in lines:
        token_count = await count_tokens_async(line)
        line_tokens.append({
            "line": line,
            "token_count": token_count
        })
    
    for lt in line_tokens:
        if chunk_tokens + lt["token_count"] > max_chunk_size - 5:
            yield ChunkWithoutID(
                content=chunk_content,
                start_line=start_line,
                end_line=curr_line - 1,
                filepath=filepath,
            )
            chunk_content = ""
            chunk_tokens = 0
            start_line = curr_line
        
        if lt["token_count"] < max_chunk_size:
            chunk_content += f"{lt['line']}\n"
            chunk_tokens += lt["token_count"] + 1
        
        curr_line += 1
    
    yield ChunkWithoutID(
        content=chunk_content,
        start_line=start_line,
        end_line=curr_line - 1,
        filepath=filepath,
    )
