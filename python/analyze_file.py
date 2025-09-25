#!/usr/bin/env python3
"""
Continue Python 포팅 버전 - 파일 분석 스크립트
원본 Continue 프로젝트의 TypeScript 구현과 동일한 기능을 Python으로 구현
Tree-sitter와 LSP를 사용하여 Java, JavaScript, Python 소스코드를 분석

AST는 코드의 구문적 구조를 트리 형태로 표현:
- 구문적 구조: 코드의 형태적, 문법적 구조를 분석
- 트리 형태: 계층적, 중첩적 구조를 트리로 표현
- 노드와 엣지: 각 코드 요소를 노드로, 관계를 엣지로 표현
- 계층적 관계: 포함 관계와 형제 관계로 구조 표현
- 구조적 탐색: 트리 순회로 전체 코드 구조 분석
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict

# Continue Python Core 모듈 import
import sys
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from core import Core, CoreConfig
from continue_types import *
from util.tree_sitter_service import TreeSitterService
from util.lsp_service import LSPService
from semantic.semantic_unit_extractor import SemanticUnitExtractor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AstNode:
    """AST 노드 정보"""
    type: str
    text: str
    start_position: List[int]
    end_position: List[int]
    children_count: int

@dataclass
class AnalysisResult:
    """분석 결과"""
    filepath: str
    language: str
    ast_root: AstNode
    symbols: List[SymbolWithRange]
    analysis: Dict[str, Any]
    semantic_analysis: Optional[Dict[str, Any]] = None

class FileAnalyzer:
    """파일 분석기 클래스 - 원본 analyze-file.js의 Python 포팅"""
    
    def __init__(self):
        self.tree_sitter_service = TreeSitterService()
        self.lsp_service = LSPService()
        self.semantic_extractor = SemanticUnitExtractor()
        self.core = None
        
        logger.info("파일 분석기 초기화 완료")
    
    async def initialize(self):
        """분석기 초기화"""
        try:
            # Tree-sitter 초기화
            await self.tree_sitter_service.initialize()
            
            # LSP 초기화
            await self.lsp_service.initialize()
            
            # Core 초기화
            config = CoreConfig(
                workspace_paths=[os.getcwd()],
                enable_tree_sitter=True,
                enable_lsp=True,
                enable_autocomplete=True,
                enable_indexing=True
            )
            self.core = Core(config)
            await self.core.initialize()
            
            # 의미적 단위 추출기 초기화
            await self.semantic_extractor.initialize()
            
            logger.info("분석기 초기화 완료")
            
        except Exception as e:
            logger.error(f"분석기 초기화 실패: {e}")
            raise
    
    def get_language_from_extension(self, filepath: str) -> str:
        """파일 확장자로부터 언어 결정"""
        ext = Path(filepath).suffix.lstrip('.').lower()
        language_map = {
            'py': 'python',
            'java': 'java',
            'js': 'javascript',
            'jsx': 'javascript',
            'ts': 'typescript',
            'tsx': 'typescript',
            'cpp': 'cpp',
            'c': 'c',
            'go': 'go',
            'rs': 'rust'
        }
        return language_map.get(ext, 'unknown')
    
    async def analyze_file(self, filepath: str) -> AnalysisResult:
        """파일 분석 - 원본 analyzeFile 함수의 Python 포팅 + 요청하신 AST 분석 기능"""
        try:
            # 파일 내용 읽기
            with open(filepath, 'r', encoding='utf-8') as f:
                contents = f.read()
            
            # 언어 결정
            language = self.get_language_from_extension(filepath)
            
            # Tree-sitter AST 분석
            ast = await self.tree_sitter_service.get_ast(filepath, contents)
            
            # 심볼 추출
            symbols = await self.tree_sitter_service.get_symbols_for_file(filepath, contents)
            
            # AST 루트 노드 정보
            ast_root = AstNode(
                type=ast.type if ast else "module",
                text=ast.text.decode('utf8')[:100] + "..." if ast and len(ast.text) > 100 else (ast.text.decode('utf8') if ast else ""),
                start_position=[ast.start_point[0], ast.start_point[1]] if ast else [0, 0],
                end_position=[ast.end_point[0], ast.end_point[1]] if ast else [0, 0],
                children_count=len(ast.children) if ast else 0
            )
            
            # 요청하신 AST 분석 단계들 구현
            ast_metadata = self.tree_sitter_service.extract_ast_metadata(ast, filepath) if ast else {}
            structural_metrics = self.tree_sitter_service.get_structural_metrics(ast) if ast else {}
            
            # 의미적 단위 추출 (요청하신 모든 단계)
            semantic_result = await self.semantic_extractor.extract_semantic_units(filepath)
            semantic_analysis = {
                'semantic_units': [
                    {
                        'name': unit.name,
                        'type': unit.type,
                        'confidence': unit.confidence,
                        'relationships_count': len(unit.relationships),
                        'has_ast_mapping': unit.ast_mapping is not None
                    }
                    for unit in semantic_result.semantic_units
                ],
                'total_units': semantic_result.total_units,
                'analysis_metrics': semantic_result.analysis_metrics,
                'processing_time': semantic_result.processing_time
            }
            
            # 분석 통계 (기존 + 새로운 메트릭)
            analysis = {
                'total_nodes': self.tree_sitter_service.count_nodes(ast),
                'max_depth': self.tree_sitter_service.get_max_depth(ast),
                'node_types': self.tree_sitter_service.get_node_types(ast),
                'structural_metrics': structural_metrics,
                'ast_metadata': ast_metadata,
                'parsing_info': {
                    'language': language,
                    'file_size': len(contents),
                    'line_count': len(contents.split('\n')),
                    'parsing_success': ast is not None
                }
            }
            
            return AnalysisResult(
                filepath=filepath,
                language=language,
                ast_root=ast_root,
                symbols=symbols,
                analysis=analysis,
                semantic_analysis=semantic_analysis
            )
            
        except Exception as e:
            logger.error(f"파일 분석 실패 {filepath}: {e}")
            raise
    
    async def analyze_file_with_core(self, filepath: str) -> Dict[str, Any]:
        """Core를 사용한 파일 분석"""
        try:
            if not self.core:
                await self.initialize()
            
            # Core를 통한 분석
            result = await self.core.analyze_file(filepath)
            
            # 추가 정보 포함
            result['file_info'] = {
                'size': os.path.getsize(filepath),
                'modified': os.path.getmtime(filepath),
                'language': self.get_language_from_extension(filepath)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Core 파일 분석 실패 {filepath}: {e}")
            raise
    
    async def get_completions_for_file(self, filepath: str, position: Position) -> List[Dict[str, Any]]:
        """파일에 대한 자동완성 제공"""
        try:
            if not self.core:
                await self.initialize()
            
            return await self.core.get_completions(filepath, position)
            
        except Exception as e:
            logger.error(f"자동완성 실패: {e}")
            return []
    
    async def get_context_for_file(self, query: str, filepath: str) -> List[ContextItemWithId]:
        """파일에 대한 컨텍스트 제공"""
        try:
            if not self.core:
                await self.initialize()
            
            return await self.core.get_context(query, filepath)
            
        except Exception as e:
            logger.error(f"컨텍스트 제공 실패: {e}")
            return []
    
    async def shutdown(self):
        """분석기 종료"""
        try:
            if self.core:
                await self.core.shutdown()
            
            if self.lsp_service:
                await self.lsp_service.shutdown()
            
            logger.info("분석기 종료 완료")
            
        except Exception as e:
            logger.error(f"분석기 종료 실패: {e}")

async def main():
    """메인 함수 - 원본 main 함수의 Python 포팅"""
    if len(sys.argv) < 2:
        print("사용법: python analyze_file.py <파일경로> [출력파일]")
        print("예시: python analyze_file.py test_example.py result.json")
        sys.exit(1)
    
    filepath = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 파일 존재 확인
    if not os.path.exists(filepath):
        print(f"파일을 찾을 수 없습니다: {filepath}")
        sys.exit(1)
    
    print(f"분석 중: {filepath}")
    
    try:
        # 파일 분석기 생성 및 초기화
        analyzer = FileAnalyzer()
        await analyzer.initialize()
        
        # 파일 분석
        result = await analyzer.analyze_file(filepath)
        
        # 결과를 딕셔너리로 변환
        result_dict = asdict(result)
        
        # JSON으로 직렬화
        json_result = json.dumps(result_dict, indent=2, ensure_ascii=False)
        
        if output_file:
            # 파일로 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_result)
            print(f"결과가 저장되었습니다: {output_file}")
        else:
            # 콘솔에 출력
            print(json_result)
        
        # 분석기 종료
        await analyzer.shutdown()
            
    except Exception as e:
        print(f"실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
