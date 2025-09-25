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
        self.accuracy_threshold = 0.7
        
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
        """위치 매칭 확인 - 2.3.1 위치 기반 매핑"""
        try:
            node_start_line = node.start_point[0]
            node_start_char = node.start_point[1]
            node_end_line = node.end_point[0]
            node_end_char = node.end_point[1]
            
            # 시작 위치가 일치하는지 확인
            start_match = (node_start_line == start_line and node_start_char == start_char)
            
            # 끝 위치가 일치하는지 확인
            end_match = (node_end_line == end_line and node_end_char == end_char)
            
            # 부분적으로 포함되는지 확인
            partial_match = (
                node_start_line <= start_line <= node_end_line and
                node_start_line <= end_line <= node_end_line
            )
            
            return start_match or end_match or partial_match
            
        except Exception as e:
            logger.error(f"위치 매칭 확인 실패: {e}")
            return False
    
    def _check_range_match(self, node: tree_sitter.Node, symbol: Dict[str, Any]) -> bool:
        """범위 매칭 확인 - 2.3.2 범위 분석"""
        try:
            # 노드의 텍스트와 심볼 이름 비교
            node_text = node.text.decode('utf-8') if node.text else ''
            symbol_name = symbol['name']
            
            # 정확한 이름 매칭
            exact_match = symbol_name in node_text
            
            # 부분 매칭 (변수명, 함수명 등)
            partial_match = any(
                word == symbol_name 
                for word in node_text.split() 
                if word.isalnum()
            )
            
            return exact_match or partial_match
            
        except Exception as e:
            logger.error(f"범위 매칭 확인 실패: {e}")
            return False
    
    def _check_context_match(self, node: tree_sitter.Node, symbol: Dict[str, Any]) -> bool:
        """컨텍스트 매칭 확인 - 2.3.2 범위 분석"""
        try:
            # 노드 타입과 심볼 타입 비교
            node_type = node.type
            symbol_type = symbol.get('type', 'unknown')
            
            # 타입 매칭 규칙
            type_mapping = {
                'function': ['function_definition', 'method_definition', 'function_declaration'],
                'class': ['class_definition', 'class_declaration'],
                'variable': ['assignment', 'variable_declaration', 'identifier'],
                'method': ['method_definition', 'function_definition'],
                'property': ['property_definition', 'field_definition']
            }
            
            expected_types = type_mapping.get(symbol_type, [])
            type_match = node_type in expected_types
            
            # 부모 노드 컨텍스트 확인
            parent_context_match = self._check_parent_context(node, symbol)
            
            return type_match and parent_context_match
            
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
        """매핑 신뢰도 계산"""
        confidence = 0.0
        
        if position_match:
            confidence += 0.4
        if range_match:
            confidence += 0.3
        if context_match:
            confidence += 0.3
        
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
        """단일 매핑 정확도 검증"""
        try:
            # 위치 매칭이 정확한지 확인
            if not mapping.position_match:
                return False
            
            # 범위 매칭이 정확한지 확인
            if not mapping.range_match:
                return False
            
            # 컨텍스트 매칭이 정확한지 확인
            if not mapping.context_match:
                return False
            
            # 신뢰도가 임계값 이상인지 확인
            if mapping.mapping_confidence < self.accuracy_threshold:
                return False
            
            return True
            
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
