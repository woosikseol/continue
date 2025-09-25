#!/usr/bin/env python3
"""
Continue Python 포팅 테스트 예시 - 복잡한 구조
Tree-sitter와 LSP 분석을 위한 다양한 구문 요소 포함
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

# 외부 라이브러리 import
import requests
import numpy as np
from datetime import datetime

# Continue Python Core import
import sys
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from core import Core, CoreConfig
from continue_types import Position
from util.tree_sitter_service import TreeSitterService
from util.lsp_service import LSPService

# 전역 변수
GLOBAL_CONFIG = {
    "debug": True,
    "version": "1.0.0",
    "features": ["tree_sitter", "lsp", "autocomplete"]
}

# 데코레이터
def timing_decorator(func):
    """실행 시간 측정 데코레이터"""
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        print(f"{func.__name__} 실행 시간: {(end_time - start_time).total_seconds():.2f}초")
        return result
    return wrapper

# 추상 클래스
class BaseAnalyzer(ABC):
    """분석기 기본 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        self.results = []
    
    @abstractmethod
    async def analyze(self, data: Any) -> Dict[str, Any]:
        """분석 수행"""
        pass
    
    def get_results(self) -> List[Dict[str, Any]]:
        """결과 반환"""
        return self.results

# 구체 클래스
class TreeSitterAnalyzer(BaseAnalyzer):
    """Tree-sitter 분석기"""
    
    def __init__(self):
        super().__init__("TreeSitterAnalyzer")
        self.service = TreeSitterService()
    
    async def analyze(self, filepath: str) -> Dict[str, Any]:
        """Tree-sitter 분석 수행"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                contents = f.read()
            
            ast = await self.service.get_ast(filepath, contents)
            symbols = await self.service.get_symbols_for_file(filepath, contents)
            
            return {
                "ast_nodes": self.service.count_nodes(ast),
                "max_depth": self.service.get_max_depth(ast),
                "symbols_count": len(symbols),
                "node_types": self.service.get_node_types(ast)
            }
        except Exception as e:
            return {"error": str(e)}

class LSPAnalyzer(BaseAnalyzer):
    """LSP 분석기"""
    
    def __init__(self):
        super().__init__("LSPAnalyzer")
        self.service = LSPService()
    
    async def analyze(self, filepath: str) -> Dict[str, Any]:
        """LSP 분석 수행"""
        try:
            await self.service.initialize()
            
            # 문서 심볼 가져오기
            symbols = await self.service.get_document_symbols(filepath)
            
            return {
                "document_symbols": len(symbols),
                "symbols": [{"name": s.name, "kind": s.kind} for s in symbols]
            }
        except Exception as e:
            return {"error": str(e)}

# 열거형
class AnalysisType:
    """분석 타입"""
    TREE_SITTER = "tree_sitter"
    LSP = "lsp"
    COMBINED = "combined"

# 예외 클래스
class AnalysisError(Exception):
    """분석 오류"""
    def __init__(self, message: str, code: int = 0):
        self.message = message
        self.code = code
        super().__init__(self.message)

# 메인 클래스
class ContinueAnalyzer:
    """Continue 분석기 메인 클래스"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or GLOBAL_CONFIG
        self.tree_sitter_analyzer = TreeSitterAnalyzer()
        self.lsp_analyzer = LSPAnalyzer()
        self.core = None
    
    @timing_decorator
    async def initialize(self):
        """분석기 초기화"""
        try:
            # Tree-sitter 초기화
            await self.tree_sitter_analyzer.service.initialize()
            
            # LSP 초기화
            await self.lsp_analyzer.service.initialize()
            
            # Core 초기화
            core_config = CoreConfig(
                workspace_paths=[str(current_dir)],
                enable_tree_sitter=True,
                enable_lsp=True,
                enable_autocomplete=True,
                enable_indexing=True
            )
            self.core = Core(core_config)
            await self.core.initialize()
            
            print("Continue 분석기 초기화 완료")
            
        except Exception as e:
            raise AnalysisError(f"초기화 실패: {e}", 1001)
    
    async def analyze_file(self, filepath: str, analysis_type: str = AnalysisType.COMBINED) -> Dict[str, Any]:
        """파일 분석"""
        try:
            results = {
                "filepath": filepath,
                "analysis_type": analysis_type,
                "timestamp": datetime.now().isoformat(),
                "config": self.config
            }
            
            if analysis_type in [AnalysisType.TREE_SITTER, AnalysisType.COMBINED]:
                tree_sitter_result = await self.tree_sitter_analyzer.analyze(filepath)
                results["tree_sitter"] = tree_sitter_result
            
            if analysis_type in [AnalysisType.LSP, AnalysisType.COMBINED]:
                lsp_result = await self.lsp_analyzer.analyze(filepath)
                results["lsp"] = lsp_result
            
            return results
            
        except Exception as e:
            raise AnalysisError(f"파일 분석 실패: {e}", 1002)
    
    async def get_completions(self, filepath: str, position: Position) -> List[Dict[str, Any]]:
        """자동완성 제공"""
        try:
            if not self.core:
                await self.initialize()
            
            return await self.core.get_completions(filepath, position)
        except Exception as e:
            print(f"자동완성 실패: {e}")
            return []
    
    async def get_context(self, query: str, filepath: str) -> List[Dict[str, Any]]:
        """컨텍스트 제공"""
        try:
            if not self.core:
                await self.initialize()
            
            return await self.core.get_context(query, filepath)
        except Exception as e:
            print(f"컨텍스트 제공 실패: {e}")
            return []
    
    async def shutdown(self):
        """분석기 종료"""
        try:
            if self.core:
                await self.core.shutdown()
            print("분석기 종료 완료")
        except Exception as e:
            print(f"종료 실패: {e}")

