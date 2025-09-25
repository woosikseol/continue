"""
의미적 분석기
요청하신 2.2 의미적 타입 결정 기능 구현
LSP 심볼 타입, 컨텍스트 분석, 언어별 특화 기능 제공
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SemanticType:
    """의미적 타입 정보"""
    name: str
    type: str
    context: Dict[str, Any]
    language_specific: Dict[str, Any]
    confidence: float

@dataclass
class ContextInfo:
    """컨텍스트 정보"""
    surrounding_code: str
    imports: List[str]
    exports: List[str]
    dependencies: List[str]
    scope_level: int

class SemanticAnalyzer:
    """의미적 분석기 - 요청하신 2.2 의미적 타입 결정 기능"""
    
    def __init__(self):
        self.language_patterns = {
            'python': self._get_python_patterns(),
            'javascript': self._get_javascript_patterns(),
            'typescript': self._get_typescript_patterns(),
            'java': self._get_java_patterns(),
            'cpp': self._get_cpp_patterns()
        }
        
        logger.info("의미적 분석기 초기화 완료")
    
    def _get_python_patterns(self) -> Dict[str, Any]:
        """Python 언어별 패턴"""
        return {
            'class_patterns': [
                r'class\s+\w+',
                r'class\s+\w+\s*\([^)]*\):',
                r'class\s+\w+\s*\([^)]*\):\s*"""',
            ],
            'function_patterns': [
                r'def\s+\w+\s*\(',
                r'async\s+def\s+\w+\s*\(',
                r'@\w+\s*\n\s*def\s+\w+\s*\(',
            ],
            'variable_patterns': [
                r'\w+\s*=\s*[^=]',
                r'[A-Z_][A-Z0-9_]*\s*=\s*',
                r'self\.\w+\s*=',
            ],
            'import_patterns': [
                r'import\s+\w+',
                r'from\s+\w+\s+import',
                r'import\s+\w+\s+as\s+\w+',
            ],
            'visibility_indicators': {
                'private': ['_', '__'],
                'protected': ['_'],
                'public': []
            }
        }
    
    def _get_javascript_patterns(self) -> Dict[str, Any]:
        """JavaScript 언어별 패턴"""
        return {
            'class_patterns': [
                r'class\s+\w+',
                r'class\s+\w+\s+extends\s+\w+',
                r'export\s+class\s+\w+',
            ],
            'function_patterns': [
                r'function\s+\w+\s*\(',
                r'const\s+\w+\s*=\s*\(',
                r'async\s+function\s+\w+\s*\(',
                r'export\s+function\s+\w+',
            ],
            'variable_patterns': [
                r'const\s+\w+\s*=',
                r'let\s+\w+\s*=',
                r'var\s+\w+\s*=',
                r'this\.\w+\s*=',
            ],
            'import_patterns': [
                r'import\s+.*\s+from\s+',
                r'require\s*\(',
                r'import\s*\{[^}]*\}\s+from',
            ],
            'visibility_indicators': {
                'private': ['#', '_'],
                'protected': ['_'],
                'public': []
            }
        }
    
    def _get_typescript_patterns(self) -> Dict[str, Any]:
        """TypeScript 언어별 패턴"""
        return {
            'class_patterns': [
                r'class\s+\w+',
                r'class\s+\w+\s+implements\s+\w+',
                r'export\s+class\s+\w+',
                r'interface\s+\w+',
            ],
            'function_patterns': [
                r'function\s+\w+\s*\(',
                r'const\s+\w+\s*:\s*\w+\s*=\s*\(',
                r'async\s+function\s+\w+\s*\(',
                r'export\s+function\s+\w+',
            ],
            'variable_patterns': [
                r'const\s+\w+\s*:\s*\w+\s*=',
                r'let\s+\w+\s*:\s*\w+\s*=',
                r'private\s+\w+\s*:',
                r'protected\s+\w+\s*:',
                r'public\s+\w+\s*:',
            ],
            'import_patterns': [
                r'import\s+.*\s+from\s+',
                r'import\s*\{[^}]*\}\s+from',
                r'import\s+\w+\s+from',
            ],
            'visibility_indicators': {
                'private': ['private', '#', '_'],
                'protected': ['protected', '_'],
                'public': ['public']
            }
        }
    
    def _get_java_patterns(self) -> Dict[str, Any]:
        """Java 언어별 패턴"""
        return {
            'class_patterns': [
                r'public\s+class\s+\w+',
                r'private\s+class\s+\w+',
                r'protected\s+class\s+\w+',
                r'class\s+\w+\s+extends\s+\w+',
                r'class\s+\w+\s+implements\s+\w+',
            ],
            'function_patterns': [
                r'public\s+\w+\s+\w+\s*\(',
                r'private\s+\w+\s+\w+\s*\(',
                r'protected\s+\w+\s+\w+\s*\(',
                r'static\s+\w+\s+\w+\s*\(',
            ],
            'variable_patterns': [
                r'private\s+\w+\s+\w+\s*;',
                r'protected\s+\w+\s+\w+\s*;',
                r'public\s+\w+\s+\w+\s*;',
                r'static\s+final\s+\w+\s+\w+\s*=',
            ],
            'import_patterns': [
                r'import\s+\w+\.\w+',
                r'import\s+\w+\.\w+\.\w+',
            ],
            'visibility_indicators': {
                'private': ['private'],
                'protected': ['protected'],
                'public': ['public'],
                'package': []
            }
        }
    
    def _get_cpp_patterns(self) -> Dict[str, Any]:
        """C++ 언어별 패턴"""
        return {
            'class_patterns': [
                r'class\s+\w+',
                r'struct\s+\w+',
                r'namespace\s+\w+',
            ],
            'function_patterns': [
                r'\w+\s+\w+\s*\(',
                r'void\s+\w+\s*\(',
                r'int\s+\w+\s*\(',
                r'std::\w+',
            ],
            'variable_patterns': [
                r'int\s+\w+\s*;',
                r'std::\w+\s+\w+\s*;',
                r'const\s+\w+\s+\w+\s*=',
            ],
            'import_patterns': [
                r'#include\s+<[^>]+>',
                r'#include\s+"[^"]+"',
                r'using\s+namespace\s+\w+',
            ],
            'visibility_indicators': {
                'private': ['private:'],
                'protected': ['protected:'],
                'public': ['public:']
            }
        }
    
    async def determine_semantic_type(self, symbol_info: Dict[str, Any], filepath: str) -> SemanticType:
        """의미적 타입 결정 - 2.2.1 LSP 심볼 타입 활용"""
        try:
            # 2.2.1 LSP 심볼 타입 활용
            lsp_type = self._get_lsp_semantic_type(symbol_info['kind'])
            
            # 2.2.2 컨텍스트 분석
            context = await self._analyze_context(symbol_info, filepath)
            
            # 2.2.3 언어별 특화
            language = self._get_language_from_file(filepath)
            language_specific = self._get_language_specific_info(symbol_info, context, language)
            
            # 신뢰도 계산
            confidence = self._calculate_confidence(lsp_type, context, language_specific)
            
            return SemanticType(
                name=symbol_info['name'],
                type=lsp_type,
                context=context,
                language_specific=language_specific,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"의미적 타입 결정 실패: {e}")
            return SemanticType(
                name=symbol_info.get('name', 'unknown'),
                type='unknown',
                context={},
                language_specific={},
                confidence=0.0
            )
    
    def _get_lsp_semantic_type(self, kind: int) -> str:
        """LSP 심볼 타입을 의미적 타입으로 변환"""
        type_mapping = {
            1: 'file',           # File
            2: 'module',         # Module
            3: 'namespace',      # Namespace
            4: 'package',        # Package
            5: 'class',          # Class
            6: 'method',         # Method
            7: 'property',       # Property
            8: 'field',          # Field
            9: 'constructor',    # Constructor
            10: 'enum',          # Enum
            11: 'interface',     # Interface
            12: 'function',      # Function
            13: 'variable',     # Variable
            14: 'constant',      # Constant
            15: 'string',        # String
            16: 'number',        # Number
            17: 'boolean',       # Boolean
            18: 'array',         # Array
            19: 'object',        # Object
            20: 'key',           # Key
            21: 'null',         # Null
            22: 'enum_member',   # EnumMember
            23: 'struct',        # Struct
            24: 'event',        # Event
            25: 'operator',      # Operator
            26: 'type_parameter' # TypeParameter
        }
        
        return type_mapping.get(kind, 'unknown')
    
    async def _analyze_context(self, symbol_info: Dict[str, Any], filepath: str) -> Dict[str, Any]:
        """컨텍스트 분석 - 2.2.2 컨텍스트 분석"""
        try:
            # 파일 내용 읽기
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            start_line = symbol_info['range']['start']['line']
            end_line = symbol_info['range']['end']['line']
            
            # 주변 코드 분석
            surrounding_lines = []
            for i in range(max(0, start_line - 5), min(len(lines), end_line + 6)):
                surrounding_lines.append(lines[i])
            
            surrounding_code = '\n'.join(surrounding_lines)
            
            # 임포트 분석
            imports = self._extract_imports(content)
            
            # 익스포트 분석
            exports = self._extract_exports(content, symbol_info)
            
            # 의존성 분석
            dependencies = self._extract_dependencies(surrounding_code)
            
            # 스코프 레벨 계산
            scope_level = self._calculate_scope_level(surrounding_code)
            
            return {
                'surrounding_code': surrounding_code,
                'imports': imports,
                'exports': exports,
                'dependencies': dependencies,
                'scope_level': scope_level
            }
            
        except Exception as e:
            logger.error(f"컨텍스트 분석 실패: {e}")
            return {
                'surrounding_code': '',
                'imports': [],
                'exports': [],
                'dependencies': [],
                'scope_level': 0
            }
    
    def _extract_imports(self, content: str) -> List[str]:
        """임포트 추출"""
        imports = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        
        return imports
    
    def _extract_exports(self, content: str, symbol_info: Dict[str, Any]) -> List[str]:
        """익스포트 추출"""
        exports = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('export ') or line.startswith('def ') or line.startswith('class '):
                if symbol_info['name'] in line:
                    exports.append(line)
        
        return exports
    
    def _extract_dependencies(self, surrounding_code: str) -> List[str]:
        """의존성 추출"""
        dependencies = []
        lines = surrounding_code.split('\n')
        
        for line in lines:
            line = line.strip()
            # 함수 호출, 변수 참조 등 의존성 패턴 찾기
            if '(' in line and ')' in line:
                # 함수 호출 패턴
                import re
                matches = re.findall(r'\b\w+\s*\(', line)
                dependencies.extend(matches)
        
        return list(set(dependencies))
    
    def _calculate_scope_level(self, surrounding_code: str) -> int:
        """스코프 레벨 계산"""
        level = 0
        lines = surrounding_code.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('class ') or line.startswith('def '):
                level += 1
            elif line.startswith('if ') or line.startswith('for ') or line.startswith('while '):
                level += 1
            elif line.startswith('try:'):
                level += 1
        
        return level
    
    def _get_language_specific_info(self, symbol_info: Dict[str, Any], context: Dict[str, Any], language: str) -> Dict[str, Any]:
        """언어별 특화 정보 - 2.2.3 언어별 특화"""
        if language not in self.language_patterns:
            return {}
        
        patterns = self.language_patterns[language]
        surrounding_code = context.get('surrounding_code', '')
        
        # 패턴 매칭
        matched_patterns = []
        for pattern_type, pattern_list in patterns.items():
            if pattern_type != 'visibility_indicators':
                for pattern in pattern_list:
                    import re
                    if re.search(pattern, surrounding_code):
                        matched_patterns.append({
                            'type': pattern_type,
                            'pattern': pattern
                        })
        
        # 가시성 분석
        visibility = self._analyze_language_visibility(symbol_info, surrounding_code, language)
        
        return {
            'matched_patterns': matched_patterns,
            'visibility': visibility,
            'language': language,
            'patterns_available': list(patterns.keys())
        }
    
    def _analyze_language_visibility(self, symbol_info: Dict[str, Any], surrounding_code: str, language: str) -> str:
        """언어별 가시성 분석"""
        if language not in self.language_patterns:
            return 'unknown'
        
        patterns = self.language_patterns[language]
        visibility_indicators = patterns.get('visibility_indicators', {})
        
        for visibility, indicators in visibility_indicators.items():
            for indicator in indicators:
                if indicator in surrounding_code:
                    return visibility
        
        return 'public'  # 기본값
    
    def _calculate_confidence(self, lsp_type: str, context: Dict[str, Any], language_specific: Dict[str, Any]) -> float:
        """신뢰도 계산"""
        confidence = 0.5  # 기본 신뢰도
        
        # LSP 타입이 명확한 경우
        if lsp_type != 'unknown':
            confidence += 0.3
        
        # 컨텍스트 정보가 풍부한 경우
        if context.get('surrounding_code'):
            confidence += 0.1
        
        # 언어별 패턴이 매칭된 경우
        if language_specific.get('matched_patterns'):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _get_language_from_file(self, filepath: str) -> str:
        """파일 확장자로부터 언어 결정"""
        ext = Path(filepath).suffix.lstrip('.').lower()
        language_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'tsx': 'typescript',
            'jsx': 'javascript',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'cpp',
            'h': 'cpp',
            'hpp': 'cpp'
        }
        return language_map.get(ext, 'python')
