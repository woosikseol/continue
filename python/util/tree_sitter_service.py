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
        """언어 라이브러리 빌드 - 원본과 동일한 언어 지원"""
        try:
            # 언어 라이브러리 디렉토리 생성
            build_dir = Path("build")
            build_dir.mkdir(exist_ok=True)
            
            # 지원하는 언어들의 소스 디렉토리 (원본과 동일)
            language_sources = [
                'vendor/tree-sitter-python',
                'vendor/tree-sitter-javascript', 
                'vendor/tree-sitter-java',
                'vendor/tree-sitter-typescript',
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
                tree_sitter.Language.build_library(
                    str(build_dir / 'my-languages.so'),
                    existing_sources
                )
                logger.info(f"언어 라이브러리 빌드 완료: {len(existing_sources)}개 언어")
            else:
                logger.warning("언어 소스 디렉토리를 찾을 수 없습니다. 기본 파서만 사용합니다.")
                
        except Exception as e:
            logger.warning(f"언어 라이브러리 빌드 실패: {e}")
    
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
    
    def get_full_language_name(self, filepath: str) -> Optional[LanguageName]:
        """파일의 전체 언어 이름 반환 - 원본 getFullLanguageName 함수 포팅"""
        ext = Path(filepath).suffix.lstrip('.').lower()
        return SUPPORTED_LANGUAGES.get(ext)
