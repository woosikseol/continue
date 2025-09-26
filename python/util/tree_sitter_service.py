"""
Tree-sitter 서비스
원본 TypeScript treeSitter.ts의 Python 포팅
Tree-sitter를 사용하여 소스코드 파싱 및 분석
원본과 동일한 Tree-sitter (C++ 기반, WebAssembly)를 직접 사용
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    import tree_sitter
    from tree_sitter import Language, Parser, Node
except ImportError:
    raise ImportError("tree-sitter가 설치되지 않았습니다. pip install tree-sitter로 설치하세요.")

from continue_types import LanguageName, SUPPORTED_LANGUAGES, SymbolWithRange, Position, Range, FileSymbolMap, RangeInFileWithContents

logger = logging.getLogger(__name__)

class TreeSitterService:
    """Tree-sitter 서비스 클래스 - 원본 treeSitter.ts의 Python 포팅"""
    
    def __init__(self):
        self.parser = Parser()
        self.language_cache: Dict[str, Language] = {}
        self._initialized = False
    
    async def initialize(self):
        """Tree-sitter 초기화 - 원본과 동일한 초기화 과정"""
        try:
            # Tree-sitter 언어 라이브러리 빌드
            self._build_language_library()
            self._initialized = True
            logger.info("Tree-sitter 서비스 초기화 완료")
            
        except Exception as e:
            logger.error(f"Tree-sitter 초기화 실패: {e}")
            raise
    
    def _build_language_library(self):
        """언어 라이브러리 빌드 - 원본과 동일한 언어 지원 + 요청하신 언어들"""
        try:
            # 언어 라이브러리 디렉토리 생성
            build_dir = Path("build")
            build_dir.mkdir(exist_ok=True)
            
            # 지원하는 언어들의 소스 디렉토리 (원본과 동일 + 요청하신 언어들)
            language_sources = [
                # 요청하신 주요 언어들
                'vendor/tree-sitter-python',      # Python
                'vendor/tree-sitter-javascript',  # JavaScript  
                'vendor/tree-sitter-typescript',  # TypeScript
                'vendor/tree-sitter-java',         # Java
                
                # 추가 지원 언어들
                'vendor/tree-sitter-cpp',
                'vendor/tree-sitter-go',
                'vendor/tree-sitter-rust',
                'vendor/tree-sitter-c',
                'vendor/tree-sitter-c-sharp',
                'vendor/tree-sitter-html',
                'vendor/tree-sitter-css',
                'vendor/tree-sitter-php',
                'vendor/tree-sitter-bash',
                'vendor/tree-sitter-json',
                'vendor/tree-sitter-ruby',
                'vendor/tree-sitter-lua',
                'vendor/tree-sitter-ocaml',
                'vendor/tree-sitter-elm',
                'vendor/tree-sitter-elixir',
                'vendor/tree-sitter-elisp',
                'vendor/tree-sitter-rescript',
                'vendor/tree-sitter-toml',
                'vendor/tree-sitter-solidity',
                'vendor/tree-sitter-systemrdl',
                'vendor/tree-sitter-ql'
            ]
            
            # 실제 존재하는 언어 소스만 필터링
            existing_sources = [src for src in language_sources if Path(src).exists()]
            
            if existing_sources:
                # 언어 라이브러리 빌드
                # 내부적으로 다음과 같은 컴파일이 수행됨
                # gcc -shared -fPIC -o my-languages.so \
                #     vendor/tree-sitter-python/src/parser.c \
                #     vendor/tree-sitter-python/src/scanner.cc \
                #     vendor/tree-sitter-javascript/src/parser.c \
                #     vendor/tree-sitter-javascript/src/scanner.c \
                # ... 다른 언어들
                tree_sitter.Language.build_library(
                    str(build_dir / 'my-languages.so'),
                    existing_sources
                )
                logger.info(f"언어 라이브러리 빌드 완료: {len(existing_sources)}개 언어")
                logger.info(f"지원 언어: {[Path(src).name for src in existing_sources]}")
            else:
                logger.warning("언어 소스 디렉토리를 찾을 수 없습니다. 기본 파서만 사용합니다.")
                
        except Exception as e:
            logger.warning(f"언어 라이브러리 빌드 실패: {e}")
    
    def get_supported_languages(self) -> List[str]:
        """지원하는 언어 목록 반환"""
        return [
            'python', 'javascript', 'typescript', 'java',
            'cpp', 'c', 'go', 'rust', 'c_sharp',
            'html', 'css', 'php', 'bash', 'json',
            'ruby', 'lua', 'ocaml', 'elm', 'elixir',
            'elisp', 'rescript', 'toml', 'solidity',
            'systemrdl', 'ql'
        ]
    
    def get_language_info(self, language: str) -> Dict[str, Any]:
        """언어별 정보 반환"""
        language_info = {
            'python': {
                'name': 'Python',
                'extensions': ['.py', '.pyw', '.pyi'],
                'description': 'Python 프로그래밍 언어',
                'parser_features': ['syntax_highlighting', 'symbol_extraction', 'ast_analysis']
            },
            'javascript': {
                'name': 'JavaScript',
                'extensions': ['.js', '.jsx', '.mjs', '.cjs'],
                'description': 'JavaScript 프로그래밍 언어',
                'parser_features': ['syntax_highlighting', 'symbol_extraction', 'ast_analysis']
            },
            'typescript': {
                'name': 'TypeScript',
                'extensions': ['.ts', '.tsx', '.mts', '.cts'],
                'description': 'TypeScript 프로그래밍 언어',
                'parser_features': ['syntax_highlighting', 'symbol_extraction', 'ast_analysis', 'type_analysis']
            },
            'java': {
                'name': 'Java',
                'extensions': ['.java'],
                'description': 'Java 프로그래밍 언어',
                'parser_features': ['syntax_highlighting', 'symbol_extraction', 'ast_analysis', 'class_analysis']
            }
        }
        
        return language_info.get(language, {
            'name': language.title(),
            'extensions': [],
            'description': f'{language} 프로그래밍 언어',
            'parser_features': ['syntax_highlighting', 'symbol_extraction', 'ast_analysis']
        })
    
    def get_language_for_file(self, filepath: str) -> Optional[Language]:
        """파일 확장자에 따른 언어 반환 - 원본 getLanguageForFile 함수 포팅"""
        try:
            ext = Path(filepath).suffix.lstrip('.').lower()
            language_name = SUPPORTED_LANGUAGES.get(ext)
            
            if not language_name:
                return None
            
            # 캐시에서 언어 확인
            if language_name.value in self.language_cache:
                return self.language_cache[language_name.value]
            
            # 언어 로드
            try:
                language = Language('build/my-languages.so', language_name.value)
                self.language_cache[language_name.value] = language
                return language
            except Exception:
                # 언어 로드 실패 시 None 반환
                logger.debug(f"언어 로드 실패: {language_name.value}")
                return None
            
        except Exception as e:
            logger.error(f"언어 결정 실패 {filepath}: {e}")
            return None
    
    def get_parser_for_file(self, filepath: str) -> Optional[Parser]:
        """파일에 대한 파서 반환 - 원본 getParserForFile 함수 포팅"""
        try:
            language = self.get_language_for_file(filepath)
            if not language:
                return None
            
            parser = Parser()
            parser.set_language(language)
            return parser
            
        except Exception as e:
            logger.error(f"파서 생성 실패 {filepath}: {e}")
            return None
    
    async def get_ast(self, filepath: str, contents: Optional[str] = None) -> Optional[Node]:
        """AST 생성 - 원본 getAst 함수 포팅"""
        try:
            if contents is None:
                with open(filepath, 'r', encoding='utf-8') as f:
                    contents = f.read()
            
            parser = self.get_parser_for_file(filepath)
            if not parser:
                return None
            
            tree = parser.parse(bytes(contents, 'utf8'))
            return tree.root_node
            
        except Exception as e:
            logger.error(f"AST 생성 실패 {filepath}: {e}")
            return None
    
    def extract_ast_metadata(self, node: Node, filepath: str) -> Dict[str, Any]:
        """1.2 AST 노드 추출 및 메타데이터 수집 - 요청하신 단계 구현"""
        if not node:
            return {}
        
        metadata = {
            'root_node': {
                'type': node.type,
                'text': node.text.decode('utf8')[:200] + "..." if len(node.text) > 200 else node.text.decode('utf8'),
                'start_position': [node.start_point[0], node.start_point[1]],
                'end_position': [node.end_point[0], node.end_point[1]],
                'children_count': len(node.children),
                'byte_range': [node.start_byte, node.end_byte]
            },
            'node_extraction': self._extract_all_nodes(node, filepath),
            'tree_structure': self._build_tree_structure(node),
            'structural_metrics': self.calculate_structural_metrics(node)
        }
        
        return metadata
    
    def _extract_all_nodes(self, node: Node, filepath: str) -> List[Dict[str, Any]]:
        """1.2.1 모든 노드 추출 및 메타데이터 수집"""
        nodes = []
        
        def extract_node_info(current_node, depth=0, path=""):
            if not current_node:
                return
            
            node_info = {
                'type': current_node.type,
                'text': current_node.text.decode('utf8')[:100] + "..." if len(current_node.text) > 100 else current_node.text.decode('utf8'),
                'start_position': [current_node.start_point[0], current_node.start_point[1]],
                'end_position': [current_node.end_point[0], current_node.end_point[1]],
                'byte_range': [current_node.start_byte, current_node.end_byte],
                'children_count': len(current_node.children),
                'depth': depth,
                'path': path,
                'is_leaf': len(current_node.children) == 0,
                'parent_type': None,  # 나중에 설정
                'sibling_index': 0,   # 나중에 설정
                'node_id': f"{filepath}:{current_node.start_byte}:{current_node.end_byte}"
            }
            
            nodes.append(node_info)
            
            # 자식 노드들 재귀 처리
            for i, child in enumerate(current_node.children):
                child_path = f"{path}/{current_node.type}[{i}]" if path else f"{current_node.type}[{i}]"
                extract_node_info(child, depth + 1, child_path)
        
        extract_node_info(node)
        
        # 부모-자식 관계 설정
        self._set_parent_child_relationships(nodes)
        
        return nodes
    
    def _set_parent_child_relationships(self, nodes: List[Dict[str, Any]]):
        """부모-자식 관계 설정"""
        for i, node in enumerate(nodes):
            # 부모 노드 찾기
            for j, potential_parent in enumerate(nodes):
                if j >= i:
                    break
                
                if (potential_parent['start_position'] <= node['start_position'] and 
                    potential_parent['end_position'] >= node['end_position'] and
                    potential_parent['depth'] < node['depth']):
                    node['parent_type'] = potential_parent['type']
                    break
            
            # 형제 인덱스 설정
            sibling_count = 0
            for j, sibling in enumerate(nodes):
                if (j < i and 
                    sibling.get('parent_type') == node.get('parent_type') and
                    sibling['depth'] == node['depth']):
                    sibling_count += 1
            node['sibling_index'] = sibling_count
    
    def _build_tree_structure(self, node: Node) -> Dict[str, Any]:
        """1.3 트리 구조 구성 - 계층적 구조, 깊이, 경로 추적"""
        if not node:
            return {}
        
        structure = {
            'hierarchical_structure': self._build_hierarchical_structure(node),
            'depth_analysis': self._analyze_depths(node),
            'path_tracking': self._track_paths(node),
            'tree_metrics': {
                'total_nodes': self.count_nodes(node),
                'max_depth': self.get_max_depth(node),
                'average_depth': self._calculate_average_depth(node),
                'tree_width': self._calculate_tree_width(node)
            }
        }
        
        return structure
    
    def _build_hierarchical_structure(self, node: Node) -> Dict[str, Any]:
        """계층적 구조 구성"""
        def build_node_structure(current_node, depth=0):
            if not current_node:
                return None
            
            structure = {
                'type': current_node.type,
                'depth': depth,
                'children': [],
                'metadata': {
                    'start_position': [current_node.start_point[0], current_node.start_point[1]],
                    'end_position': [current_node.end_point[0], current_node.end_point[1]],
                    'text_preview': current_node.text.decode('utf8')[:50] + "..." if len(current_node.text) > 50 else current_node.text.decode('utf8')
                }
            }
            
            for child in current_node.children:
                child_structure = build_node_structure(child, depth + 1)
                if child_structure:
                    structure['children'].append(child_structure)
            
            return structure
        
        return build_node_structure(node)
    
    def _analyze_depths(self, node: Node) -> Dict[str, Any]:
        """깊이 분석"""
        depth_stats = {
            'max_depth': 0,
            'min_depth': float('inf'),
            'depth_distribution': {},
            'nodes_at_depth': {}
        }
        
        def analyze_depth(current_node, depth=0):
            if not current_node:
                return
            
            depth_stats['max_depth'] = max(depth_stats['max_depth'], depth)
            depth_stats['min_depth'] = min(depth_stats['min_depth'], depth)
            
            depth_stats['depth_distribution'][depth] = depth_stats['depth_distribution'].get(depth, 0) + 1
            
            if depth not in depth_stats['nodes_at_depth']:
                depth_stats['nodes_at_depth'][depth] = []
            
            depth_stats['nodes_at_depth'][depth].append({
                'type': current_node.type,
                'position': [current_node.start_point[0], current_node.start_point[1]]
            })
            
            for child in current_node.children:
                analyze_depth(child, depth + 1)
        
        analyze_depth(node)
        
        if depth_stats['min_depth'] == float('inf'):
            depth_stats['min_depth'] = 0
        
        return depth_stats
    
    def _track_paths(self, node: Node) -> List[Dict[str, Any]]:
        """경로 추적 - 루트부터 각 노드까지의 경로"""
        paths = []
        
        def track_path(current_node, current_path=None):
            if not current_node:
                return
            
            if current_path is None:
                current_path = []
            
            current_path = current_path + [{
                'type': current_node.type,
                'position': [current_node.start_point[0], current_node.start_point[1]],
                'depth': len(current_path)
            }]
            
            # 리프 노드인 경우 경로 저장
            if not current_node.children:
                paths.append({
                    'path': current_path,
                    'length': len(current_path),
                    'end_node': current_node.type
                })
            
            for child in current_node.children:
                track_path(child, current_path)
        
        track_path(node)
        return paths
    
    def _calculate_average_depth(self, node: Node) -> float:
        """평균 깊이 계산"""
        if not node:
            return 0.0
        
        total_depth = 0
        total_nodes = 0
        
        def calculate_depth(current_node, depth=0):
            nonlocal total_depth, total_nodes
            if not current_node:
                return
            
            total_depth += depth
            total_nodes += 1
            
            for child in current_node.children:
                calculate_depth(child, depth + 1)
        
        calculate_depth(node)
        return total_depth / total_nodes if total_nodes > 0 else 0.0
    
    def _calculate_tree_width(self, node: Node) -> int:
        """트리 너비 계산 (최대 자식 수)"""
        if not node:
            return 0
        
        max_width = len(node.children)
        
        def find_max_width(current_node):
            nonlocal max_width
            if not current_node:
                return
            
            max_width = max(max_width, len(current_node.children))
            
            for child in current_node.children:
                find_max_width(child)
        
        find_max_width(node)
        return max_width
    
    async def get_symbols_for_file(self, filepath: str, contents: Optional[str] = None) -> List[SymbolWithRange]:
        """파일에서 심볼 추출 - 원본 getSymbolsForFile 함수 포팅"""
        try:
            ast = await self.get_ast(filepath, contents)
            if not ast:
                return []
            
            symbols = []
            self._extract_symbols_recursive(ast, filepath, symbols)
            return symbols
            
        except Exception as e:
            logger.error(f"심볼 추출 실패 {filepath}: {e}")
            return []
    
    def _extract_symbols_recursive(self, node: Node, filepath: str, symbols: List[SymbolWithRange]):
        """재귀적으로 심볼 추출 - 원본 findNamedNodesRecursive 함수 포팅"""
        # 원본과 동일한 심볼 노드 타입들
        GET_SYMBOLS_FOR_NODE_TYPES = [
            'class_declaration', 'class_definition', 'function_item',
            'function_definition', 'method_declaration', 'method_definition',
            'generator_function_declaration', 'class', 'function', 'method',
            'interface', 'enum', 'variable_declaration', 'const_declaration',
            'property_identifier', 'field_declaration'
        ]
        
        if node.type in GET_SYMBOLS_FOR_NODE_TYPES:
            # 식별자 찾기 - 원본과 동일한 로직
            identifier = self._find_identifier(node)
            if identifier:
                symbol = SymbolWithRange(
                    filepath=filepath,
                    type=node.type,
                    name=identifier.text.decode('utf8'),
                    range=Range(
                        start=Position(
                            line=node.start_point[0],
                            character=node.start_point[1]
                        ),
                        end=Position(
                            line=node.end_point[0],
                            character=node.end_point[1]
                        )
                    ),
                    content=node.text.decode('utf8')
                )
                symbols.append(symbol)
        
        # 자식 노드들 재귀 처리
        for child in node.children:
            self._extract_symbols_recursive(child, filepath, symbols)
    
    def _find_identifier(self, node: Node) -> Optional[Node]:
        """노드에서 식별자 찾기 - 원본과 동일한 로직"""
        # 자식 노드들을 역순으로 검색 (원본과 동일)
        for child in reversed(node.children):
            if child.type in ['identifier', 'property_identifier']:
                return child
        return None
    
    async def get_symbols_for_many_files(self, filepaths: List[str]) -> FileSymbolMap:
        """여러 파일에서 심볼 추출 - 원본 getSymbolsForManyFiles 함수 포팅"""
        try:
            results = {}
            
            # 병렬로 심볼 추출
            import asyncio
            tasks = []
            for filepath in filepaths:
                task = self.get_symbols_for_file(filepath)
                tasks.append((filepath, task))
            
            for filepath, task in tasks:
                try:
                    symbols = await task
                    results[filepath] = symbols
                except Exception as e:
                    logger.error(f"심볼 추출 실패 {filepath}: {e}")
                    results[filepath] = []
            
            return results
            
        except Exception as e:
            logger.error(f"다중 파일 심볼 추출 실패: {e}")
            return {}
    
    def get_tree_path_at_cursor(self, ast: Node, cursor_index: int) -> List[Node]:
        """커서 위치의 트리 경로 반환 - 원본 getTreePathAtCursor 함수 포팅"""
        try:
            path = [ast]
            while path[-1].child_count > 0:
                found_child = False
                for child in path[-1].children:
                    if child.start_byte <= cursor_index <= child.end_byte:
                        path.append(child)
                        found_child = True
                        break
                
                if not found_child:
                    break
            
            return path
            
        except Exception as e:
            logger.error(f"트리 경로 추출 실패: {e}")
            return []
    
    def get_scope_around_range(self, filepath: str, contents: str, range_obj: Range) -> Optional[RangeInFileWithContents]:
        """범위 주변의 스코프 반환 - 원본 getScopeAroundRange 함수 포팅"""
        try:
            ast = self.get_ast(filepath, contents)
            if not ast:
                return None
            
            # 범위를 바이트 인덱스로 변환
            lines = contents.split("\n")
            start_index = sum(len(line) + 1 for line in lines[:range_obj.start.line]) + range_obj.start.character
            end_index = sum(len(line) + 1 for line in lines[:range_obj.end.line]) + range_obj.end.character
            
            # 범위를 포함하는 가장 작은 노드 찾기
            node = ast
            while node.child_count > 0:
                found_child = False
                for child in node.children:
                    if child.start_byte < start_index and child.end_byte > end_index:
                        node = child
                        found_child = True
                        break
                
                if not found_child:
                    break
            
            return RangeInFileWithContents(
                filepath=filepath,
                range=Range(
                    start=Position(
                        line=node.start_point[0],
                        character=node.start_point[1]
                    ),
                    end=Position(
                        line=node.end_point[0],
                        character=node.end_point[1]
                    )
                ),
                contents=node.text.decode('utf8')
            )
            
        except Exception as e:
            logger.error(f"스코프 추출 실패: {e}")
            return None
    
    def count_nodes(self, node: Node) -> int:
        """노드 수 계산"""
        if not node:
            return 0
        
        count = 1
        for child in node.children:
            count += self.count_nodes(child)
        return count
    
    def get_max_depth(self, node: Node, depth: int = 0) -> int:
        """최대 깊이 계산"""
        if not node or not node.children:
            return depth
        
        max_child_depth = depth
        for child in node.children:
            child_depth = self.get_max_depth(child, depth + 1)
            max_child_depth = max(max_child_depth, child_depth)
        
        return max_child_depth
    
    def get_node_types(self, node: Node) -> Dict[str, int]:
        """노드 타입별 개수 계산"""
        types = {}
        
        def count_types(current_node):
            if not current_node:
                return
            
            node_type = current_node.type
            types[node_type] = types.get(node_type, 0) + 1
            
            for child in current_node.children:
                count_types(child)
        
        count_types(node)
        return types
    
    def get_structural_metrics(self, node: Node) -> Dict[str, Any]:
        """구조적 메트릭 계산 - 요청하신 모든 단계 구현"""
        if not node:
            return {
                'total_nodes': 0,
                'max_depth': 0,
                'node_types': {},
                'complexity': 0,
                'structural_metrics': {}
            }
        
        # 1.4 구조적 메트릭 계산
        total_nodes = self.count_nodes(node)
        max_depth = self.get_max_depth(node)
        node_types = self.get_node_types(node)
        
        # 복잡도 계산 (Cyclomatic Complexity 근사)
        complexity = self._calculate_complexity(node)
        
        # 구조적 메트릭
        structural_metrics = {
            'total_nodes': total_nodes,
            'max_depth': max_depth,
            'node_types': node_types,
            'complexity': complexity,
            'average_children_per_node': self._calculate_average_children(node),
            'leaf_node_ratio': self._calculate_leaf_node_ratio(node),
            'branching_factor': self._calculate_branching_factor(node)
        }
        
        return structural_metrics
    
    def _calculate_complexity(self, node: Node) -> int:
        """복잡도 계산 (Cyclomatic Complexity)"""
        complexity = 1  # 기본 복잡도
        
        def count_complexity_nodes(current_node):
            nonlocal complexity
            if not current_node:
                return
            
            # 복잡도를 증가시키는 노드 타입들
            complexity_nodes = [
                'if_statement', 'while_statement', 'for_statement', 'for_in_statement',
                'try_statement', 'catch_clause', 'switch_statement', 'case_clause',
                'conditional_expression', 'logical_expression', 'binary_expression',
                'and', 'or', 'not', 'ternary_expression'
            ]
            
            if current_node.type in complexity_nodes:
                complexity += 1
            
            for child in current_node.children:
                count_complexity_nodes(child)
        
        count_complexity_nodes(node)
        return complexity
    
    def _calculate_average_children(self, node: Node) -> float:
        """노드당 평균 자식 수 계산"""
        if not node:
            return 0.0
        
        total_children = 0
        total_nodes = 0
        
        def count_children(current_node):
            nonlocal total_children, total_nodes
            if not current_node:
                return
            
            total_nodes += 1
            total_children += len(current_node.children)
            
            for child in current_node.children:
                count_children(child)
        
        count_children(node)
        return total_children / total_nodes if total_nodes > 0 else 0.0
    
    def _calculate_leaf_node_ratio(self, node: Node) -> float:
        """리프 노드 비율 계산"""
        if not node:
            return 0.0
        
        total_nodes = self.count_nodes(node)
        leaf_nodes = self._count_leaf_nodes(node)
        
        return leaf_nodes / total_nodes if total_nodes > 0 else 0.0
    
    def _count_leaf_nodes(self, node: Node) -> int:
        """리프 노드 수 계산"""
        if not node:
            return 0
        
        if not node.children:
            return 1
        
        count = 0
        for child in node.children:
            count += self._count_leaf_nodes(child)
        
        return count
    
    def _calculate_branching_factor(self, node: Node) -> float:
        """분기 인수 계산"""
        if not node:
            return 0.0
        
        total_branches = 0
        total_nodes = 0
        
        def count_branches(current_node):
            nonlocal total_branches, total_nodes
            if not current_node:
                return
            
            total_nodes += 1
            if len(current_node.children) > 1:
                total_branches += len(current_node.children) - 1
            
            for child in current_node.children:
                count_branches(child)
        
        count_branches(node)
        return total_branches / total_nodes if total_nodes > 0 else 0.0
    
    def get_full_language_name(self, filepath: str) -> Optional[LanguageName]:
        """파일의 전체 언어 이름 반환 - 원본 getFullLanguageName 함수 포팅"""
        ext = Path(filepath).suffix.lstrip('.').lower()
        return SUPPORTED_LANGUAGES.get(ext)
    
    def calculate_structural_metrics(self, node: Node) -> Dict[str, Any]:
        """1.4 구조적 메트릭 계산 - 요청하신 단계 완전 구현"""
        if not node:
            return {}
        
        metrics = {
            'total_nodes': 0,
            'max_depth': 0,
            'complexity_score': 0.0,
            'node_type_distribution': {},
            'average_children_per_node': 0.0,
            'leaf_nodes': 0,
            'branch_nodes': 0,
            'cyclomatic_complexity': 0,
            'nesting_depth_distribution': {},
            'structural_patterns': {},
            'code_quality_metrics': {}
        }
        
        def calculate_metrics(current_node, depth=0):
            if not current_node:
                return
            
            metrics['total_nodes'] += 1
            metrics['max_depth'] = max(metrics['max_depth'], depth)
            
            # 노드 타입별 분포
            node_type = current_node.type
            metrics['node_type_distribution'][node_type] = metrics['node_type_distribution'].get(node_type, 0) + 1
            
            # 깊이별 분포
            depth_key = f'depth_{depth}'
            metrics['nesting_depth_distribution'][depth_key] = metrics['nesting_depth_distribution'].get(depth_key, 0) + 1
            
            # 리프 노드와 브랜치 노드 구분
            if len(current_node.children) == 0:
                metrics['leaf_nodes'] += 1
            else:
                metrics['branch_nodes'] += 1
            
            # 순환 복잡도 계산 (제어 구조 기반)
            if node_type in ['if_statement', 'while_statement', 'for_statement', 'try_statement', 'switch_statement', 'conditional_expression']:
                metrics['cyclomatic_complexity'] += 1
            elif node_type in ['case_statement', 'except_clause', 'elif_clause']:
                metrics['cyclomatic_complexity'] += 1
            
            # 구조적 복잡도 계산 (분기 노드 기반)
            if len(current_node.children) > 1:
                metrics['complexity_score'] += len(current_node.children) * 0.5
                
                # 깊은 중첩 패널티
                if depth > 3:
                    metrics['complexity_score'] += (depth - 3) * 0.3
            
            # 구조적 패턴 분석
            self._analyze_structural_patterns(current_node, metrics, depth)
            
            # 자식 노드들 재귀 처리
            for child in current_node.children:
                calculate_metrics(child, depth + 1)
        
        calculate_metrics(node)
        
        # 평균 자식 노드 수 계산
        if metrics['branch_nodes'] > 0:
            total_children = metrics['total_nodes'] - 1  # 루트 제외
            metrics['average_children_per_node'] = total_children / metrics['branch_nodes']
        
        # 코드 품질 메트릭 계산
        metrics['code_quality_metrics'] = self._calculate_code_quality_metrics(metrics)
        
        return metrics
    
    def _analyze_structural_patterns(self, node: Node, metrics: Dict[str, Any], depth: int):
        """구조적 패턴 분석"""
        if 'structural_patterns' not in metrics:
            metrics['structural_patterns'] = {}
        
        patterns = metrics['structural_patterns']
        node_type = node.type
        
        # 함수/메서드 패턴
        if node_type in ['function_definition', 'method_definition', 'function_declaration']:
            patterns['functions'] = patterns.get('functions', 0) + 1
            
            # 함수 복잡도 (매개변수 수, 중첩 깊이)
            param_count = len([child for child in node.children if child.type in ['parameters', 'parameter_list']])
            if param_count > 5:
                patterns['complex_functions'] = patterns.get('complex_functions', 0) + 1
        
        # 클래스 패턴
        elif node_type in ['class_definition', 'class_declaration']:
            patterns['classes'] = patterns.get('classes', 0) + 1
            
            # 메서드 수 계산
            method_count = len([child for child in node.children if child.type in ['function_definition', 'method_definition']])
            if method_count > 10:
                patterns['large_classes'] = patterns.get('large_classes', 0) + 1
        
        # 깊은 중첩 패턴
        if depth > 5:
            patterns['deep_nesting'] = patterns.get('deep_nesting', 0) + 1
        
        # 반복문 패턴
        if node_type in ['for_statement', 'while_statement']:
            patterns['loops'] = patterns.get('loops', 0) + 1
            
            # 중첩 반복문
            if depth > 2:
                patterns['nested_loops'] = patterns.get('nested_loops', 0) + 1
        
        # 조건문 패턴
        if node_type in ['if_statement', 'conditional_expression']:
            patterns['conditionals'] = patterns.get('conditionals', 0) + 1
            
            # 복잡한 조건문 (else if 체인)
            elif_count = len([child for child in node.children if child.type == 'elif_clause'])
            if elif_count > 3:
                patterns['complex_conditionals'] = patterns.get('complex_conditionals', 0) + 1
    
    def _calculate_code_quality_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """코드 품질 메트릭 계산"""
        quality_metrics = {}
        
        # 복잡도 점수 (0-100)
        complexity_score = min(100, max(0, 100 - (metrics['complexity_score'] * 2)))
        quality_metrics['complexity_score'] = round(complexity_score, 2)
        
        # 유지보수성 점수
        maintainability = 100
        if metrics['max_depth'] > 6:
            maintainability -= (metrics['max_depth'] - 6) * 5
        if metrics['cyclomatic_complexity'] > 10:
            maintainability -= (metrics['cyclomatic_complexity'] - 10) * 3
        
        quality_metrics['maintainability_score'] = round(max(0, maintainability), 2)
        
        # 구조적 균형 점수
        if metrics['total_nodes'] > 0:
            leaf_ratio = metrics['leaf_nodes'] / metrics['total_nodes']
            balance_score = 100 - abs(0.5 - leaf_ratio) * 200  # 50% 리프 노드가 이상적
            quality_metrics['structural_balance'] = round(max(0, balance_score), 2)
        
        # 전체 품질 점수
        overall_score = (
            quality_metrics['complexity_score'] * 0.4 +
            quality_metrics['maintainability_score'] * 0.4 +
            quality_metrics.get('structural_balance', 50) * 0.2
        )
        quality_metrics['overall_quality'] = round(overall_score, 2)
        
        return quality_metrics
