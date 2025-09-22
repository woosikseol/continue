"""
자동완성 제공자
원본 TypeScript CompletionProvider의 Python 포팅
Tree-sitter와 LSP를 사용하여 정확한 자동완성 제공
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from continue_types import Position, Range, ContextItemWithId
from util.tree_sitter_service import TreeSitterService
from util.lsp_service import LSPService

logger = logging.getLogger(__name__)

@dataclass
class CompletionItem:
    """완성 아이템"""
    label: str
    kind: str
    detail: Optional[str] = None
    documentation: Optional[str] = None
    insert_text: Optional[str] = None
    range: Optional[Range] = None

@dataclass
class CompletionContext:
    """완성 컨텍스트"""
    filepath: str
    position: Position
    trigger_character: Optional[str] = None
    trigger_kind: str = "invoked"  # "invoked" | "triggerCharacter"

class CompletionProvider:
    """자동완성 제공자 - 원본 TypeScript CompletionProvider의 Python 포팅"""
    
    def __init__(self, tree_sitter_service: Optional[TreeSitterService], lsp_service: Optional[LSPService]):
        self.tree_sitter_service = tree_sitter_service
        self.lsp_service = lsp_service
        self._completion_cache: Dict[str, List[CompletionItem]] = {}
        
        logger.info("자동완성 제공자 초기화 완료")
    
    async def get_completions(self, filepath: str, position: Position) -> List[CompletionItem]:
        """자동완성 제공 - 원본과 동일한 기능"""
        try:
            context = CompletionContext(
                filepath=filepath,
                position=position
            )
            
            # 캐시 확인
            cache_key = f"{filepath}:{position.line}:{position.character}"
            if cache_key in self._completion_cache:
                return self._completion_cache[cache_key]
            
            completions = []
            
            # Tree-sitter 기반 완성
            if self.tree_sitter_service:
                tree_sitter_completions = await self._get_tree_sitter_completions(context)
                completions.extend(tree_sitter_completions)
            
            # LSP 기반 완성
            if self.lsp_service:
                lsp_completions = await self._get_lsp_completions(context)
                completions.extend(lsp_completions)
            
            # 중복 제거 및 정렬
            completions = self._deduplicate_and_sort_completions(completions)
            
            # 캐시 저장
            self._completion_cache[cache_key] = completions
            
            return completions
            
        except Exception as e:
            logger.error(f"자동완성 실패: {e}")
            return []
    
    async def _get_tree_sitter_completions(self, context: CompletionContext) -> List[CompletionItem]:
        """Tree-sitter 기반 자동완성"""
        try:
            if not self.tree_sitter_service:
                return []
            
            # AST 분석
            ast = await self.tree_sitter_service.get_ast(context.filepath)
            if not ast:
                return []
            
            # 커서 위치의 트리 경로
            cursor_index = self._get_cursor_index(context)
            tree_path = self.tree_sitter_service.get_tree_path_at_cursor(ast, cursor_index)
            
            completions = []
            
            # 현재 스코프의 심볼들 찾기
            scope_symbols = await self._get_scope_symbols(context, tree_path)
            for symbol in scope_symbols:
                completion = CompletionItem(
                    label=symbol.name,
                    kind=self._get_completion_kind(symbol.type),
                    detail=f"{symbol.type} in {symbol.filepath}",
                    documentation=symbol.content[:200] + "..." if len(symbol.content) > 200 else symbol.content,
                    range=symbol.range
                )
                completions.append(completion)
            
            return completions
            
        except Exception as e:
            logger.error(f"Tree-sitter 자동완성 실패: {e}")
            return []
    
    async def _get_lsp_completions(self, context: CompletionContext) -> List[CompletionItem]:
        """LSP 기반 자동완성"""
        try:
            if not self.lsp_service:
                return []
            
            # LSP 완성 요청
            lsp_position = self.lsp_service.LSPPosition(
                line=context.position.line,
                character=context.position.character
            )
            
            # LSP 완성 요청 (실제 구현에서는 LSP 프로토콜 사용)
            # 여기서는 시뮬레이션
            completions = []
            
            # 문서 심볼들 가져오기
            document_symbols = await self.lsp_service.get_document_symbols(context.filepath)
            for symbol in document_symbols:
                completion = CompletionItem(
                    label=symbol.name,
                    kind=self._get_lsp_completion_kind(symbol.kind),
                    detail=f"Symbol at line {symbol.range.start.line}",
                    range=Range(
                        start=Position(
                            line=symbol.range.start.line,
                            character=symbol.range.start.character
                        ),
                        end=Position(
                            line=symbol.range.end.line,
                            character=symbol.range.end.character
                        )
                    )
                )
                completions.append(completion)
            
            return completions
            
        except Exception as e:
            logger.error(f"LSP 자동완성 실패: {e}")
            return []
    
    async def _get_scope_symbols(self, context: CompletionContext, tree_path: List[Any]) -> List[Any]:
        """현재 스코프의 심볼들 가져오기"""
        try:
            if not self.tree_sitter_service:
                return []
            
            # 파일의 모든 심볼 가져오기
            all_symbols = await self.tree_sitter_service.get_symbols_for_file(context.filepath)
            
            # 현재 스코프에 있는 심볼들 필터링
            scope_symbols = []
            for symbol in all_symbols:
                # 심볼이 현재 위치보다 앞에 정의되어 있는지 확인
                if (symbol.range.end.line < context.position.line or 
                    (symbol.range.end.line == context.position.line and 
                     symbol.range.end.character <= context.position.character)):
                    scope_symbols.append(symbol)
            
            return scope_symbols
            
        except Exception as e:
            logger.error(f"스코프 심볼 가져오기 실패: {e}")
            return []
    
    def _get_cursor_index(self, context: CompletionContext) -> int:
        """커서 위치를 바이트 인덱스로 변환"""
        try:
            with open(context.filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            index = 0
            
            # 현재 라인까지의 모든 문자 수 계산
            for i in range(context.position.line):
                index += len(lines[i]) + 1  # +1 for newline
            
            # 현재 라인의 문자 수 추가
            index += context.position.character
            
            return index
            
        except Exception as e:
            logger.error(f"커서 인덱스 계산 실패: {e}")
            return 0
    
    def _get_completion_kind(self, symbol_type: str) -> str:
        """심볼 타입을 완성 종류로 변환"""
        kind_map = {
            'function_definition': 'function',
            'function_declaration': 'function',
            'method_definition': 'method',
            'method_declaration': 'method',
            'class_definition': 'class',
            'class_declaration': 'class',
            'variable_declaration': 'variable',
            'const_declaration': 'constant',
            'interface': 'interface',
            'enum': 'enum',
            'property_identifier': 'property',
            'field_declaration': 'field'
        }
        return kind_map.get(symbol_type, 'text')
    
    def _get_lsp_completion_kind(self, lsp_kind: int) -> str:
        """LSP 심볼 종류를 완성 종류로 변환"""
        # LSP SymbolKind enum 값들
        kind_map = {
            1: 'file',      # File
            2: 'module',    # Module
            3: 'namespace', # Namespace
            4: 'package',   # Package
            5: 'class',     # Class
            6: 'method',    # Method
            7: 'property',  # Property
            8: 'field',     # Field
            9: 'constructor', # Constructor
            10: 'enum',     # Enum
            11: 'interface', # Interface
            12: 'function', # Function
            13: 'variable', # Variable
            14: 'constant', # Constant
            15: 'string',   # String
            16: 'number',   # Number
            17: 'boolean',  # Boolean
            18: 'array',    # Array
            19: 'object',   # Object
            20: 'key',      # Key
            21: 'null',     # Null
            22: 'enumMember', # EnumMember
            23: 'struct',   # Struct
            24: 'event',    # Event
            25: 'operator', # Operator
            26: 'typeParameter' # TypeParameter
        }
        return kind_map.get(lsp_kind, 'text')
    
    def _deduplicate_and_sort_completions(self, completions: List[CompletionItem]) -> List[CompletionItem]:
        """완성 목록 중복 제거 및 정렬"""
        try:
            # 중복 제거 (label 기준)
            seen_labels = set()
            unique_completions = []
            
            for completion in completions:
                if completion.label not in seen_labels:
                    seen_labels.add(completion.label)
                    unique_completions.append(completion)
            
            # 정렬 (label 기준)
            unique_completions.sort(key=lambda x: x.label.lower())
            
            return unique_completions
            
        except Exception as e:
            logger.error(f"완성 목록 정렬 실패: {e}")
            return completions
    
    def clear_cache(self):
        """완성 캐시 초기화"""
        self._completion_cache.clear()
        logger.info("완성 캐시 초기화 완료")
    
    async def get_completion_details(self, filepath: str, position: Position, label: str) -> Optional[Dict[str, Any]]:
        """완성 아이템의 상세 정보 제공"""
        try:
            # LSP를 통한 상세 정보 가져오기
            if self.lsp_service:
                lsp_position = self.lsp_service.LSPPosition(
                    line=position.line,
                    character=position.character
                )
                
                # 시그니처 도움말 가져오기
                signature_help = await self.lsp_service.get_signature_help(filepath, lsp_position)
                if signature_help:
                    return {
                        'signatures': signature_help.signatures,
                        'active_signature': signature_help.active_signature,
                        'active_parameter': signature_help.active_parameter
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"완성 상세 정보 가져오기 실패: {e}")
            return None
