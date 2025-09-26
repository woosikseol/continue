"""
종합 분석기
요청하신 모든 절차를 통합한 프로젝트 전체 분석기
1.1-1.4 AST 구조 분석 + 2.1-2.4 의미적 단위 분석
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict

from util.tree_sitter_service import TreeSitterService
from semantic.semantic_unit_extractor import SemanticUnitExtractor, SemanticAnalysisResult
from continue_types import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

@dataclass
class ComprehensiveAnalysisResult:
    """종합 분석 결과"""
    project_path: str
    total_files: int
    analyzed_files: int
    total_processing_time: float
    
    # 1.1-1.4 AST 구조 분석 결과
    ast_analysis: Dict[str, Any]
    
    # 2.1-2.4 의미적 단위 분석 결과  
    semantic_analysis: Dict[str, Any]
    
    # 통합 메트릭
    project_metrics: Dict[str, Any]
    
    # 파일별 상세 결과
    file_results: Dict[str, Dict[str, Any]]

class ComprehensiveAnalyzer:
    """종합 분석기 - 요청하신 모든 절차 통합"""
    
    def __init__(self):
        self.tree_sitter_service = TreeSitterService()
        self.semantic_extractor = SemanticUnitExtractor()
        self.supported_extensions = set(SUPPORTED_LANGUAGES.keys())
        
        logger.info("종합 분석기 초기화 완료")
    
    async def initialize(self):
        """분석기 초기화"""
        await self.tree_sitter_service.initialize()
        await self.semantic_extractor.initialize()
        logger.info("종합 분석기 서비스 초기화 완료")
    
    async def analyze_project(self, project_path: str, output_file: Optional[str] = None) -> ComprehensiveAnalysisResult:
        """프로젝트 전체 종합 분석"""
        start_time = time.time()
        
        logger.info(f"프로젝트 종합 분석 시작: {project_path}")
        
        # 분석 대상 파일 수집
        files_to_analyze = self._collect_files(project_path)
        
        logger.info(f"분석 대상 파일: {len(files_to_analyze)}개")
        
        # 파일별 분석 결과
        file_results = {}
        ast_results = {}
        semantic_results = {}
        
        analyzed_count = 0
        
        for filepath in files_to_analyze:
            try:
                logger.info(f"분석 중: {filepath}")
                
                # 1.1-1.4 AST 구조 분석
                ast_result = await self._analyze_ast_structure(filepath)
                ast_results[filepath] = ast_result
                
                # 2.1-2.4 의미적 단위 분석
                semantic_result = await self._analyze_semantic_units(filepath)
                semantic_results[filepath] = semantic_result
                
                # 통합 결과
                file_results[filepath] = {
                    'ast_analysis': ast_result,
                    'semantic_analysis': semantic_result,
                    'file_metrics': self._calculate_file_metrics(ast_result, semantic_result)
                }
                
                analyzed_count += 1
                
            except Exception as e:
                logger.error(f"파일 분석 실패 {filepath}: {e}")
                file_results[filepath] = {
                    'error': str(e),
                    'ast_analysis': None,
                    'semantic_analysis': None
                }
        
        # 프로젝트 전체 메트릭 계산
        project_metrics = self._calculate_project_metrics(ast_results, semantic_results)
        
        # 종합 분석 결과 생성
        result = ComprehensiveAnalysisResult(
            project_path=project_path,
            total_files=len(files_to_analyze),
            analyzed_files=analyzed_count,
            total_processing_time=time.time() - start_time,
            ast_analysis=self._aggregate_ast_results(ast_results),
            semantic_analysis=self._aggregate_semantic_results(semantic_results),
            project_metrics=project_metrics,
            file_results=file_results
        )
        
        # 결과 저장
        if output_file:
            await self._save_results(result, output_file)
        
        logger.info(f"프로젝트 종합 분석 완료: {result.total_processing_time:.2f}초")
        
        return result
    
    def _collect_files(self, project_path: str) -> List[str]:
        """분석 대상 파일 수집"""
        files = []
        project_dir = Path(project_path)
        
        if project_dir.is_file():
            # 단일 파일
            if project_dir.suffix.lstrip('.').lower() in self.supported_extensions:
                files.append(str(project_dir))
        else:
            # 디렉토리 전체
            for ext in self.supported_extensions:
                files.extend(project_dir.rglob(f"*.{ext}"))
            files = [str(f) for f in files]
        
        return files
    
    async def _analyze_ast_structure(self, filepath: str) -> Dict[str, Any]:
        """1.1-1.4 AST 구조 분석"""
        try:
            # 1.1 파싱 단계
            root_node = await self.tree_sitter_service.get_ast(filepath)
            if not root_node:
                return {'error': 'AST 파싱 실패', 'parsing_success': False}
            
            # 1.2-1.4 노드 추출, 트리 구조, 메트릭 계산
            ast_metadata = self.tree_sitter_service.extract_ast_metadata(root_node, filepath)
            
            return {
                'parsing_success': True,
                'root_node_type': root_node.type,
                'metadata': ast_metadata,
                'file_info': {
                    'filepath': str(filepath),
                    'language': str(self.tree_sitter_service.get_full_language_name(filepath) or 'unknown')
                }
            }
            
        except Exception as e:
            logger.error(f"AST 구조 분석 실패 {filepath}: {e}")
            return {'error': str(e), 'parsing_success': False}
    
    async def _analyze_semantic_units(self, filepath: str) -> Dict[str, Any]:
        """2.1-2.4 의미적 단위 분석"""
        try:
            # 의미적 단위 추출
            result = await self.semantic_extractor.extract_semantic_units(filepath)
            
            # Tree-sitter Node 객체를 직렬화 가능한 형태로 변환
            safe_semantic_units = []
            for unit in result.semantic_units:
                safe_unit = {
                    'name': unit.name,
                    'type': unit.type,
                    'semantic_type': {
                        'name': unit.semantic_type.name,
                        'type': unit.semantic_type.type,
                        'context': unit.semantic_type.context,
                        'language_specific': unit.semantic_type.language_specific,
                        'confidence': unit.semantic_type.confidence
                    },
                    'ast_mapping': {
                        'symbol_name': unit.ast_mapping.symbol_name if unit.ast_mapping else None,
                        'mapping_type': unit.ast_mapping.mapping_type if unit.ast_mapping else None,
                        'mapping_confidence': unit.ast_mapping.mapping_confidence if unit.ast_mapping else 0.0,
                        'position_match': unit.ast_mapping.position_match if unit.ast_mapping else False,
                        'range_match': unit.ast_mapping.range_match if unit.ast_mapping else False,
                        'context_match': unit.ast_mapping.context_match if unit.ast_mapping else False
                    } if unit.ast_mapping else None,
                    'relationships': [
                        {
                            'source': rel.source,
                            'target': rel.target,
                            'relationship_type': rel.relationship_type,
                            'strength': rel.strength,
                            'context': rel.context,
                            'metadata': rel.metadata
                        } for rel in unit.relationships
                    ],
                    'confidence': unit.confidence,
                    'metadata': unit.metadata
                }
                safe_semantic_units.append(safe_unit)
            
            return {
                'extraction_success': True,
                'semantic_units': safe_semantic_units,
                'total_units': result.total_units,
                'analysis_metrics': result.analysis_metrics,
                'processing_time': result.processing_time
            }
            
        except Exception as e:
            logger.error(f"의미적 단위 분석 실패 {filepath}: {e}")
            return {'error': str(e), 'extraction_success': False}
    
    def _calculate_file_metrics(self, ast_result: Dict[str, Any], semantic_result: Dict[str, Any]) -> Dict[str, Any]:
        """파일별 통합 메트릭 계산 - 의미적 분석 품질 지표 포함"""
        metrics = {
            'analysis_success': ast_result.get('parsing_success', False) and semantic_result.get('extraction_success', False),
            'complexity_indicators': {},
            'quality_scores': {}
        }
        
        # AST 메트릭 통합
        if ast_result.get('metadata', {}).get('structural_metrics'):
            ast_metrics = ast_result['metadata']['structural_metrics']
            metrics['complexity_indicators'].update({
                'ast_complexity': ast_metrics.get('complexity_score', 0),
                'max_depth': ast_metrics.get('max_depth', 0),
                'total_nodes': ast_metrics.get('total_nodes', 0),
                'cyclomatic_complexity': ast_metrics.get('cyclomatic_complexity', 0)
            })
            
            if 'code_quality_metrics' in ast_metrics:
                # AST 기반 품질 점수를 가져오되, 가중치 조정을 위해 별도 저장
                ast_quality = ast_metrics['code_quality_metrics']
                metrics['quality_scores']['ast_quality'] = ast_quality.get('overall_quality', 0)
                metrics['quality_scores']['complexity_score'] = ast_quality.get('complexity_score', 0)
                metrics['quality_scores']['maintainability_score'] = ast_quality.get('maintainability_score', 0)
                metrics['quality_scores']['structural_balance'] = ast_quality.get('structural_balance', 50)
        
        # 의미적 분석 메트릭 통합 및 품질 점수 계산
        semantic_quality_score = 0
        if semantic_result.get('analysis_metrics'):
            semantic_metrics = semantic_result['analysis_metrics']
            metrics['complexity_indicators'].update({
                'semantic_units_count': semantic_result.get('total_units', 0),
                'relationships_count': semantic_metrics.get('total_relationships', 0)
            })
            
            # 의미적 품질 점수 계산
            semantic_quality_score = self._calculate_semantic_quality_score(semantic_result, semantic_metrics)
            metrics['quality_scores']['semantic_quality'] = semantic_quality_score
        
        # 통합 품질 점수 계산 (의미적 분석 결과 반영)
        ast_quality = metrics['quality_scores'].get('ast_quality', 0)
        
        # AST 품질과 의미적 품질의 가중 평균
        # 의미적 분석이 성공한 경우 더 높은 가중치 부여
        if semantic_result.get('extraction_success', False):
            # 의미적 분석 성공 시: AST 30%, 의미적 70%
            overall_quality = ast_quality * 0.3 + semantic_quality_score * 0.7
        else:
            # 의미적 분석 실패 시: AST 품질만 사용하되 페널티 적용
            overall_quality = ast_quality * 0.5  # 50% 페널티
        
        metrics['quality_scores']['overall_quality'] = round(overall_quality, 2)
        
        # 전체 복잡도 점수 계산 (기존 로직 유지)
        ast_complexity = metrics['complexity_indicators'].get('ast_complexity', 0)
        semantic_complexity = metrics['complexity_indicators'].get('relationships_count', 0) * 0.1
        overall_complexity = (ast_complexity + semantic_complexity) / 2
        metrics['quality_scores']['overall_complexity'] = round(overall_complexity, 2)
        
        return metrics
    
    def _calculate_semantic_quality_score(self, semantic_result: Dict[str, Any], semantic_metrics: Dict[str, Any]) -> float:
        """의미적 분석 품질 점수 계산"""
        try:
            quality_score = 0.0
            
            # 1. 매핑 정확도 (40% 가중치) - 가장 중요한 지표
            mapping_accuracy = semantic_metrics.get('mapping_accuracy', {})
            accuracy_rate = mapping_accuracy.get('accuracy_rate', 0.0) * 100  # 0-100 스케일로 변환
            quality_score += accuracy_rate * 0.4
            
            # 2. 의미적 단위 신뢰도 (25% 가중치)
            average_confidence = semantic_metrics.get('average_confidence', 0.0) * 100  # 0-100 스케일로 변환
            quality_score += average_confidence * 0.25
            
            # 3. 새로운 품질 지표 사용 (개선된 계산)
            quality_metrics = semantic_metrics.get('quality_metrics', {})
            if quality_metrics:
                # 이미 계산된 종합 품질 점수 사용
                semantic_overall_quality = quality_metrics.get('overall_quality_score', 0)
                quality_score = semantic_overall_quality
            else:
                # 기존 방식으로 계산 (fallback)
                total_relationships = semantic_metrics.get('total_relationships', 0)
                total_units = semantic_result.get('total_units', 1)  # 0으로 나누기 방지
                relationship_density = min(total_relationships / total_units, 10) * 10  # 관계 밀도 (최대 100점)
                quality_score += relationship_density * 0.2
                
                # 4. 신뢰도 분포 품질 (15% 가중치)
                confidence_dist = semantic_metrics.get('confidence_distribution', {})
                high_confidence_ratio = confidence_dist.get('high', 0) / total_units if total_units > 0 else 0
                confidence_quality = high_confidence_ratio * 100
                quality_score += confidence_quality * 0.15
            
            return round(min(quality_score, 100.0), 2)  # 최대 100점으로 제한
            
        except Exception as e:
            logger.error(f"의미적 품질 점수 계산 실패: {e}")
            return 0.0
    
    def _calculate_project_metrics(self, ast_results: Dict[str, Any], semantic_results: Dict[str, Any]) -> Dict[str, Any]:
        """프로젝트 전체 메트릭 계산"""
        metrics = {
            'total_ast_nodes': 0,
            'total_semantic_units': 0,
            'total_relationships': 0,
            'average_complexity': 0.0,
            'language_distribution': {},
            'quality_distribution': {
                'high_quality': 0,
                'medium_quality': 0,
                'low_quality': 0
            }
        }
        
        complexity_scores = []
        integrated_quality_scores = []
        
        # 통합 품질 점수 계산을 위해 파일별로 AST와 의미적 분석 결과를 매칭
        for filepath in ast_results.keys():
            ast_result = ast_results.get(filepath, {})
            semantic_result = semantic_results.get(filepath, {})
            
            # 파일별 통합 메트릭 계산
            file_metrics = self._calculate_file_metrics(ast_result, semantic_result)
            
            # AST 노드 수 집계
            if ast_result.get('metadata', {}).get('structural_metrics'):
                ast_metrics = ast_result['metadata']['structural_metrics']
                metrics['total_ast_nodes'] += ast_metrics.get('total_nodes', 0)
                
                # 기존 AST 품질 점수도 수집 (비교용)
                if 'code_quality_metrics' in ast_metrics:
                    ast_quality_score = ast_metrics['code_quality_metrics'].get('overall_quality', 0)
                    complexity_scores.append(ast_quality_score)
            
            # 통합 품질 점수 사용
            integrated_quality = file_metrics['quality_scores'].get('overall_quality', 0)
            integrated_quality_scores.append(integrated_quality)
            
            # 품질 분포 계산 (통합 점수 기준)
            if integrated_quality >= 80:
                metrics['quality_distribution']['high_quality'] += 1
            elif integrated_quality >= 60:
                metrics['quality_distribution']['medium_quality'] += 1
            else:
                metrics['quality_distribution']['low_quality'] += 1
            
            # 언어 분포 (LanguageName을 문자열로 변환)
            language = ast_result.get('file_info', {}).get('language', 'unknown')
            language_str = str(language) if language else 'unknown'
            metrics['language_distribution'][language_str] = metrics['language_distribution'].get(language_str, 0) + 1
        
        # 의미적 분석 결과 집계
        for filepath, semantic_result in semantic_results.items():
            if semantic_result.get('extraction_success', False):
                metrics['total_semantic_units'] += semantic_result.get('total_units', 0)
                
                if semantic_result.get('analysis_metrics'):
                    metrics['total_relationships'] += semantic_result['analysis_metrics'].get('total_relationships', 0)
        
        # 평균 품질 점수 계산 (통합 품질 점수 사용)
        if integrated_quality_scores:
            metrics['average_complexity'] = round(sum(integrated_quality_scores) / len(integrated_quality_scores), 2)
        
        # 추가 메트릭: AST 전용 품질 점수와 통합 품질 점수 비교
        if complexity_scores and integrated_quality_scores:
            ast_avg = sum(complexity_scores) / len(complexity_scores)
            integrated_avg = sum(integrated_quality_scores) / len(integrated_quality_scores)
            metrics['quality_improvement'] = round(integrated_avg - ast_avg, 2)
        
        return metrics
    
    def _aggregate_ast_results(self, ast_results: Dict[str, Any]) -> Dict[str, Any]:
        """AST 분석 결과 집계"""
        aggregated = {
            'total_files_parsed': len([r for r in ast_results.values() if r.get('parsing_success')]),
            'parsing_failures': len([r for r in ast_results.values() if not r.get('parsing_success')]),
            'node_type_distribution': {},
            'structural_patterns': {}
        }
        
        # 노드 타입 분포 집계
        for ast_result in ast_results.values():
            if ast_result.get('metadata', {}).get('structural_metrics', {}).get('node_type_distribution'):
                node_dist = ast_result['metadata']['structural_metrics']['node_type_distribution']
                for node_type, count in node_dist.items():
                    aggregated['node_type_distribution'][node_type] = aggregated['node_type_distribution'].get(node_type, 0) + count
        
        return aggregated
    
    def _aggregate_semantic_results(self, semantic_results: Dict[str, Any]) -> Dict[str, Any]:
        """의미적 분석 결과 집계"""
        aggregated = {
            'total_files_analyzed': len([r for r in semantic_results.values() if r.get('extraction_success')]),
            'analysis_failures': len([r for r in semantic_results.values() if not r.get('extraction_success')]),
            'semantic_unit_types': {},
            'relationship_types': {}
        }
        
        # 의미적 단위 타입 분포 집계
        for semantic_result in semantic_results.values():
            if semantic_result.get('semantic_units'):
                for unit in semantic_result['semantic_units']:
                    unit_type = unit.get('type', 'unknown')
                    aggregated['semantic_unit_types'][unit_type] = aggregated['semantic_unit_types'].get(unit_type, 0) + 1
        
        return aggregated
    
    async def _save_results(self, result: ComprehensiveAnalysisResult, output_file: str):
        """분석 결과 저장"""
        try:
            # dataclass를 dict로 변환
            result_dict = asdict(result)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2)
            
            logger.info(f"분석 결과 저장 완료: {output_file}")
            
        except Exception as e:
            logger.error(f"결과 저장 실패: {e}")
    
    async def shutdown(self):
        """분석기 종료"""
        await self.semantic_extractor.shutdown()
        logger.info("종합 분석기 종료 완료")

# 메인 실행 함수
async def main():
    """메인 실행 함수"""
    import sys
    
    if len(sys.argv) < 2:
        print("사용법: python comprehensive_analyzer.py <프로젝트_경로> [출력_파일]")
        return
    
    project_path = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "comprehensive_analysis.json"
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    analyzer = ComprehensiveAnalyzer()
    
    try:
        await analyzer.initialize()
        result = await analyzer.analyze_project(project_path, output_file)
        
        print(f"\n=== 종합 분석 결과 ===")
        print(f"프로젝트 경로: {result.project_path}")
        print(f"전체 파일 수: {result.total_files}")
        print(f"분석 완료 파일: {result.analyzed_files}")
        print(f"처리 시간: {result.total_processing_time:.2f}초")
        print(f"전체 AST 노드: {result.project_metrics['total_ast_nodes']:,}개")
        print(f"전체 의미적 단위: {result.project_metrics['total_semantic_units']:,}개")
        print(f"전체 관계: {result.project_metrics['total_relationships']:,}개")
        print(f"평균 품질 점수: {result.project_metrics['average_complexity']}")
        print(f"결과 저장: {output_file}")
        
    finally:
        await analyzer.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