# 유틸리티 함수들
def calculate_complexity(symbols: List[Dict[str, Any]]) -> int:
    """복잡도 계산"""
    return len(symbols) * 2 + 10

def format_analysis_result(result: Dict[str, Any]) -> str:
    """분석 결과 포맷팅"""
    return json.dumps(result, indent=2, ensure_ascii=False)

# 비동기 함수들
async def test_tree_sitter_analysis():
    """Tree-sitter 분석 테스트"""
    print("=== Tree-sitter 분석 테스트 ===")
    
    try:
        analyzer = ContinueAnalyzer()
        await analyzer.initialize()
        
        # 현재 파일 분석
        result = await analyzer.analyze_file(__file__, AnalysisType.TREE_SITTER)
        print(f"Tree-sitter 분석 결과: {format_analysis_result(result)}")
        
        await analyzer.shutdown()
        print("Tree-sitter 분석 테스트 완료\n")
        
    except AnalysisError as e:
        print(f"Tree-sitter 분석 테스트 실패: {e.message} (코드: {e.code})\n")

async def test_lsp_analysis():
    """LSP 분석 테스트"""
    print("=== LSP 분석 테스트 ===")
    
    try:
        analyzer = ContinueAnalyzer()
        await analyzer.initialize()
        
        # 현재 파일 분석
        result = await analyzer.analyze_file(__file__, AnalysisType.LSP)
        print(f"LSP 분석 결과: {format_analysis_result(result)}")
        
        await analyzer.shutdown()
        print("LSP 분석 테스트 완료\n")
        
    except AnalysisError as e:
        print(f"LSP 분석 테스트 실패: {e.message} (코드: {e.code})\n")

async def test_combined_analysis():
    """통합 분석 테스트"""
    print("=== 통합 분석 테스트 ===")
    
    try:
        analyzer = ContinueAnalyzer()
        await analyzer.initialize()
        
        # 현재 파일 분석
        result = await analyzer.analyze_file(__file__, AnalysisType.COMBINED)
        print(f"통합 분석 결과: {format_analysis_result(result)}")
        
        # 자동완성 테스트
        position = Position(line=50, character=10)
        completions = await analyzer.get_completions(__file__, position)
        print(f"자동완성 항목 수: {len(completions)}")
        
        # 컨텍스트 테스트
        context_items = await analyzer.get_context("function", __file__)
        print(f"컨텍스트 항목 수: {len(context_items)}")
        
        await analyzer.shutdown()
        print("통합 분석 테스트 완료\n")
        
    except AnalysisError as e:
        print(f"통합 분석 테스트 실패: {e.message} (코드: {e.code})\n")

# 메인 실행 함수
async def main():
    """메인 함수"""
    print("Continue Python 포팅 테스트 시작")
    print("=" * 50)
    
    # 각종 분석 테스트 실행
    await test_tree_sitter_analysis()
    await test_lsp_analysis()
    await test_combined_analysis()
    
    print("모든 테스트 완료!")

# 스크립트 실행
if __name__ == "__main__":
    asyncio.run(main())