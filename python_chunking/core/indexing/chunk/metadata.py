"""
메타데이터 추출 모듈 (3단계: 고급 크로스 파일 관계 분석)
Tree-sitter AST 노드에서 심볼, import/export, 상속, 참조 관계 등을 추출합니다.
"""
from typing import Optional, List, Dict, Set
from tree_sitter import Node
from core.index import ChunkMetadata


# 언어별 심볼 타입 매핑
SYMBOL_TYPE_MAPPING = {
    # Root nodes
    "module": "file",  # Python
    "source_file": "file",  # Java, C, etc
    "program": "file",  # JavaScript, TypeScript
    
    # Python
    "class_definition": "class",
    "function_definition": "function",
    "decorated_definition": "function",  # @decorator가 붙은 함수/클래스
    
    # JavaScript/TypeScript
    "class_declaration": "class",
    "function_declaration": "function",
    "method_definition": "method",
    "arrow_function": "function",
    
    # Java
    "class_declaration": "class",
    "interface_declaration": "interface",
    "method_declaration": "method",
    
    # Rust
    "impl_item": "class",
    "function_item": "function",
    "struct_item": "struct",
    "trait_item": "trait",
}


def extract_node_text(node: Optional[Node]) -> Optional[str]:
    """노드의 텍스트를 추출합니다."""
    if node is None:
        return None
    try:
        return node.text.decode('utf8')
    except:
        return None


def find_child_by_type(node: Node, type_name: str) -> Optional[Node]:
    """특정 타입의 첫 번째 자식 노드를 찾습니다."""
    for child in node.children:
        if child.type == type_name:
            return child
    return None


def find_children_by_type(node: Node, type_name: str) -> List[Node]:
    """특정 타입의 모든 자식 노드를 찾습니다."""
    return [child for child in node.children if child.type == type_name]


def extract_symbol_name(node: Node) -> Optional[str]:
    """노드에서 심볼 이름을 추출합니다."""
    # 일반적인 이름 필드들
    name_types = ["identifier", "name", "type_identifier"]
    
    for name_type in name_types:
        name_node = find_child_by_type(node, name_type)
        if name_node:
            return extract_node_text(name_node)
    
    # 자식 중에서 찾기
    for child in node.children:
        if child.type in name_types:
            return extract_node_text(child)
    
    return None


def extract_imports_python(root_node: Node) -> List[str]:
    """Python import 문을 추출합니다."""
    imports = []
    
    def traverse(node: Node):
        if node.type == "import_statement":
            # import numpy, pandas
            for child in node.children:
                if child.type == "dotted_name" or child.type == "identifier":
                    module_name = extract_node_text(child)
                    if module_name:
                        imports.append(module_name)
        
        elif node.type == "import_from_statement":
            # from calculator import Calculator
            module_node = find_child_by_type(node, "dotted_name")
            if not module_node:
                module_node = find_child_by_type(node, "relative_import")
            if module_node:
                module_name = extract_node_text(module_node)
                if module_name:
                    imports.append(module_name)
        
        for child in node.children:
            traverse(child)
    
    traverse(root_node)
    return imports


def extract_imports_javascript(root_node: Node) -> List[str]:
    """JavaScript/TypeScript import 문을 추출합니다."""
    imports = []
    
    def traverse(node: Node):
        if node.type == "import_statement":
            # import Calculator from './Calculator'
            string_node = find_child_by_type(node, "string")
            if string_node:
                import_path = extract_node_text(string_node)
                if import_path:
                    # 따옴표 제거
                    import_path = import_path.strip('"\'')
                    imports.append(import_path)
        
        for child in node.children:
            traverse(child)
    
    traverse(root_node)
    return imports


def extract_imports_java(root_node: Node) -> List[str]:
    """Java import 문을 추출합니다."""
    imports = []
    
    def traverse(node: Node):
        if node.type == "import_declaration":
            # import java.util.ArrayList;
            for child in node.children:
                if child.type == "scoped_identifier" or child.type == "identifier":
                    import_name = extract_node_text(child)
                    if import_name:
                        imports.append(import_name)
        
        for child in node.children:
            traverse(child)
    
    traverse(root_node)
    return imports


def extract_imports(root_node: Node, language: str) -> List[str]:
    """언어별 import를 추출합니다."""
    if language == "python":
        return extract_imports_python(root_node)
    elif language in ["javascript", "typescript", "tsx", "jsx"]:
        return extract_imports_javascript(root_node)
    elif language == "java":
        return extract_imports_java(root_node)
    # 다른 언어는 추후 확장
    return []


def extract_exports_python(root_node: Node) -> List[str]:
    """Python에서 export되는 심볼들을 추출합니다 (클래스, 함수 등)."""
    exports = []
    
    # 최상위 레벨의 클래스와 함수를 export로 간주
    for child in root_node.children:
        if child.type in ["class_definition", "function_definition"]:
            name = extract_symbol_name(child)
            if name:
                exports.append(name)
    
    return exports


def extract_exports_javascript(root_node: Node) -> List[str]:
    """JavaScript/TypeScript export 문을 추출합니다."""
    exports = []
    
    def traverse(node: Node):
        if node.type == "export_statement":
            # export class Calculator
            for child in node.children:
                if child.type in ["class_declaration", "function_declaration"]:
                    name = extract_symbol_name(child)
                    if name:
                        exports.append(name)
        
        for child in node.children:
            traverse(child)
    
    traverse(root_node)
    return exports


