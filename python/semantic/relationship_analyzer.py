"""
의미적 관계 분석기
요청하신 2.4 의미적 관계 설정 기능 구현
내보내기/가져오기, 상속 관계, 의존성 관계 설정 기능 제공
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from pathlib import Path
import re

logger = logging.getLogger(__name__)

@dataclass
class Relationship:
    """의미적 관계"""
    source: str
    target: str
    relationship_type: str
    strength: float
    context: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class DependencyGraph:
    """의존성 그래프"""
    nodes: List[str]
    edges: List[Tuple[str, str, str]]  # (source, target, relationship_type)
    relationships: List[Relationship]

class RelationshipAnalyzer:
    """의미적 관계 분석기 - 요청하신 2.4 의미적 관계 설정 기능"""
    
    def __init__(self):
        self.relationship_cache: Dict[str, List[Relationship]] = {}
        self.dependency_graphs: Dict[str, DependencyGraph] = {}
        
        logger.info("의미적 관계 분석기 초기화 완료")
    
    async def analyze_semantic_relationships(self, symbols: List[Dict[str, Any]], filepath: str) -> List[Relationship]:
        """의미적 관계 분석 - 2.4 의미적 관계 설정"""
        try:
            relationships = []
            
            # 2.4.1 내보내기/가져오기 관계 설정
            import_export_relationships = await self._analyze_import_export_relationships(symbols, filepath)
            relationships.extend(import_export_relationships)
            
            # 2.4.2 상속 관계 설정
            inheritance_relationships = await self._analyze_inheritance_relationships(symbols, filepath)
            relationships.extend(inheritance_relationships)
            
            # 2.4.3 의존성 관계 설정
            dependency_relationships = await self._analyze_dependency_relationships(symbols, filepath)
            relationships.extend(dependency_relationships)
            
            # 관계 강도 계산
            for relationship in relationships:
                relationship.strength = self._calculate_relationship_strength(relationship)
            
            # 캐시에 저장
            self.relationship_cache[filepath] = relationships
            
            # 의존성 그래프 생성
            dependency_graph = self._build_dependency_graph(relationships)
            self.dependency_graphs[filepath] = dependency_graph
            
            logger.info(f"의미적 관계 분석 완료: {len(relationships)}개 관계 발견")
            
            return relationships
            
        except Exception as e:
            logger.error(f"의미적 관계 분석 실패: {e}")
            return []
    
    async def _analyze_import_export_relationships(self, symbols: List[Dict[str, Any]], filepath: str) -> List[Relationship]:
        """내보내기/가져오기 관계 분석 - 2.4.1 내보내기/가져오기 관계 설정"""
        try:
            relationships = []
            
            # 파일 내용 읽기
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # 임포트 문 분석
            imports = self._extract_imports(content)
            
            # 익스포트 문 분석
            exports = self._extract_exports(content)
            
            # 임포트 관계 직접 분석 (심볼 매칭 없이)
            for import_info in imports:
                try:
                    module_name = str(import_info.get('module', 'unknown_module'))
                    relationship = Relationship(
                        source=module_name,
                        target=f"imported_from_{module_name}",
                        relationship_type='import',
                        strength=0.0,  # 나중에 계산
                        context={
                            'import_type': str(import_info.get('type', 'unknown')),
                            'import_line': import_info.get('line', 0)
                        },
                        metadata={
                            'file': str(filepath),
                            'import_statement': str(import_info.get('statement', ''))
                        }
                    )
                    relationships.append(relationship)
                except Exception as e:
                    logger.warning(f"임포트 관계 생성 실패: {e}")
                    continue
            
            # 심볼과 임포트/익스포트 매칭
            for symbol in symbols:
                try:
                    symbol_name = symbol.get('name', 'unknown_symbol')
                    
                    # 임포트 관계 분석
                    for import_info in imports:
                        if self._is_symbol_imported(symbol_name, import_info):
                            try:
                                relationship = Relationship(
                                    source=str(import_info.get('module', 'unknown_module')),
                                    target=symbol_name,
                                    relationship_type='import',
                                    strength=0.0,  # 나중에 계산
                                    context={
                                        'import_type': str(import_info.get('type', 'unknown')),
                                        'import_line': import_info.get('line', 0),
                                        'symbol_range': symbol.get('range', {})
                                    },
                                    metadata={
                                        'file': str(filepath),
                                        'import_statement': str(import_info.get('statement', ''))
                                    }
                                )
                                relationships.append(relationship)
                            except Exception as e:
                                logger.warning(f"심볼-임포트 관계 생성 실패: {e}")
                                continue
                except Exception as e:
                    logger.warning(f"심볼-임포트 관계 생성 실패: {e}")
                
                # 익스포트 관계 분석
                for export_info in exports:
                    if self._is_symbol_exported(symbol_name, export_info):
                        try:
                            relationship = Relationship(
                                source=symbol_name,
                                target=str(export_info.get('module', 'unknown_module')),
                                relationship_type='export',
                                strength=0.0,  # 나중에 계산
                                context={
                                    'export_type': str(export_info.get('type', 'unknown')),
                                    'export_line': export_info.get('line', 0),
                                    'symbol_range': symbol.get('range', {})
                                },
                                metadata={
                                    'file': str(filepath),
                                    'export_statement': str(export_info.get('statement', ''))
                                }
                            )
                            relationships.append(relationship)
                        except Exception as e:
                            logger.warning(f"심볼-익스포트 관계 생성 실패: {e}")
                            continue
            
            return relationships
            
        except Exception as e:
            logger.error(f"임포트/익스포트 관계 분석 실패: {e}")
            return []
    
    def _extract_imports(self, content: str) -> List[Dict[str, Any]]:
        """임포트 문 추출"""
        imports = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Python 임포트
            if line.startswith('import '):
                match = re.match(r'import\s+(\w+)', line)
                if match:
                    imports.append({
                        'type': 'direct_import',
                        'module': match.group(1),
                        'line': i,
                        'statement': line
                    })
            
            elif line.startswith('from '):
                match = re.match(r'from\s+(\w+)\s+import\s+(.+)', line)
                if match:
                    imports.append({
                        'type': 'from_import',
                        'module': match.group(1),
                        'imports': match.group(2).split(','),
                        'line': i,
                        'statement': line
                    })
            
            # JavaScript/TypeScript 임포트
            elif line.startswith('import '):
                match = re.match(r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]', line)
                if match:
                    imports.append({
                        'type': 'es6_import',
                        'module': match.group(1),
                        'line': i,
                        'statement': line
                    })
            
            # Java 임포트
            elif line.startswith('import '):
                match = re.match(r'import\s+([\w.]+)', line)
                if match:
                    imports.append({
                        'type': 'java_import',
                        'module': match.group(1),
                        'line': i,
                        'statement': line
                    })
        
        return imports
    
    def _extract_exports(self, content: str) -> List[Dict[str, Any]]:
        """익스포트 문 추출"""
        exports = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Python 익스포트
            if line.startswith('def ') or line.startswith('class '):
                # 함수나 클래스 정의
                match = re.match(r'(def|class)\s+(\w+)', line)
                if match:
                    exports.append({
                        'type': 'definition',
                        'symbol': match.group(2),
                        'line': i,
                        'statement': line
                    })
            
            # JavaScript/TypeScript 익스포트
            elif line.startswith('export '):
                match = re.match(r'export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)', line)
                if match:
                    exports.append({
                        'type': 'es6_export',
                        'symbol': match.group(1),
                        'line': i,
                        'statement': line
                    })
            
            # Java 익스포트 (public 클래스/메서드)
            elif 'public' in line and ('class' in line or 'interface' in line):
                match = re.match(r'public\s+(?:class|interface)\s+(\w+)', line)
                if match:
                    exports.append({
                        'type': 'java_public',
                        'symbol': match.group(1),
                        'line': i,
                        'statement': line
                    })
        
        return exports
    
    def _is_symbol_imported(self, symbol_name: str, import_info: Dict[str, Any]) -> bool:
        """심볼이 임포트되었는지 확인"""
        try:
            import_type = import_info.get('type', '')
            if import_type == 'from_import':
                return symbol_name in import_info.get('imports', [])
            elif import_type in ['direct_import', 'es6_import', 'java_import']:
                return symbol_name == str(import_info.get('module', ''))
            return False
        except Exception as e:
            logger.warning(f"심볼 임포트 확인 실패: {e}")
            return False
    
    def _is_symbol_exported(self, symbol_name: str, export_info: Dict[str, Any]) -> bool:
        """심볼이 익스포트되었는지 확인"""
        try:
            return symbol_name == str(export_info.get('symbol', ''))
        except Exception as e:
            logger.warning(f"심볼 익스포트 확인 실패: {e}")
            return False
    
    async def _analyze_inheritance_relationships(self, symbols: List[Dict[str, Any]], filepath: str) -> List[Relationship]:
        """상속 관계 분석 - 2.4.2 상속 관계 설정"""
        try:
            relationships = []
            
            # 파일 내용 읽기
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # 클래스 정의 찾기
            class_definitions = []
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Python 클래스
                if line.startswith('class '):
                    match = re.match(r'class\s+(\w+)(?:\s*\(([^)]+)\))?', line)
                    if match:
                        class_name = match.group(1)
                        parent_classes = match.group(2).split(',') if match.group(2) else []
                        class_definitions.append({
                            'name': class_name,
                            'parents': [p.strip() for p in parent_classes],
                            'line': i
                        })
                
                # JavaScript/TypeScript 클래스
                elif 'class ' in line:
                    match = re.match(r'class\s+(\w+)(?:\s+extends\s+(\w+))?', line)
                    if match:
                        class_name = match.group(1)
                        parent_class = match.group(2) if match.group(2) else None
                        class_definitions.append({
                            'name': class_name,
                            'parents': [parent_class] if parent_class else [],
                            'line': i
                        })
                
                # Java 클래스
                elif 'class ' in line and 'extends' in line:
                    match = re.match(r'class\s+(\w+)\s+extends\s+(\w+)', line)
                    if match:
                        class_name = match.group(1)
                        parent_class = match.group(2)
                        class_definitions.append({
                            'name': class_name,
                            'parents': [parent_class],
                            'line': i
                        })
            
            # 상속 관계 생성
            for class_def in class_definitions:
                try:
                    for parent in class_def['parents']:
                        if parent and parent.strip():  # None이 아니고 빈 문자열이 아닌 경우만
                            parent = parent.strip()
                            relationship = Relationship(
                                source=class_def['name'],
                                target=parent,
                                relationship_type='inheritance',
                                strength=0.0,  # 나중에 계산
                                context={
                                    'inheritance_type': 'class_inheritance',
                                    'class_line': class_def['line']
                                },
                                metadata={
                                    'file': filepath,
                                    'class_definition': class_def
                                }
                            )
                            relationships.append(relationship)
                            logger.info(f"상속 관계 발견: {class_def['name']} -> {parent}")
                except Exception as e:
                    logger.warning(f"상속 관계 생성 실패: {e}")
            
            # 인터페이스 구현 관계도 추가
            interface_implementations = self._extract_interface_implementations(content)
            for impl in interface_implementations:
                try:
                    relationship = Relationship(
                        source=impl['class'],
                        target=impl['interface'],
                        relationship_type='interface_implementation',
                        strength=0.0,  # 나중에 계산
                        context={
                            'implementation_type': 'interface_implementation',
                            'implementation_line': impl['line']
                        },
                        metadata={
                            'file': filepath,
                            'implementation_info': impl
                        }
                    )
                    relationships.append(relationship)
                    logger.info(f"인터페이스 구현 관계 발견: {impl['class']} implements {impl['interface']}")
                except Exception as e:
                    logger.warning(f"인터페이스 구현 관계 생성 실패: {e}")
            
            return relationships
            
        except Exception as e:
            logger.error(f"상속 관계 분석 실패: {e}")
            return []
    
    async def _analyze_dependency_relationships(self, symbols: List[Dict[str, Any]], filepath: str) -> List[Relationship]:
        """의존성 관계 분석 - 2.4.3 의존성 관계 설정"""
        try:
            relationships = []
            
            # 파일 내용 읽기
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 함수 호출 관계 분석
            function_calls = self._extract_function_calls(content)
            
            # 변수 참조 관계 분석
            variable_references = self._extract_variable_references(content)
            
            # 심볼 간 의존성 관계 생성
            for symbol in symbols:
                symbol_name = symbol['name']
                symbol_type = symbol.get('type', 'unknown')
                
                # 함수 호출 의존성
                for call in function_calls:
                    if call['function'] == symbol_name:
                        for caller in call['callers']:
                            relationship = Relationship(
                                source=caller,
                                target=symbol_name,
                                relationship_type='function_call',
                                strength=0.0,  # 나중에 계산
                                context={
                                    'call_type': 'function_invocation',
                                    'call_line': call['line']
                                },
                                metadata={
                                    'file': filepath,
                                    'call_context': call['context']
                                }
                            )
                            relationships.append(relationship)
                
                # 변수 참조 의존성
                for ref in variable_references:
                    if ref['variable'] == symbol_name:
                        for user in ref['users']:
                            relationship = Relationship(
                                source=user,
                                target=symbol_name,
                                relationship_type='variable_reference',
                                strength=0.0,  # 나중에 계산
                                context={
                                    'reference_type': 'variable_usage',
                                    'reference_line': ref['line']
                                },
                                metadata={
                                    'file': filepath,
                                    'reference_context': ref['context']
                                }
                            )
                            relationships.append(relationship)
            
            return relationships
            
        except Exception as e:
            logger.error(f"의존성 관계 분석 실패: {e}")
            return []
    
    def _extract_function_calls(self, content: str) -> List[Dict[str, Any]]:
        """함수 호출 추출 - 실제 호출자 식별"""
        function_calls = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # 함수 호출 패턴 찾기 (더 정확한 패턴)
            matches = re.findall(r'(?:\w+\.)?(\w+)\s*\(', line)
            for match in matches:
                # 호출자 식별 시도
                caller = self._identify_caller(line, i, lines)
                function_calls.append({
                    'function': match,
                    'callers': [caller] if caller else ['module'],
                    'line': i,
                    'context': line.strip()
                })
        
        return function_calls
    
    def _identify_caller(self, line: str, line_num: int, all_lines: List[str]) -> str:
        """호출자 식별 - 클래스나 함수 내부에서 호출되는지 확인"""
        # 현재 라인에서 클래스/함수 정의 찾기
        for i in range(line_num, -1, -1):
            prev_line = all_lines[i].strip()
            
            # 클래스 정의
            if prev_line.startswith('class '):
                match = re.match(r'class\s+(\w+)', prev_line)
                if match:
                    return match.group(1)
            
            # 함수 정의
            elif prev_line.startswith('def '):
                match = re.match(r'def\s+(\w+)', prev_line)
                if match:
                    return match.group(1)
            
            # self. 호출인 경우
            if 'self.' in line:
                return 'self'
        
        return 'module'  # 모듈 레벨 호출
    
    def _extract_variable_references(self, content: str) -> List[Dict[str, Any]]:
        """변수 참조 추출 - 실제 사용자 식별"""
        variable_references = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # 변수 참조 패턴 찾기 (더 정확한 패턴)
            matches = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', line)
            for match in matches:
                if not match.isdigit() and match not in ['def', 'class', 'if', 'for', 'while', 'return', 'import', 'from']:
                    # 사용자 식별 시도
                    user = self._identify_variable_user(line, i, lines, match)
                    variable_references.append({
                        'variable': match,
                        'users': [user] if user else ['module'],
                        'line': i,
                        'context': line.strip()
                    })
        
        return variable_references
    
    def _identify_variable_user(self, line: str, line_num: int, all_lines: List[str], variable: str) -> str:
        """변수 사용자 식별 - 어떤 컨텍스트에서 사용되는지 확인"""
        # import 문에서 사용되는 경우
        if 'import' in line:
            return 'import_statement'
        
        # 함수 호출에서 사용되는 경우
        if '(' in line and variable in line:
            return 'function_call'
        
        # 변수 할당에서 사용되는 경우
        if '=' in line and variable in line:
            return 'assignment'
        
        # 클래스나 함수 내부에서 사용되는 경우
        for i in range(line_num, -1, -1):
            prev_line = all_lines[i].strip()
            
            if prev_line.startswith('class '):
                match = re.match(r'class\s+(\w+)', prev_line)
                if match:
                    return f'class_{match.group(1)}'
            
            elif prev_line.startswith('def '):
                match = re.match(r'def\s+(\w+)', prev_line)
                if match:
                    return f'function_{match.group(1)}'
        
        return 'module'  # 모듈 레벨 사용
    
    def _extract_interface_implementations(self, content: str) -> List[Dict[str, Any]]:
        """인터페이스 구현 관계 추출"""
        implementations = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Java 인터페이스 구현
            if 'implements' in line:
                match = re.match(r'class\s+(\w+).*implements\s+([^{]+)', line)
                if match:
                    class_name = match.group(1)
                    interfaces = [iface.strip() for iface in match.group(2).split(',')]
                    for interface in interfaces:
                        implementations.append({
                            'class': class_name,
                            'interface': interface,
                            'line': i,
                            'language': 'java'
                        })
            
            # TypeScript 인터페이스 구현
            elif 'class ' in line and 'implements' in line:
                match = re.match(r'class\s+(\w+).*implements\s+([^{]+)', line)
                if match:
                    class_name = match.group(1)
                    interfaces = [iface.strip() for iface in match.group(2).split(',')]
                    for interface in interfaces:
                        implementations.append({
                            'class': class_name,
                            'interface': interface,
                            'line': i,
                            'language': 'typescript'
                        })
            
            # Python ABC (Abstract Base Class) 상속
            elif 'ABC' in line and 'class ' in line:
                match = re.match(r'class\s+(\w+)\s*\([^)]*ABC[^)]*\)', line)
                if match:
                    class_name = match.group(1)
                    implementations.append({
                        'class': class_name,
                        'interface': 'ABC',
                        'line': i,
                        'language': 'python'
                    })
        
        return implementations
    
    def _calculate_relationship_strength(self, relationship: Relationship) -> float:
        """관계 강도 계산"""
        strength = 0.5  # 기본 강도
        
        # 관계 타입별 가중치
        type_weights = {
            'import': 0.8,
            'export': 0.9,
            'inheritance': 1.0,
            'function_call': 0.7,
            'variable_reference': 0.6
        }
        
        relationship_type = relationship.relationship_type
        if relationship_type in type_weights:
            strength *= type_weights[relationship_type]
        
        # 컨텍스트 정보에 따른 조정
        context = relationship.context
        if 'call_line' in context or 'reference_line' in context:
            strength += 0.1
        
        return min(strength, 1.0)
    
    def _build_dependency_graph(self, relationships: List[Relationship]) -> DependencyGraph:
        """의존성 그래프 생성"""
        nodes = set()
        edges = []
        
        for relationship in relationships:
            nodes.add(relationship.source)
            nodes.add(relationship.target)
            edges.append((relationship.source, relationship.target, relationship.relationship_type))
        
        return DependencyGraph(
            nodes=list(nodes),
            edges=edges,
            relationships=relationships
        )
    
    async def get_relationship_statistics(self, filepath: str) -> Dict[str, Any]:
        """관계 통계 정보"""
        try:
            if filepath not in self.relationship_cache:
                return {}
            
            relationships = self.relationship_cache[filepath]
            
            # 관계 타입별 통계
            relationship_types = {}
            for rel in relationships:
                rel_type = rel.relationship_type
                relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
            
            # 강도 분포
            strength_distribution = {
                'strong': len([r for r in relationships if r.strength >= 0.8]),
                'medium': len([r for r in relationships if 0.5 <= r.strength < 0.8]),
                'weak': len([r for r in relationships if r.strength < 0.5])
            }
            
            # 평균 강도
            average_strength = sum(r.strength for r in relationships) / len(relationships) if relationships else 0
            
            return {
                'total_relationships': len(relationships),
                'relationship_types': relationship_types,
                'strength_distribution': strength_distribution,
                'average_strength': average_strength,
                'dependency_graph': self.dependency_graphs.get(filepath, None)
            }
            
        except Exception as e:
            logger.error(f"관계 통계 생성 실패: {e}")
            return {}
    
    def clear_cache(self, filepath: Optional[str] = None):
        """캐시 정리"""
        if filepath:
            if filepath in self.relationship_cache:
                del self.relationship_cache[filepath]
            if filepath in self.dependency_graphs:
                del self.dependency_graphs[filepath]
        else:
            self.relationship_cache.clear()
            self.dependency_graphs.clear()
        
        logger.info(f"관계 캐시 정리 완료: {filepath or '전체'}")
