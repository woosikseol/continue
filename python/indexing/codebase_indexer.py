"""
코드베이스 인덱서
원본 TypeScript CodebaseIndexer의 Python 포팅
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from util.tree_sitter_service import TreeSitterService
from continue_types import FileSymbolMap

logger = logging.getLogger(__name__)

class CodebaseIndexer:
    """코드베이스 인덱서 - 원본 TypeScript CodebaseIndexer의 Python 포팅"""
    
    def __init__(self, tree_sitter_service: Optional[TreeSitterService]):
        self.tree_sitter_service = tree_sitter_service
        self.indexed_files: Dict[str, Any] = {}
        
        logger.info("코드베이스 인덱서 초기화 완료")
    
    async def index_workspaces(self, workspace_paths: List[str]):
        """워크스페이스 인덱싱"""
        try:
            for workspace_path in workspace_paths:
                await self._index_workspace(workspace_path)
            
            logger.info(f"워크스페이스 인덱싱 완료: {len(workspace_paths)}개")
            
        except Exception as e:
            logger.error(f"워크스페이스 인덱싱 실패: {e}")
            raise
    
    async def _index_workspace(self, workspace_path: str):
        """워크스페이스 인덱싱"""
        try:
            workspace = Path(workspace_path)
            if not workspace.exists():
                logger.warning(f"워크스페이스가 존재하지 않습니다: {workspace_path}")
                return
            
            # 지원하는 파일 확장자들
            supported_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs'}
            
            # 파일들 수집
            files_to_index = []
            for file_path in workspace.rglob('*'):
                if file_path.is_file() and file_path.suffix in supported_extensions:
                    files_to_index.append(str(file_path))
            
            # 병렬로 인덱싱
            if self.tree_sitter_service:
                symbols_map = await self.tree_sitter_service.get_symbols_for_many_files(files_to_index)
                self.indexed_files.update(symbols_map)
            
            logger.info(f"워크스페이스 인덱싱 완료: {workspace_path} ({len(files_to_index)}개 파일)")
            
        except Exception as e:
            logger.error(f"워크스페이스 인덱싱 실패 {workspace_path}: {e}")
    
    def get_indexed_symbols(self) -> FileSymbolMap:
        """인덱싱된 심볼들 반환"""
        return self.indexed_files
    
    def get_symbols_for_file(self, filepath: str) -> List[Any]:
        """파일의 심볼들 반환"""
        return self.indexed_files.get(filepath, [])
    
    def clear_index(self):
        """인덱스 초기화"""
        self.indexed_files.clear()
        logger.info("인덱스 초기화 완료")
