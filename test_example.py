#!/usr/bin/env python3
"""
Continue Python 포팅 테스트 예시
원본 analyze-file.js와 동일한 기능을 테스트
"""

import asyncio
import json
from pathlib import Path

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

async def test_tree_sitter_analysis():
    """Tree-sitter 분석 테스트"""
    print("=== Tree-sitter 분석 테스트 ===")
    
    try:
        # Tree-sitter 서비스 초기화
        tree_sitter_service = TreeSitterService()
        await tree_sitter_service.initialize()
        
        # 테스트 파일 경로
        test_file = __file__  # 현재 파일을 테스트
        
        # AST 분석
        ast = await tree_sitter_service.get_ast(test_file)
        if ast:
            print(f"AST 루트 타입: {ast.type}")
            print(f"AST 노드 수: {tree_sitter_service.count_nodes(ast)}")
            print(f"AST 최대 깊이: {tree_sitter_service.get_max_depth(ast)}")
            print(f"AST 노드 타입들: {list(tree_sitter_service.get_node_types(ast).keys())[:10]}")
        
        # 심볼 추출
        symbols = await tree_sitter_service.get_symbols_for_file(test_file)
        print(f"추출된 심볼 수: {len(symbols)}")
        for symbol in symbols[:5]:  # 처음 5개만 출력
            print(f"  - {symbol.name} ({symbol.type})")
        
        print("Tree-sitter 분석 테스트 완료\n")
        
    except Exception as e:
        print(f"Tree-sitter 분석 테스트 실패: {e}\n")

async def test_core_analysis():
    """Core 분석 테스트"""
    print("=== Core 분석 테스트 ===")
    
    try:
        # Core 초기화
        config = CoreConfig(
            workspace_paths=[str(Path(__file__).parent)],
            enable_tree_sitter=True,
            enable_lsp=False,  # LSP는 환경 설정이 필요하므로 비활성화
            enable_autocomplete=True,
            enable_indexing=True
        )
        core = Core(config)
        await core.initialize()
        
        # 테스트 파일 분석
        test_file = __file__
        result = await core.analyze_file(test_file)
        
        print(f"분석 결과:")
        print(f"  - Tree-sitter 노드 수: {result['tree_sitter']['node_count']}")
        print(f"  - Tree-sitter 최대 깊이: {result['tree_sitter']['max_depth']}")
        print(f"  - Tree-sitter 노드 타입 수: {len(result['tree_sitter']['node_types'])}")
        
        # 자동완성 테스트
        position = Position(line=10, character=5)
        completions = await core.get_completions(test_file, position)
        print(f"  - 자동완성 항목 수: {len(completions)}")
        
        # 컨텍스트 테스트
        context_items = await core.get_context("function", test_file)
        print(f"  - 컨텍스트 항목 수: {len(context_items)}")
        
        # 종료
        await core.shutdown()
        
        print("Core 분석 테스트 완료\n")
        
    except Exception as e:
        print(f"Core 분석 테스트 실패: {e}\n")

async def test_file_analysis():
    """파일 분석 테스트"""
    print("=== 파일 분석 테스트 ===")
    
    try:
        from analyze_file import FileAnalyzer
        
        # 파일 분석기 초기화
        analyzer = FileAnalyzer()
        await analyzer.initialize()
        
        # 현재 파일 분석
        test_file = __file__
        result = await analyzer.analyze_file(test_file)
        
        print(f"파일 분석 결과:")
        print(f"  - 파일: {result.filepath}")
        print(f"  - 언어: {result.language}")
        print(f"  - AST 루트 타입: {result.ast_root.type}")
        print(f"  - AST 자식 수: {result.ast_root.children_count}")
        print(f"  - 총 노드 수: {result.analysis['total_nodes']}")
        print(f"  - 최대 깊이: {result.analysis['max_depth']}")
        print(f"  - 심볼 수: {len(result.symbols)}")
        
        # 심볼 정보 출력
        for symbol in result.symbols[:3]:  # 처음 3개만
            print(f"    - {symbol.name} ({symbol.type}) at line {symbol.range.start.line}")
        
        # 종료
        await analyzer.shutdown()
        
        print("파일 분석 테스트 완료\n")
        
    except Exception as e:
        print(f"파일 분석 테스트 실패: {e}\n")

async def main():
    """메인 테스트 함수"""
    print("Continue Python 포팅 테스트 시작\n")
    
    # Tree-sitter 분석 테스트
    await test_tree_sitter_analysis()
    
    # Core 분석 테스트
    await test_core_analysis()
    
    # 파일 분석 테스트
    await test_file_analysis()
    
    print("모든 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(main())
