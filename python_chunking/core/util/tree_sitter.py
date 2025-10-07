"""
Tree-sitter utilities for parsing code files.
"""
import os
import pathlib
from typing import Optional, Dict, Any, List
import tree_sitter
from tree_sitter import Language, Parser, Node
from dataclasses import dataclass


class LanguageName:
    """Supported language names"""
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


# Supported languages mapping
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "cpp": LanguageName.CPP,
    "hpp": LanguageName.CPP,
    "cc": LanguageName.CPP,
    "cxx": LanguageName.CPP,
    "hxx": LanguageName.CPP,
    "cp": LanguageName.CPP,
    "hh": LanguageName.CPP,
    "inc": LanguageName.CPP,
    "cs": LanguageName.C_SHARP,
    "c": LanguageName.C,
    "h": LanguageName.C,
    "css": LanguageName.CSS,
    "php": LanguageName.PHP,
    "phtml": LanguageName.PHP,
    "php3": LanguageName.PHP,
    "php4": LanguageName.PHP,
    "php5": LanguageName.PHP,
    "php7": LanguageName.PHP,
    "phps": LanguageName.PHP,
    "php-s": LanguageName.PHP,
    "bash": LanguageName.BASH,
    "sh": LanguageName.BASH,
    "json": LanguageName.JSON,
    "ts": LanguageName.TYPESCRIPT,
    "mts": LanguageName.TYPESCRIPT,
    "cts": LanguageName.TYPESCRIPT,
    "tsx": LanguageName.TSX,
    "elm": LanguageName.ELM,
    "js": LanguageName.JAVASCRIPT,
    "jsx": LanguageName.JAVASCRIPT,
    "mjs": LanguageName.JAVASCRIPT,
    "cjs": LanguageName.JAVASCRIPT,
    "py": LanguageName.PYTHON,
    "pyw": LanguageName.PYTHON,
    "pyi": LanguageName.PYTHON,
    "el": LanguageName.ELISP,
    "emacs": LanguageName.ELISP,
    "ex": LanguageName.ELIXIR,
    "exs": LanguageName.ELIXIR,
    "go": LanguageName.GO,
    "eex": LanguageName.EMBEDDED_TEMPLATE,
    "heex": LanguageName.EMBEDDED_TEMPLATE,
    "leex": LanguageName.EMBEDDED_TEMPLATE,
    "html": LanguageName.HTML,
    "htm": LanguageName.HTML,
    "java": LanguageName.JAVA,
    "lua": LanguageName.LUA,
    "luau": LanguageName.LUA,
    "ocaml": LanguageName.OCAML,
    "ml": LanguageName.OCAML,
    "mli": LanguageName.OCAML,
    "ql": LanguageName.QL,
    "res": LanguageName.RESCRIPT,
    "resi": LanguageName.RESCRIPT,
    "rb": LanguageName.RUBY,
    "erb": LanguageName.RUBY,
    "rs": LanguageName.RUST,
    "rdl": LanguageName.SYSTEMRDL,
    "toml": LanguageName.TOML,
    "sol": LanguageName.SOLIDITY,
}

# Ignore path patterns for specific languages
IGNORE_PATH_PATTERNS: Dict[str, list] = {
    LanguageName.TYPESCRIPT: [r".*node_modules"],
    LanguageName.JAVASCRIPT: [r".*node_modules"],
}

# Cache for loaded languages
_name_to_language: Dict[str, Language] = {}


def get_uri_file_extension(filepath: str) -> str:
    """Extract file extension from URI path"""
    return pathlib.Path(filepath).suffix.lstrip('.')


def get_uri_path_basename(filepath: str) -> str:
    """Get basename from URI path"""
    return pathlib.Path(filepath).name


async def get_parser_for_file(filepath: str) -> Optional[Parser]:
    """Get parser for a specific file"""
    try:
        parser = Parser()
        language = await get_language_for_file(filepath)
        if not language:
            return None
        
        parser.set_language(language)
        return parser
    except Exception as e:
        print(f"Unable to load language for file {filepath}: {e}")
        return None


async def get_language_for_file(filepath: str) -> Optional[Language]:
    """Get language for a specific file"""
    try:
        extension = get_uri_file_extension(filepath)
        language_name = SUPPORTED_LANGUAGES.get(extension)
        
        if not language_name:
            return None
            
        # Check cache first
        if language_name in _name_to_language:
            return _name_to_language[language_name]
        
        # Load language
        language = await load_language_for_file_ext(extension)
        if language:
            _name_to_language[language_name] = language
        return language
    except Exception as e:
        print(f"Unable to load language for file {filepath}: {e}")
        return None


async def load_language_for_file_ext(file_extension: str) -> Optional[Language]:
    """Load language for file extension"""
    try:
        language_name = SUPPORTED_LANGUAGES.get(file_extension)
        if not language_name:
            return None
        
        # Load from built library
        build_path = pathlib.Path(__file__).parent.parent.parent / "build"
        library_path = build_path / f"languages-{language_name}.so"
        
        if library_path.exists():
            return Language(str(library_path), language_name)
        
        print(f"Tree-sitter parser for {language_name} not found. Please run build_parsers.py first.")
        return None
    except Exception as e:
        print(f"Failed to load language for extension {file_extension}: {e}")
        return None


def get_full_language_name(filepath: str) -> Optional[str]:
    """Get full language name for filepath"""
    extension = get_uri_file_extension(filepath)
    return SUPPORTED_LANGUAGES.get(extension)


# Node types for symbol extraction
GET_SYMBOLS_FOR_NODE_TYPES = [
    "class_declaration",
    "class_definition", 
    "function_item",
    "function_definition",
    "method_declaration",
    "method_definition",
    "generator_function_declaration",
]


@dataclass
class SymbolWithRange:
    """Symbol with range information"""
    filepath: str
    type: str
    name: str
    range: Dict[str, Any]
    content: str


async def get_symbols_for_file(filepath: str, contents: str) -> Optional[List[SymbolWithRange]]:
    """Get symbols for a file"""
    parser = await get_parser_for_file(filepath)
    if not parser:
        return None
    
    try:
        tree = parser.parse(bytes(contents, "utf8"))
    except Exception as e:
        print(f"Error parsing file: {filepath}")
        return None
    
    symbols = []
    
    def find_named_nodes_recursive(node: Node):
        if node.type in GET_SYMBOLS_FOR_NODE_TYPES:
            # Find the last identifier in the node
            identifier = None
            for child in reversed(node.children):
                if child.type in ["identifier", "property_identifier"]:
                    identifier = child
                    break
            
            if identifier and identifier.text:
                symbols.append(SymbolWithRange(
                    filepath=filepath,
                    type=node.type,
                    name=identifier.text.decode('utf8'),
                    range={
                        "start": {
                            "character": node.start_point[1],
                            "line": node.start_point[0],
                        },
                        "end": {
                            "character": node.end_point[1] + 1,
                            "line": node.end_point[0] + 1,
                        },
                    },
                    content=node.text.decode('utf8'),
                ))
        
        for child in node.children:
            find_named_nodes_recursive(child)
    
    find_named_nodes_recursive(tree.root_node)
    return symbols
