"""
URI utility functions.
"""
import pathlib


def get_uri_file_extension(filepath: str) -> str:
    """Extract file extension from URI path"""
    return pathlib.Path(filepath).suffix.lstrip('.')


def get_uri_path_basename(filepath: str) -> str:
    """Get basename from URI path"""
    return pathlib.Path(filepath).name
