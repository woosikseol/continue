#!/usr/bin/env python3
"""
Continue Python 프로젝트 전체 AST 분석 스크립트
요청하신 모든 단계를 프로젝트 내 여러 폴더와 파일에 대해 실행
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import time

# Continue Python Core 모듈 import
import sys
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from analyze_file import FileAnalyzer, AnalysisResult
from continue_types import *

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ProjectAnalysisResult:
    """프로젝트 전체 분석 결과"""
    project_path: str
    total_files: int
    successful_analyses: int
    failed_analyses: int
    analysis_results: List[AnalysisResult]
    project_metrics: Dict[str, Any]
    language_distribution: Dict[str, int]
    structural_summary: Dict[str, Any]
    semantic_summary: Optional[Dict[str, Any]] = None

class ProjectAnalyzer:
    """프로젝트 전체 AST 분석기"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.analyzer = FileAnalyzer()
        self.supported_extensions = {
            '.py', '.js', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
            '.go', '.rs', '.php', '.rb', '.lua', '.html', '.css', '.json'
        }
        self.exclude_dirs = {
            'node_modules', '__pycache__', '.git', '.vscode', '.idea',
            'build', 'dist', 'target', 'vendor', '.pytest_cache'
        }
        
        logger.info(f"프로젝트 분석기 초기화: {self.project_path}")
    
    async def initialize(self):
        """분석기 초기화"""
        await self.analyzer.initialize()
        logger.info("프로젝트 분석기 초기화 완료")
    
    def get_target_files(self) -> List[Path]:
        """분석 대상 파일 목록 수집"""
        target_files = []
        
        def collect_files(directory: Path):
            try:
                for item in directory.iterdir():
                    if item.is_file():
                        if item.suffix.lower() in self.supported_extensions:
                            target_files.append(item)
                    elif item.is_dir():
                        if item.name not in self.exclude_dirs:
                            collect_files(item)
            except PermissionError:
                logger.warning(f"권한 없음: {directory}")
            except Exception as e:
                logger.warning(f"디렉토리 스캔 실패 {directory}: {e}")
        
        collect_files(self.project_path)
        logger.info(f"분석 대상 파일 {len(target_files)}개 발견")
        return target_files
    
    async def analyze_project(self) -> ProjectAnalysisResult:
        """프로젝트 전체 AST 분석 - 요청하신 모든 단계 실행"""
        start_time = time.time()
        
        # 1. 대상 파일 수집
        target_files = self.get_target_files()
        
        if not target_files:
            logger.warning("분석할 파일이 없습니다.")
            return ProjectAnalysisResult(
                project_path=str(self.project_path),
                total_files=0,
                successful_analyses=0,
                failed_analyses=0,
                analysis_results=[],
                project_metrics={},
                language_distribution={},
                structural_summary={}
            )
        
        # 2. 파일별 AST 분석 실행
        analysis_results = []
        successful_count = 0
        failed_count = 0
        
        logger.info(f"프로젝트 AST 분석 시작: {len(target_files)}개 파일")
        
        for i, file_path in enumerate(target_files):
            try:
                logger.info(f"분석 중 ({i+1}/{len(target_files)}): {file_path.name}")
                
                # 1.1 파싱 단계 (Tree-sitter 파싱)
                # 1.2 AST 노드 추출
                # 1.3 트리 구조 구성
                # 1.4 구조적 메트릭 계산
                result = await self.analyzer.analyze_file(str(file_path))
                analysis_results.append(result)
                successful_count += 1
                
                # 진행 상황 로깅
                if (i + 1) % 10 == 0:
                    logger.info(f"진행률: {i+1}/{len(target_files)} ({(i+1)/len(target_files)*100:.1f}%)")
                
            except Exception as e:
                logger.error(f"파일 분석 실패 {file_path}: {e}")
                failed_count += 1
        
        # 3. 프로젝트 전체 메트릭 계산
        project_metrics = self._calculate_project_metrics(analysis_results)
        language_distribution = self._calculate_language_distribution(analysis_results)
        structural_summary = self._calculate_structural_summary(analysis_results)
        
        # 4. 의미적 분석 요약 계산
        semantic_summary = self._calculate_semantic_summary(analysis_results)
        
        analysis_time = time.time() - start_time
        
        logger.info(f"프로젝트 AST 분석 완료: {analysis_time:.2f}초")
        logger.info(f"성공: {successful_count}, 실패: {failed_count}")
        
        return ProjectAnalysisResult(
            project_path=str(self.project_path),
            total_files=len(target_files),
            successful_analyses=successful_count,
            failed_analyses=failed_count,
            analysis_results=analysis_results,
            project_metrics=project_metrics,
            language_distribution=language_distribution,
            structural_summary=structural_summary,
            semantic_summary=semantic_summary
        )
    
    def _calculate_project_metrics(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """프로젝트 전체 메트릭 계산"""
        if not results:
            return {}
        
        total_nodes = sum(r.analysis.get('total_nodes', 0) for r in results)
        max_depth = max(r.analysis.get('max_depth', 0) for r in results)
        total_files = len(results)
        
        # 노드 타입 통계
        all_node_types = {}
        for result in results:
            node_types = result.analysis.get('node_types', {})
            for node_type, count in node_types.items():
                all_node_types[node_type] = all_node_types.get(node_type, 0) + count
        
        # 복잡도 통계
        complexities = []
        for result in results:
            structural_metrics = result.analysis.get('structural_metrics', {})
            if 'complexity' in structural_metrics:
                complexities.append(structural_metrics['complexity'])
        
        return {
            'total_nodes': total_nodes,
            'max_depth': max_depth,
            'average_nodes_per_file': total_nodes / total_files if total_files > 0 else 0,
            'total_node_types': len(all_node_types),
            'most_common_node_types': dict(sorted(all_node_types.items(), key=lambda x: x[1], reverse=True)[:10]),
            'complexity_stats': {
                'average': sum(complexities) / len(complexities) if complexities else 0,
                'max': max(complexities) if complexities else 0,
                'min': min(complexities) if complexities else 0
            },
            'file_size_stats': {
                'total_size': sum(r.analysis.get('parsing_info', {}).get('file_size', 0) for r in results),
                'average_size': sum(r.analysis.get('parsing_info', {}).get('file_size', 0) for r in results) / total_files if total_files > 0 else 0
            }
        }
    
    def _calculate_language_distribution(self, results: List[AnalysisResult]) -> Dict[str, int]:
        """언어별 분포 계산"""
        distribution = {}
        for result in results:
            language = result.language
            distribution[language] = distribution.get(language, 0) + 1
        return distribution
    
    def _calculate_structural_summary(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """구조적 요약 계산"""
        if not results:
            return {}
        
        # 모든 구조적 메트릭 수집
        all_metrics = []
        for result in results:
            structural_metrics = result.analysis.get('structural_metrics', {})
            if structural_metrics:
                all_metrics.append(structural_metrics)
        
        if not all_metrics:
            return {}
        
        # 평균값 계산
        avg_metrics = {}
        for key in ['complexity', 'average_children_per_node', 'leaf_node_ratio', 'branching_factor']:
            values = [m.get(key, 0) for m in all_metrics if key in m]
            if values:
                avg_metrics[f'average_{key}'] = sum(values) / len(values)
                avg_metrics[f'max_{key}'] = max(values)
                avg_metrics[f'min_{key}'] = min(values)
        
        return {
            'files_with_structural_metrics': len(all_metrics),
            'average_metrics': avg_metrics,
            'complexity_distribution': self._get_complexity_distribution(all_metrics)
        }
    
    def _get_complexity_distribution(self, metrics: List[Dict[str, Any]]) -> Dict[str, int]:
        """복잡도 분포 계산"""
        distribution = {'low': 0, 'medium': 0, 'high': 0, 'very_high': 0}
        
        for metric in metrics:
            complexity = metric.get('complexity', 0)
            if complexity <= 5:
                distribution['low'] += 1
            elif complexity <= 15:
                distribution['medium'] += 1
            elif complexity <= 30:
                distribution['high'] += 1
            else:
                distribution['very_high'] += 1
        
        return distribution
    
    def _calculate_semantic_summary(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """의미적 분석 요약 계산"""
        try:
            if not results:
                return {}
            
            # 의미적 분석이 있는 결과들만 필터링
            semantic_results = [r for r in results if r.semantic_analysis]
            
            if not semantic_results:
                return {}
            
            # 전체 의미적 단위 수
            total_semantic_units = sum(
                r.semantic_analysis.get('total_units', 0) 
                for r in semantic_results
            )
            
            # 신뢰도 분포
            all_confidence_distribution = {
                'high': 0,
                'medium': 0,
                'low': 0
            }
            
            # 타입 분포
            all_type_distribution = {}
            
            for result in semantic_results:
                semantic_analysis = result.semantic_analysis
                
                # 신뢰도 분포 누적
                confidence_dist = semantic_analysis.get('analysis_metrics', {}).get('confidence_distribution', {})
                for level, count in confidence_dist.items():
                    all_confidence_distribution[level] += count
                
                # 타입 분포 누적
                type_dist = semantic_analysis.get('analysis_metrics', {}).get('type_distribution', {})
                for unit_type, count in type_dist.items():
                    all_type_distribution[unit_type] = all_type_distribution.get(unit_type, 0) + count
            
            # 평균 처리 시간
            avg_processing_time = sum(
                r.semantic_analysis.get('processing_time', 0) 
                for r in semantic_results
            ) / len(semantic_results) if semantic_results else 0
            
            return {
                'total_semantic_units': total_semantic_units,
                'files_with_semantic_analysis': len(semantic_results),
                'confidence_distribution': all_confidence_distribution,
                'type_distribution': all_type_distribution,
                'average_processing_time': avg_processing_time,
                'semantic_analysis_coverage': len(semantic_results) / len(results) if results else 0
            }
            
        except Exception as e:
            logger.error(f"의미적 분석 요약 계산 실패: {e}")
            return {}
    
    async def shutdown(self):
        """분석기 종료"""
        await self.analyzer.shutdown()
        logger.info("프로젝트 분석기 종료 완료")

async def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("사용법: python analyze_project.py <프로젝트경로> [출력파일]")
        print("예시: python analyze_project.py /path/to/project result.json")
        sys.exit(1)
    
    project_path = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 프로젝트 경로 확인
    if not os.path.exists(project_path):
        print(f"프로젝트 경로를 찾을 수 없습니다: {project_path}")
        sys.exit(1)
    
    print(f"프로젝트 AST 분석 시작: {project_path}")
    
    try:
        # 프로젝트 분석기 생성 및 초기화
        analyzer = ProjectAnalyzer(project_path)
        await analyzer.initialize()
        
        # 프로젝트 전체 AST 분석 실행
        result = await analyzer.analyze_project()
        
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
        
        # 분석 요약 출력
        print(f"\n=== 분석 요약 ===")
        print(f"총 파일 수: {result.total_files}")
        print(f"성공한 분석: {result.successful_analyses}")
        print(f"실패한 분석: {result.failed_analyses}")
        print(f"언어 분포: {result.language_distribution}")
        print(f"총 AST 노드 수: {result.project_metrics.get('total_nodes', 0)}")
        print(f"최대 깊이: {result.project_metrics.get('max_depth', 0)}")
        
        # 의미적 분석 요약 출력
        if result.semantic_summary:
            print(f"\n=== 의미적 분석 요약 ===")
            print(f"총 의미적 단위 수: {result.semantic_summary.get('total_semantic_units', 0)}")
            print(f"의미적 분석 파일 수: {result.semantic_summary.get('files_with_semantic_analysis', 0)}")
            print(f"의미적 분석 커버리지: {result.semantic_summary.get('semantic_analysis_coverage', 0):.2%}")
            print(f"평균 처리 시간: {result.semantic_summary.get('average_processing_time', 0):.2f}초")
        
        # 분석기 종료
        await analyzer.shutdown()
            
    except Exception as e:
        print(f"실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