def extract_exports(root_node: Node, language: str) -> List[str]:
    """언어별 export를 추출합니다."""
    if language == "python":
        return extract_exports_python(root_node)
    elif language in ["javascript", "typescript", "tsx", "jsx"]:
        return extract_exports_javascript(root_node)
    # Java는 public 클래스가 export
    elif language == "java":
        exports = []
        for child in root_node.children:
            if child.type == "class_declaration":
                # public 키워드 확인
                modifiers = find_child_by_type(child, "modifiers")
                if modifiers:
                    mod_text = extract_node_text(modifiers)
                    if mod_text and "public" in mod_text:
                        name = extract_symbol_name(child)
                        if name:
                            exports.append(name)
        return exports
    return []


def extract_parent_class(node: Node) -> Optional[str]:
    """클래스의 부모 클래스를 추출합니다."""
    # Python: class Child(Parent):
    if node.type == "class_definition":
        argument_list = find_child_by_type(node, "argument_list")
        if argument_list and len(argument_list.children) > 0:
            for child in argument_list.children:
                if child.type == "identifier":
                    return extract_node_text(child)
    
    # Java/JavaScript: class Child extends Parent
    if node.type == "class_declaration":
        # superclass 또는 extends_clause 찾기
        extends_node = find_child_by_type(node, "superclass")
        if not extends_node:
            extends_node = find_child_by_type(node, "extends_clause")
        
        if extends_node:
            # 타입 식별자 찾기
            type_id = find_child_by_type(extends_node, "type_identifier")
            if not type_id:
                type_id = find_child_by_type(extends_node, "identifier")
            if type_id:
                return extract_node_text(type_id)
    
    return None


def extract_interfaces(node: Node) -> List[str]:
    """클래스가 구현하는 인터페이스들을 추출합니다."""
    interfaces = []
    
    # Java: class MyClass implements Interface1, Interface2
    if node.type == "class_declaration":
        super_interfaces = find_child_by_type(node, "super_interfaces")
        if super_interfaces:
            type_list = find_child_by_type(super_interfaces, "type_list")
            if type_list:
                for child in type_list.children:
                    if child.type == "type_identifier":
                        interface_name = extract_node_text(child)
                        if interface_name:
                            interfaces.append(interface_name)
    
    return interfaces


def extract_references(node: Node, content: str) -> List[str]:
    """노드 내에서 참조하는 심볼들을 추출합니다."""
    references = set()
    
    def traverse(n: Node):
        # 함수 호출, 변수 참조 등
        if n.type in ["call", "call_expression"]:
            # 함수 이름 찾기
            func_node = None
            for child in n.children:
                if child.type in ["identifier", "attribute"]:
                    func_node = child
                    break
            
            if func_node:
                func_name = extract_node_text(func_node)
                if func_name:
                    references.add(func_name)
        
        # 속성 접근 (self.method, obj.property)
        elif n.type == "attribute":
            attr_name = None
            for child in n.children:
                if child.type == "identifier" and child != n.children[0]:
                    attr_name = extract_node_text(child)
                    break
            if attr_name:
                references.add(attr_name)
        
        for child in n.children:
            traverse(child)
    
    traverse(node)
    return list(references)


def extract_symbol_definitions(node: Node) -> Dict[str, str]:
    """노드 내에서 정의된 심볼들을 추출합니다."""
    definitions = {}
    
    for child in node.children:
        # 함수나 메서드 정의
        if child.type in ["function_definition", "method_definition", "method_declaration"]:
            name = extract_symbol_name(child)
            if name:
                location = f"line:{child.start_point[0]}"
                definitions[name] = location
    
    return definitions


def extract_metadata_from_node(
    node: Node,
    content: str,
    root_node: Node,
    language: str,
    filepath: str = "",
) -> ChunkMetadata:
    """
    AST 노드에서 메타데이터를 추출합니다.
    
    Args:
        node: 현재 청크의 AST 노드
        content: 청크의 텍스트 내용
        root_node: 파일 전체의 루트 노드 (import 분석용)
        language: 프로그래밍 언어
        filepath: 파일 경로 (루트 노드의 symbol_name으로 사용)
    
    Returns:
        ChunkMetadata: 추출된 메타데이터
    """
    metadata = ChunkMetadata()
    
    # 1. 심볼 정보 추출
    if node.type in SYMBOL_TYPE_MAPPING:
        metadata.symbol_type = SYMBOL_TYPE_MAPPING[node.type]
        
        # 루트 노드인 경우 파일명을 symbol_name으로 사용
        if metadata.symbol_type == "file" and filepath:
            import os
            metadata.symbol_name = os.path.basename(filepath)
        else:
            metadata.symbol_name = extract_symbol_name(node)
    
    # 2. Import 분석 (루트 노드에서)
    metadata.imports = extract_imports(root_node, language)
    
    # 3. Export 분석 (루트 노드에서)
    metadata.exports = extract_exports(root_node, language)
    
    # 4. 참조 관계
    metadata.references_to = extract_references(node, content)
    metadata.symbol_definitions = extract_symbol_definitions(node)
    
    # 5. 상속 관계 (클래스인 경우)
    if metadata.symbol_type == "class":
        metadata.extends = extract_parent_class(node)
        metadata.implements = extract_interfaces(node)
    
    return metadata


def get_language_from_filepath(filepath: str) -> str:
    """파일 경로에서 언어를 추출합니다."""
    ext_to_lang = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "jsx",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".java": "java",
        ".rs": "rust",
        ".go": "go",
        ".cpp": "cpp",
        ".c": "c",
    }
    
    for ext, lang in ext_to_lang.items():
        if filepath.endswith(ext):
            return lang
    
    return "unknown"

