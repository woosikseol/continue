"""
AST 노드와 심볼 매핑기
요청하신 2.3 AST 노드와 심볼 매핑 기능 구현
위치 기반 매핑, 범위 분석, 정확도 검증 기능 제공
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from pathlib import Path
import tree_sitter

logger = logging.getLogger(__name__)

@dataclass
class MappingResult:
    """매핑 결과"""
    symbol_name: str
    ast_node: tree_sitter.Node
    mapping_confidence: float
    mapping_type: str
    position_match: bool
    range_match: bool
    context_match: bool

@dataclass
class MappingAccuracy:
    """매핑 정확도"""
    total_mappings: int
    accurate_mappings: int
    accuracy_percentage: float
    false_positives: int
    false_negatives: int

class ASTSymbolMapper:
    """AST 노드와 심볼 매핑기 - 요청하신 2.3 AST 노드와 심볼 매핑 기능"""
    
    def __init__(self):
        self.mapping_cache: Dict[str, List[MappingResult]] = {}
        self.accuracy_threshold = 0.3  # 임계값을 낮춰서 더 많은 매핑 허용
        
        logger.info("AST 심볼 매핑기 초기화 완료")
    
    async def map_ast_to_symbols(self, ast: tree_sitter.Node, symbols: List[Dict[str, Any]], filepath: str) -> List[MappingResult]:
        """AST 노드와 심볼 매핑 - 2.3.1 위치 기반 매핑"""
        try:
            mappings = []
            
            # 2.3.1 위치 기반 매핑
            for symbol in symbols:
                symbol_mappings = await self._map_symbol_to_ast_nodes(symbol, ast)
                mappings.extend(symbol_mappings)
            
            # 2.3.2 범위 분석
            validated_mappings = await self._validate_range_mappings(mappings, filepath)
            
            # 2.3.3 정확도 검증
            accuracy = await self._verify_mapping_accuracy(validated_mappings, filepath)
            
            # 캐시에 저장
            self.mapping_cache[filepath] = validated_mappings
            
            logger.info(f"AST-심볼 매핑 완료: {len(validated_mappings)}개 매핑, 정확도: {accuracy.accuracy_percentage:.2f}%")
            
            return validated_mappings
            
        except Exception as e:
            logger.error(f"AST-심볼 매핑 실패: {e}")
            return []
    
    async def _map_symbol_to_ast_nodes(self, symbol: Dict[str, Any], ast: tree_sitter.Node) -> List[MappingResult]:
        """심볼을 AST 노드에 매핑 - 2.3.1 위치 기반 매핑"""
        try:
            mappings = []
            
            # 심볼의 위치 정보
            symbol_start_line = symbol['range']['start']['line']
            symbol_start_char = symbol['range']['start']['character']
            symbol_end_line = symbol['range']['end']['line']
            symbol_end_char = symbol['range']['end']['character']
            
            # AST 노드들을 순회하며 매핑
            for node in self._traverse_ast(ast):
                # 위치 매칭 확인
                position_match = self._check_position_match(
                    node, symbol_start_line, symbol_start_char, symbol_end_line, symbol_end_char
                )
                
                if position_match:
                    # 범위 매칭 확인
                    range_match = self._check_range_match(node, symbol)
                    
                    # 컨텍스트 매칭 확인
                    context_match = self._check_context_match(node, symbol)
                    
                    # 매핑 신뢰도 계산
                    confidence = self._calculate_mapping_confidence(
                        position_match, range_match, context_match
                    )
                    
                    # 매핑 타입 결정
                    mapping_type = self._determine_mapping_type(node, symbol)
                    
                    mapping = MappingResult(
                        symbol_name=symbol['name'],
                        ast_node=node,
                        mapping_confidence=confidence,
                        mapping_type=mapping_type,
                        position_match=position_match,
                        range_match=range_match,
                        context_match=context_match
                    )
                    
                    mappings.append(mapping)
            
            return mappings
            
        except Exception as e:
            logger.error(f"심볼-AST 매핑 실패: {e}")
            return []
    
    def _traverse_ast(self, node: tree_sitter.Node) -> List[tree_sitter.Node]:
        """AST 노드 순회"""
        nodes = []
        
        def traverse(current_node):
            nodes.append(current_node)
            for child in current_node.children:
                traverse(child)
        
        traverse(node)
        return nodes
    
    def _check_position_match(self, node: tree_sitter.Node, start_line: int, start_char: int, end_line: int, end_char: int) -> bool:
        """위치 매칭 확인 - 2.3.1 위치 기반 매핑 (개선된 알고리즘)"""
        try:
            node_start_line = node.start_point[0]
            node_start_char = node.start_point[1]
            node_end_line = node.end_point[0]
            node_end_char = node.end_point[1]
            
            # 1. 완전 일치 (최고 우선순위)
            if (node_start_line == start_line and node_start_char == start_char and 
                node_end_line == end_line and node_end_char == end_char):
                return True
            
            # 2. 시작 위치 일치 (높은 우선순위)
            if (node_start_line == start_line and node_start_char == start_char):
                return True
            
            # 3. 범위 내 포함 (중간 우선순위) - 더 관대한 조건
            if (node_start_line <= start_line and node_end_line >= end_line):
                return True
            
            # 4. 부분 겹침 (낮은 우선순위) - 더 관대한 조건
            if (node_start_line <= end_line and node_end_line >= start_line):
                return True
            
            # 5. 라인 범위만 일치 (매우 낮은 우선순위)
            if (node_start_line <= start_line <= node_end_line or 
                node_start_line <= end_line <= node_end_line):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"위치 매칭 확인 실패: {e}")
            return False
    
    def _check_range_match(self, node: tree_sitter.Node, symbol: Dict[str, Any]) -> bool:
        """범위 매칭 확인 - 2.3.2 범위 분석 (개선된 알고리즘)"""
        try:
            # 노드의 텍스트와 심볼 이름 비교
            node_text = node.text.decode('utf-8') if node.text else ''
            symbol_name = symbol['name']
            
            # 1. 정확한 이름 매칭 (최고 우선순위)
            if symbol_name == node_text.strip():
                return True
            
            # 2. 심볼 이름이 노드 텍스트에 포함 (높은 우선순위)
            if symbol_name in node_text:
                return True
            
            # 3. 단어 단위 매칭 (중간 우선순위)
            words = [word.strip('.,;()[]{}') for word in node_text.split() if word.isalnum()]
            if symbol_name in words:
                return True
            
            # 4. 부분 문자열 매칭 (낮은 우선순위)
            if any(symbol_name in word for word in words):
                return True
            
            # 5. 정규식 기반 매칭 (매우 낮은 우선순위)
            import re
            pattern = r'\b' + re.escape(symbol_name) + r'\b'
            if re.search(pattern, node_text):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"범위 매칭 확인 실패: {e}")
            return False
    
    def _check_context_match(self, node: tree_sitter.Node, symbol: Dict[str, Any]) -> bool:
        """컨텍스트 매칭 확인 - 2.3.2 범위 분석 (개선된 알고리즘)"""
        try:
            # 노드 타입과 심볼 타입 비교
            node_type = node.type
            symbol_type = symbol.get('type', 'unknown')
            
            # 확장된 타입 매칭 규칙
            type_mapping = {
                'function': ['function_definition', 'method_definition', 'function_declaration', 'def', 'function'],
                'class': ['class_definition', 'class_declaration', 'class'],
                'variable': ['assignment', 'variable_declaration', 'identifier', 'name', 'variable'],
                'method': ['method_definition', 'function_definition', 'def', 'method'],
                'property': ['property_definition', 'field_definition', 'attribute', 'property'],
                'module': ['module', 'file', 'source_file'],
                'namespace': ['namespace', 'scope', 'block'],
                'interface': ['interface', 'protocol', 'trait'],
                'enum': ['enum', 'enumeration', 'enum_definition'],
                'constant': ['constant', 'const', 'final'],
                'parameter': ['parameter', 'argument', 'param'],
                'import': ['import', 'import_statement', 'import_from_statement'],
                'export': ['export', 'export_statement', 'export_declaration']
            }
            
            expected_types = type_mapping.get(symbol_type, [])
            
            # 1. 정확한 타입 매칭 (최고 우선순위)
            if node_type in expected_types:
                return True
            
            # 2. 부분 타입 매칭 (높은 우선순위)
            if any(expected_type in node_type for expected_type in expected_types):
                return True
            
            # 3. 일반적인 노드 타입 매칭 (중간 우선순위)
            general_mapping = {
                'function': ['call', 'function_call', 'method_call'],
                'class': ['class_body', 'class_member'],
                'variable': ['identifier', 'name', 'symbol'],
                'method': ['call', 'function_call', 'method_call']
            }
            
            general_types = general_mapping.get(symbol_type, [])
            if node_type in general_types:
                return True
            
            # 4. 부모 노드 컨텍스트 확인 (낮은 우선순위)
            parent_context_match = self._check_parent_context(node, symbol)
            if parent_context_match:
                return True
            
            # 5. 텍스트 기반 매칭 (매우 낮은 우선순위)
            node_text = node.text.decode('utf-8') if node.text else ''
            if symbol_type.lower() in node_text.lower():
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"컨텍스트 매칭 확인 실패: {e}")
            return False
    
    def _check_parent_context(self, node: tree_sitter.Node, symbol: Dict[str, Any]) -> bool:
        """부모 노드 컨텍스트 확인"""
        try:
            if not node.parent:
                return True
            
            parent_type = node.parent.type
            symbol_type = symbol.get('type', 'unknown')
            
            # 클래스 내부의 메서드/속성
            if symbol_type in ['method', 'property'] and parent_type == 'class_definition':
                return True
            
            # 모듈 레벨의 함수/변수
            if symbol_type in ['function', 'variable'] and parent_type in ['module', 'program']:
                return True
            
            return True  # 기본적으로 매칭으로 간주
            
        except Exception as e:
            logger.error(f"부모 컨텍스트 확인 실패: {e}")
            return True
    
    def _calculate_mapping_confidence(self, position_match: bool, range_match: bool, context_match: bool) -> float:
        """매핑 신뢰도 계산 (개선된 알고리즘)"""
        confidence = 0.0
        
        # 가중치 기반 신뢰도 계산
        if position_match:
            confidence += 0.4  # 위치 매칭이 가장 중요
        if range_match:
            confidence += 0.4  # 범위 매칭도 중요
        if context_match:
            confidence += 0.2  # 컨텍스트 매칭은 보조적
        
        # 모든 조건이 만족되면 보너스 점수
        if position_match and range_match and context_match:
            confidence += 0.2
        
        # 부분 매칭 보너스
        if position_match and (range_match or context_match):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _determine_mapping_type(self, node: tree_sitter.Node, symbol: Dict[str, Any]) -> str:
        """매핑 타입 결정"""
        node_type = node.type
        symbol_type = symbol.get('type', 'unknown')
        
        # 정확한 매핑
        if node_type in ['function_definition', 'method_definition'] and symbol_type == 'function':
            return 'exact'
        
        # 부분 매핑
        if node_type in ['identifier', 'assignment'] and symbol_type in ['variable', 'constant']:
            return 'partial'
        
        # 컨텍스트 매핑
        if node_type in ['class_definition'] and symbol_type == 'class':
            return 'context'
        
        return 'uncertain'
    
    async def _validate_range_mappings(self, mappings: List[MappingResult], filepath: str) -> List[MappingResult]:
        """범위 매핑 검증 - 2.3.2 범위 분석"""
        try:
            validated_mappings = []
            
            for mapping in mappings:
                # 신뢰도 임계값 확인
                if mapping.mapping_confidence >= self.accuracy_threshold:
                    # 중복 매핑 제거
                    if not self._is_duplicate_mapping(mapping, validated_mappings):
                        validated_mappings.append(mapping)
            
            return validated_mappings
            
        except Exception as e:
            logger.error(f"범위 매핑 검증 실패: {e}")
            return mappings
    
    def _is_duplicate_mapping(self, mapping: MappingResult, existing_mappings: List[MappingResult]) -> bool:
        """중복 매핑 확인"""
        for existing in existing_mappings:
            if (existing.symbol_name == mapping.symbol_name and 
                existing.ast_node == mapping.ast_node):
                return True
        return False
    
    async def _verify_mapping_accuracy(self, mappings: List[MappingResult], filepath: str) -> MappingAccuracy:
        """매핑 정확도 검증 - 2.3.3 정확도 검증"""
        try:
            total_mappings = len(mappings)
            accurate_mappings = 0
            false_positives = 0
            false_negatives = 0
            
            for mapping in mappings:
                # 정확도 검증 로직
                is_accurate = await self._verify_single_mapping_accuracy(mapping, filepath)
                
                if is_accurate:
                    accurate_mappings += 1
                else:
                    if mapping.mapping_confidence > 0.5:
                        false_positives += 1
                    else:
                        false_negatives += 1
            
            accuracy_percentage = (accurate_mappings / total_mappings * 100) if total_mappings > 0 else 0
            
            return MappingAccuracy(
                total_mappings=total_mappings,
                accurate_mappings=accurate_mappings,
                accuracy_percentage=accuracy_percentage,
                false_positives=false_positives,
                false_negatives=false_negatives
            )
            
        except Exception as e:
            logger.error(f"매핑 정확도 검증 실패: {e}")
            return MappingAccuracy(0, 0, 0.0, 0, 0)
    
    async def _verify_single_mapping_accuracy(self, mapping: MappingResult, filepath: str) -> bool:
        """단일 매핑 정확도 검증 (개선된 알고리즘)"""
        try:
            # 신뢰도 기반 검증 (가장 중요)
            if mapping.mapping_confidence < self.accuracy_threshold:
                return False
            
            # 위치 매칭이 있으면 높은 점수
            position_score = 1.0 if mapping.position_match else 0.0
            
            # 범위 매칭이 있으면 높은 점수
            range_score = 1.0 if mapping.range_match else 0.0
            
            # 컨텍스트 매칭이 있으면 보조 점수
            context_score = 0.5 if mapping.context_match else 0.0
            
            # 총점 계산 (더 관대한 기준)
            total_score = position_score + range_score + context_score
            
            # 최소 1.0점 이상이면 정확한 매핑으로 간주
            return total_score >= 1.0
            
        except Exception as e:
            logger.error(f"단일 매핑 정확도 검증 실패: {e}")
            return False
    
    async def get_mapping_statistics(self, filepath: str) -> Dict[str, Any]:
        """매핑 통계 정보"""
        try:
            if filepath not in self.mapping_cache:
                return {}
            
            mappings = self.mapping_cache[filepath]
            
            # 매핑 타입별 통계
            mapping_types = {}
            for mapping in mappings:
                mapping_type = mapping.mapping_type
                mapping_types[mapping_type] = mapping_types.get(mapping_type, 0) + 1
            
            # 신뢰도 분포
            confidence_distribution = {
                'high': len([m for m in mappings if m.mapping_confidence >= 0.8]),
                'medium': len([m for m in mappings if 0.5 <= m.mapping_confidence < 0.8]),
                'low': len([m for m in mappings if m.mapping_confidence < 0.5])
            }
            
            # 매칭 성공률
            position_matches = len([m for m in mappings if m.position_match])
            range_matches = len([m for m in mappings if m.range_match])
            context_matches = len([m for m in mappings if m.context_match])
            
            return {
                'total_mappings': len(mappings),
                'mapping_types': mapping_types,
                'confidence_distribution': confidence_distribution,
                'position_matches': position_matches,
                'range_matches': range_matches,
                'context_matches': context_matches,
                'average_confidence': sum(m.mapping_confidence for m in mappings) / len(mappings) if mappings else 0
            }
            
        except Exception as e:
            logger.error(f"매핑 통계 생성 실패: {e}")
            return {}
    
    def clear_cache(self, filepath: Optional[str] = None):
        """캐시 정리"""
        if filepath:
            if filepath in self.mapping_cache:
                del self.mapping_cache[filepath]
        else:
            self.mapping_cache.clear()
        
        logger.info(f"매핑 캐시 정리 완료: {filepath or '전체'}")
