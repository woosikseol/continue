"""
Token counting utilities for LLM operations.
"""
import tiktoken
from typing import Optional


# Cache for encodings
_encoding_cache: dict = {}


def get_encoding(model: str = "gpt-3.5-turbo") -> tiktoken.Encoding:
    """Get encoding for a model"""
    if model not in _encoding_cache:
        try:
            _encoding_cache[model] = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base encoding
            _encoding_cache[model] = tiktoken.get_encoding("cl100k_base")
    return _encoding_cache[model]


async def count_tokens_async(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count tokens in text asynchronously"""
    encoding = get_encoding(model)
    return len(encoding.encode(text))


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count tokens in text synchronously"""
    encoding = get_encoding(model)
    return len(encoding.encode(text))
