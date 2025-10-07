"""
Build Tree-sitter parsers for Python, JavaScript, and Java
"""
import os
import subprocess
from pathlib import Path
from tree_sitter import Language


def build_language(parser_dir: Path, language_name: str) -> Language:
    """Build a Tree-sitter language from source"""
    print(f"Building {language_name} parser...")
    
    # Build the parser
    Language.build_library(
        f"build/languages-{language_name}.so",
        [str(parser_dir)]
    )
    
    # Load and return the language
    return Language(f"build/languages-{language_name}.so", language_name)


def main():
    """Build all parsers"""
    vendor_dir = Path(__file__).parent / "vendor"
    build_dir = Path(__file__).parent / "build"
    build_dir.mkdir(exist_ok=True)
    
    parsers = [
        ("tree-sitter-python", "python"),
        ("tree-sitter-javascript", "javascript"), 
        ("tree-sitter-java", "java"),
    ]
    
    for parser_dir_name, language_name in parsers:
        parser_dir = vendor_dir / parser_dir_name
        if parser_dir.exists():
            try:
                language = build_language(parser_dir, language_name)
                print(f"✓ Successfully built {language_name} parser")
            except Exception as e:
                print(f"✗ Failed to build {language_name} parser: {e}")
        else:
            print(f"✗ Parser directory not found: {parser_dir}")
    
    print("Parser building complete!")


if __name__ == "__main__":
    main()
