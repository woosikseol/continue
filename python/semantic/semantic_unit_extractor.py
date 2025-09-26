"""
의미적 단위 추출기
요청하신 모든 단계를 통합한 메인 분석기
2.1 LSP 기반 심볼 추출, 2.2 의미적 타입 결정, 2.3 AST 노드와 심볼 매핑, 2.4 의미적 관계 설정
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

from .semantic_analyzer import SemanticAnalyzer, SemanticType
from .ast_symbol_mapper import ASTSymbolMapper, MappingResult
from .relationship_analyzer import RelationshipAnalyzer, Relationship
from util.lsp_service import LSPService
from util.tree_sitter_service import TreeSitterService

logger = logging.getLogger(__name__)

@dataclass
class SemanticUnit:
    """의미적 단위"""
    name: str
    type: str
    semantic_type: SemanticType
    ast_mapping: Optional[MappingResult]
    relationships: List[Relationship]
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class SemanticAnalysisResult:
    """의미적 분석 결과"""
    filepath: str
    semantic_units: List[SemanticUnit]
    total_units: int
    analysis_metrics: Dict[str, Any]
    processing_time: float

class SemanticUnitExtractor:
    """의미적 단위 추출기 - 요청하신 모든 단계를 통합한 메인 분석기"""
    
    def __init__(self):
        self.lsp_service = LSPService()
        self.tree_sitter_service = TreeSitterService()
        self.semantic_analyzer = SemanticAnalyzer()
        self.ast_symbol_mapper = ASTSymbolMapper()
        self.relationship_analyzer = RelationshipAnalyzer()
        
        logger.info("의미적 단위 추출기 초기화 완료")
    
    async def initialize(self):
        """추출기 초기화"""
        try:
            await self.lsp_service.initialize()
            await self.tree_sitter_service.initialize()
            logger.info("의미적 단위 추출기 초기화 완료")
            
        except Exception as e:
            logger.error(f"의미적 단위 추출기 초기화 실패: {e}")
            raise
    
    async def extract_semantic_units(self, filepath: str) -> SemanticAnalysisResult:
        """의미적 단위 추출 - 요청하신 모든 단계 실행"""
        import time
        start_time = time.time()
        
        try:
            logger.info(f"의미적 단위 추출 시작: {filepath}")
            
            # 2.1 LSP 기반 심볼 추출
            logger.info("2.1 LSP 기반 심볼 추출 시작")
            semantic_symbols = await self.lsp_service.get_semantic_symbols(filepath)
            logger.info(f"LSP 심볼 추출 완료: {len(semantic_symbols)}개 심볼")
            
            # 2.2 의미적 타입 결정
            logger.info("2.2 의미적 타입 결정 시작")
            semantic_types = []
            for symbol in semantic_symbols:
                semantic_type = await self.semantic_analyzer.determine_semantic_type(symbol, filepath)
                semantic_types.append(semantic_type)
            logger.info(f"의미적 타입 결정 완료: {len(semantic_types)}개 타입")
            
            # 2.3 AST 노드와 심볼 매핑
            logger.info("2.3 AST 노드와 심볼 매핑 시작")
            ast = await self.tree_sitter_service.get_ast(filepath)
            if ast:
                mappings = await self.ast_symbol_mapper.map_ast_to_symbols(ast, semantic_symbols, filepath)
                logger.info(f"AST-심볼 매핑 완료: {len(mappings)}개 매핑")
            else:
                mappings = []
                logger.warning("AST 생성 실패, 매핑 건너뜀")
            
            # 2.4 의미적 관계 설정
            logger.info("2.4 의미적 관계 설정 시작")
            relationships = await self.relationship_analyzer.analyze_semantic_relationships(semantic_symbols, filepath)
            logger.info(f"의미적 관계 설정 완료: {len(relationships)}개 관계")
            
            # 의미적 단위 생성
            semantic_units = await self._create_semantic_units(
                semantic_symbols, semantic_types, mappings, relationships, filepath
            )
            
            # 분석 메트릭 계산
            analysis_metrics = await self._calculate_analysis_metrics(
                semantic_units, mappings, relationships, filepath
            )
            
            processing_time = time.time() - start_time
            
            result = SemanticAnalysisResult(
                filepath=filepath,
                semantic_units=semantic_units,
                total_units=len(semantic_units),
                analysis_metrics=analysis_metrics,
                processing_time=processing_time
            )
            
            logger.info(f"의미적 단위 추출 완료: {processing_time:.2f}초, {len(semantic_units)}개 단위")
            
            return result
            
        except Exception as e:
            logger.error(f"의미적 단위 추출 실패: {e}")
            raise
    
    async def _create_semantic_units(
        self, 
        semantic_symbols: List[Dict[str, Any]], 
        semantic_types: List[SemanticType], 
        mappings: List[MappingResult], 
        relationships: List[Relationship],
        filepath: str
    ) -> List[SemanticUnit]:
        """의미적 단위 생성"""
        try:
            semantic_units = []
            
            for i, symbol in enumerate(semantic_symbols):
                # 해당 심볼의 의미적 타입 찾기
                semantic_type = semantic_types[i] if i < len(semantic_types) else None
                
                # 해당 심볼의 AST 매핑 찾기
                ast_mapping = None
                for mapping in mappings:
                    if mapping.symbol_name == symbol['name']:
                        ast_mapping = mapping
                        break
                
                # 해당 심볼의 관계들 찾기
                symbol_relationships = []
                for relationship in relationships:
                    if (relationship.source == symbol['name'] or 
                        relationship.target == symbol['name']):
                        symbol_relationships.append(relationship)
                
                # 신뢰도 계산
                confidence = self._calculate_unit_confidence(semantic_type, ast_mapping, symbol_relationships)
                
                # 메타데이터 생성
                metadata = {
                    'symbol_info': symbol,
                    'file': filepath,
                    'relationships_count': len(symbol_relationships),
                    'has_ast_mapping': ast_mapping is not None,
                    'semantic_type_confidence': semantic_type.confidence if semantic_type else 0.0
                }
                
                semantic_unit = SemanticUnit(
                    name=symbol['name'],
                    type=symbol.get('type', 'unknown'),
                    semantic_type=semantic_type,
                    ast_mapping=ast_mapping,
                    relationships=symbol_relationships,
                    confidence=confidence,
                    metadata=metadata
                )
                
                semantic_units.append(semantic_unit)
            
            return semantic_units
            
        except Exception as e:
            logger.error(f"의미적 단위 생성 실패: {e}")
            return []
    
    def _calculate_unit_confidence(
        self, 
        semantic_type: Optional[SemanticType], 
        ast_mapping: Optional[MappingResult], 
        relationships: List[Relationship]
    ) -> float:
        """개선된 단위 신뢰도 계산"""
        confidence = 0.0
        
        # 1. 의미적 타입 신뢰도 (35% 가중치)
        if semantic_type:
            confidence += semantic_type.confidence * 0.35
        else:
            # 타입이 없으면 기본 페널티
            confidence += 0.1
        
        # 2. AST 매핑 신뢰도 (40% 가중치) - 가장 중요
        if ast_mapping:
            mapping_score = ast_mapping.mapping_confidence
            
            # 매핑 품질 보너스
            if ast_mapping.position_match and ast_mapping.range_match:
                mapping_score = min(mapping_score * 1.2, 1.0)  # 20% 보너스
            elif ast_mapping.position_match or ast_mapping.range_match:
                mapping_score = min(mapping_score * 1.1, 1.0)  # 10% 보너스
                
            confidence += mapping_score * 0.4
        else:
            # 매핑이 없으면 큰 페널티
            confidence += 0.05
        
        # 3. 관계 신뢰도 (25% 가중치)
        if relationships:
            # 관계의 수와 품질 모두 고려
            relationship_count_score = min(len(relationships) / 5.0, 1.0)  # 5개 관계가 최적
            avg_relationship_strength = sum(r.strength for r in relationships) / len(relationships)
            
            # 관계 점수 = 수량 점수 * 0.3 + 품질 점수 * 0.7
            relationship_score = relationship_count_score * 0.3 + avg_relationship_strength * 0.7
            confidence += relationship_score * 0.25
        
        # 최종 신뢰도 정규화 및 품질 등급 적용
        final_confidence = min(confidence, 1.0)
        
        # 품질 등급별 조정
        if final_confidence >= 0.9:
            final_confidence = min(final_confidence * 1.05, 1.0)  # 최고 품질 보너스
        elif final_confidence < 0.3:
            final_confidence *= 0.8  # 저품질 페널티
        
        return round(final_confidence, 3)
    
    async def _calculate_analysis_metrics(
        self, 
        semantic_units: List[SemanticUnit], 
        mappings: List[MappingResult], 
        relationships: List[Relationship],
        filepath: str
    ) -> Dict[str, Any]:
        """분석 메트릭 계산"""
        try:
            # 기본 통계
            total_units = len(semantic_units)
            total_mappings = len(mappings)
            total_relationships = len(relationships)
            
            # 신뢰도 분포
            confidence_levels = {
                'high': len([u for u in semantic_units if u.confidence >= 0.8]),
                'medium': len([u for u in semantic_units if 0.5 <= u.confidence < 0.8]),
                'low': len([u for u in semantic_units if u.confidence < 0.5])
            }
            
            # 타입별 분포
            type_distribution = {}
            for unit in semantic_units:
                unit_type = unit.type
                type_distribution[unit_type] = type_distribution.get(unit_type, 0) + 1
            
            # 관계 타입별 분포
            relationship_type_distribution = {}
            for relationship in relationships:
                rel_type = relationship.relationship_type
                relationship_type_distribution[rel_type] = relationship_type_distribution.get(rel_type, 0) + 1
            
            # 매핑 정확도
            mapping_accuracy = await self.ast_symbol_mapper.get_mapping_statistics(filepath)
            
            # 관계 통계
            relationship_stats = await self.relationship_analyzer.get_relationship_statistics(filepath)
            
            # 품질 지표 계산
            quality_metrics = self._calculate_quality_metrics(semantic_units, mappings, relationships)
            
            return {
                'total_units': total_units,
                'total_mappings': total_mappings,
                'total_relationships': total_relationships,
                'confidence_distribution': confidence_levels,
                'type_distribution': type_distribution,
                'relationship_type_distribution': relationship_type_distribution,
                'mapping_accuracy': mapping_accuracy,
                'relationship_stats': relationship_stats,
                'average_confidence': sum(u.confidence for u in semantic_units) / total_units if total_units > 0 else 0,
                'quality_metrics': quality_metrics  # 새로운 품질 지표 추가
            }
            
        except Exception as e:
            logger.error(f"분석 메트릭 계산 실패: {e}")
            return {}
    
    def _calculate_quality_metrics(
        self, 
        semantic_units: List[SemanticUnit], 
        mappings: List[MappingResult], 
        relationships: List[Relationship]
    ) -> Dict[str, Any]:
        """품질 지표 계산"""
        try:
            total_units = len(semantic_units)
            if total_units == 0:
                return {}
            
            # 1. 신뢰도 품질 지표
            confidences = [u.confidence for u in semantic_units]
            confidence_quality = {
                'average': sum(confidences) / len(confidences),
                'median': sorted(confidences)[len(confidences) // 2],
                'std_dev': self._calculate_std_dev(confidences),
                'high_confidence_ratio': len([c for c in confidences if c >= 0.8]) / total_units
            }
            
            # 2. 매핑 품질 지표
            mapping_quality = {
                'mapping_ratio': len(mappings) / total_units if total_units > 0 else 0,
                'high_quality_mappings': len([m for m in mappings if m.mapping_confidence >= 0.8]),
                'position_match_ratio': len([m for m in mappings if m.position_match]) / len(mappings) if mappings else 0,
                'range_match_ratio': len([m for m in mappings if m.range_match]) / len(mappings) if mappings else 0
            }
            
            # 3. 관계 품질 지표
            relationship_quality = {
                'relationship_density': len(relationships) / total_units if total_units > 0 else 0,
                'average_strength': sum(r.strength for r in relationships) / len(relationships) if relationships else 0,
                'strong_relationships': len([r for r in relationships if r.strength >= 0.8]),
                'relationship_diversity': len(set(r.relationship_type for r in relationships))
            }
            
            # 4. 종합 품질 점수
            overall_quality = (
                confidence_quality['average'] * 0.4 +
                mapping_quality['mapping_ratio'] * 0.3 +
                relationship_quality['relationship_density'] * 0.2 +
                confidence_quality['high_confidence_ratio'] * 0.1
            ) * 100  # 0-100 스케일로 변환
            
            return {
                'confidence_quality': confidence_quality,
                'mapping_quality': mapping_quality,
                'relationship_quality': relationship_quality,
                'overall_quality_score': round(overall_quality, 2)
            }
            
        except Exception as e:
            logger.error(f"품질 지표 계산 실패: {e}")
            return {}
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """표준편차 계산"""
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return round(variance ** 0.5, 3)
    
    async def analyze_multiple_files(self, filepaths: List[str]) -> Dict[str, SemanticAnalysisResult]:
        """여러 파일에 대한 의미적 단위 추출"""
        try:
            results = {}
            
            for i, filepath in enumerate(filepaths):
                logger.info(f"파일 분석 중 ({i+1}/{len(filepaths)}): {filepath}")
                
                try:
                    result = await self.extract_semantic_units(filepath)
                    results[filepath] = result
                    
                except Exception as e:
                    logger.error(f"파일 분석 실패 {filepath}: {e}")
                    continue
            
            logger.info(f"다중 파일 분석 완료: {len(results)}개 파일 성공")
            
            return results
            
        except Exception as e:
            logger.error(f"다중 파일 분석 실패: {e}")
            return {}
    
    async def get_project_semantic_summary(self, results: Dict[str, SemanticAnalysisResult]) -> Dict[str, Any]:
        """프로젝트 전체 의미적 요약"""
        try:
            total_files = len(results)
            total_units = sum(r.total_units for r in results.values())
            total_processing_time = sum(r.processing_time for r in results.values())
            
            # 전체 타입 분포
            all_type_distribution = {}
            for result in results.values():
                type_dist = result.analysis_metrics.get('type_distribution', {})
                for unit_type, count in type_dist.items():
                    all_type_distribution[unit_type] = all_type_distribution.get(unit_type, 0) + count
            
            # 전체 신뢰도 분포
            all_confidence_distribution = {
                'high': sum(r.analysis_metrics.get('confidence_distribution', {}).get('high', 0) for r in results.values()),
                'medium': sum(r.analysis_metrics.get('confidence_distribution', {}).get('medium', 0) for r in results.values()),
                'low': sum(r.analysis_metrics.get('confidence_distribution', {}).get('low', 0) for r in results.values())
            }
            
            return {
                'total_files': total_files,
                'total_units': total_units,
                'total_processing_time': total_processing_time,
                'average_units_per_file': total_units / total_files if total_files > 0 else 0,
                'type_distribution': all_type_distribution,
                'confidence_distribution': all_confidence_distribution,
                'files_analyzed': list(results.keys())
            }
            
        except Exception as e:
            logger.error(f"프로젝트 의미적 요약 생성 실패: {e}")
            return {}
    
    async def shutdown(self):
        """추출기 종료"""
        try:
            await self.lsp_service.shutdown()
            logger.info("의미적 단위 추출기 종료 완료")
            
        except Exception as e:
            logger.error(f"의미적 단위 추출기 종료 실패: {e}")
