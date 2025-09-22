"""
Continue Core 클래스
원본 TypeScript Core 클래스의 Python 포팅
Tree-sitter와 LSP를 사용하여 소스코드 분석 및 자동완성 제공
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from config.config_handler import ConfigHandler
from indexing.codebase_indexer import CodebaseIndexer
from autocomplete.completion_provider import CompletionProvider
from util.tree_sitter_service import TreeSitterService
from util.lsp_service import LSPService
from llm.llm_provider import LLMProvider
from context.providers import ContextProvider
from continue_types import *

logger = logging.getLogger(__name__)

@dataclass
class CoreConfig:
    """Core 설정"""
    workspace_paths: List[str]
    enable_tree_sitter: bool = True
    enable_lsp: bool = True
    enable_autocomplete: bool = True
    enable_indexing: bool = True

class Core:
    """Continue Core 클래스 - 원본 TypeScript Core의 Python 포팅"""
    
    def __init__(self, config: CoreConfig):
        self.config = config
        self.config_handler = ConfigHandler()
        self.tree_sitter_service = TreeSitterService() if config.enable_tree_sitter else None
        self.lsp_service = LSPService() if config.enable_lsp else None
        self.completion_provider = CompletionProvider(
            self.tree_sitter_service, 
            self.lsp_service
        ) if config.enable_autocomplete else None
        self.codebase_indexer = CodebaseIndexer(
            self.tree_sitter_service
        ) if config.enable_indexing else None
        self.llm_provider = LLMProvider()
        self.context_provider = ContextProvider()
        
        logger.info("Continue Core 초기화 완료")
    
    async def initialize(self):
        """Core 초기화"""
        try:
            # Tree-sitter 초기화
            if self.tree_sitter_service:
                await self.tree_sitter_service.initialize()
            
            # LSP 초기화
            if self.lsp_service:
                await self.lsp_service.initialize()
            
            # 코드베이스 인덱싱
            if self.codebase_indexer:
                await self.codebase_indexer.index_workspaces(self.config.workspace_paths)
            
            logger.info("Core 초기화 완료")
            
        except Exception as e:
            logger.error(f"Core 초기화 실패: {e}")
            raise
    
    async def analyze_file(self, filepath: str) -> Dict[str, Any]:
        """파일 분석 - 원본과 동일한 분석 기능 제공"""
        try:
            result = {}
            
            # Tree-sitter 분석
            if self.tree_sitter_service:
                ast = await self.tree_sitter_service.get_ast(filepath)
                symbols = await self.tree_sitter_service.get_symbols_for_file(filepath)
                result['tree_sitter'] = {
                    'ast': ast,
                    'symbols': symbols,
                    'node_count': self.tree_sitter_service.count_nodes(ast) if ast else 0,
                    'max_depth': self.tree_sitter_service.get_max_depth(ast) if ast else 0,
                    'node_types': self.tree_sitter_service.get_node_types(ast) if ast else {}
                }
            
            # LSP 분석
            if self.lsp_service:
                # 파일의 첫 번째 위치에서 정의 찾기
                position = Position(line=0, character=0)
                definitions = await self.lsp_service.get_definitions(filepath, position)
                references = await self.lsp_service.get_references(filepath, position)
                result['lsp'] = {
                    'definitions': definitions,
                    'references': references
                }
            
            return result
            
        except Exception as e:
            logger.error(f"파일 분석 실패 {filepath}: {e}")
            raise
    
    async def get_completions(self, filepath: str, position: Position) -> List[Dict[str, Any]]:
        """자동완성 제공"""
        try:
            if not self.completion_provider:
                return []
            
            return await self.completion_provider.get_completions(filepath, position)
            
        except Exception as e:
            logger.error(f"자동완성 실패: {e}")
            return []
    
    async def get_context(self, query: str, filepath: str) -> List[ContextItemWithId]:
        """컨텍스트 제공"""
        try:
            return await self.context_provider.get_context(query, filepath)
            
        except Exception as e:
            logger.error(f"컨텍스트 제공 실패: {e}")
            return []
    
    async def get_symbols_for_many_files(self, filepaths: List[str]) -> FileSymbolMap:
        """여러 파일에서 심볼 추출 - 원본 getSymbolsForManyFiles 함수 포팅"""
        try:
            if not self.tree_sitter_service:
                return {}
            
            return await self.tree_sitter_service.get_symbols_for_many_files(filepaths)
            
        except Exception as e:
            logger.error(f"다중 파일 심볼 추출 실패: {e}")
            return {}
    
    async def get_ast_for_file(self, filepath: str, contents: Optional[str] = None) -> Optional[Any]:
        """파일에 대한 AST 반환 - 원본 getAst 함수 포팅"""
        try:
            if not self.tree_sitter_service:
                return None
            
            return await self.tree_sitter_service.get_ast(filepath, contents)
            
        except Exception as e:
            logger.error(f"AST 생성 실패 {filepath}: {e}")
            return None
    
    async def get_tree_path_at_cursor(self, filepath: str, cursor_index: int) -> List[Any]:
        """커서 위치의 트리 경로 반환 - 원본 getTreePathAtCursor 함수 포팅"""
        try:
            if not self.tree_sitter_service:
                return []
            
            ast = await self.tree_sitter_service.get_ast(filepath)
            if not ast:
                return []
            
            return self.tree_sitter_service.get_tree_path_at_cursor(ast, cursor_index)
            
        except Exception as e:
            logger.error(f"트리 경로 추출 실패: {e}")
            return []
    
    async def shutdown(self):
        """Core 종료"""
        try:
            if self.lsp_service:
                await self.lsp_service.shutdown()
            
            logger.info("Core 종료 완료")
            
        except Exception as e:
            logger.error(f"Core 종료 실패: {e}")