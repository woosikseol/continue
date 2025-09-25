"""
LSP 서비스
원본 TypeScript LSP 관련 코드의 Python 포팅
Language Server Protocol을 사용하여 정확한 의미론적 분석 제공
"""

import asyncio
import logging
import subprocess
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class LSPPosition:
    """LSP 위치 정보"""
    line: int
    character: int

@dataclass
class LSPRange:
    """LSP 범위 정보"""
    start: LSPPosition
    end: LSPPosition

@dataclass
class LSPLocation:
    """LSP 위치 정보"""
    uri: str
    range: LSPRange

@dataclass
class LSPSignatureHelp:
    """LSP 시그니처 도움말"""
    signatures: List[Dict[str, Any]]
    active_signature: Optional[int] = None
    active_parameter: Optional[int] = None

@dataclass
class DocumentSymbol:
    """문서 심볼"""
    name: str
    range: LSPRange
    selection_range: LSPRange
    kind: int

class LSPService:
    """LSP 서비스 클래스 - 원본 TypeScript LSP 코드의 Python 포팅"""
    
    def __init__(self):
        self.clients: Dict[str, Any] = {}
        self._initialized = False
        self._request_id = 0
    
    async def initialize(self):
        """LSP 서비스 초기화"""
        try:
            # 지원하는 언어 서버들 초기화
            await self._initialize_language_servers()
            self._initialized = True
            logger.info("LSP 서비스 초기화 완료")
            
        except Exception as e:
            logger.error(f"LSP 초기화 실패: {e}")
            raise
    
    async def _initialize_language_servers(self):
        """언어 서버들 초기화"""
        logger.info("LSP 서버들을 활성화하여 의미적 분석 수행")
        
        # Python LSP 서버
        await self._start_python_lsp()
        
        # TypeScript/JavaScript LSP 서버 (비활성화)
        # await self._start_typescript_lsp()
        
        # Java LSP 서버 (비활성화)
        # await self._start_java_lsp()
        
        logger.info("언어 서버들 초기화 완료 (Python LSP 활성화됨)")
    
    async def _start_python_lsp(self):
        """Python LSP 서버 시작"""
        try:
            # pylsp (Python Language Server) 시작
            process = await asyncio.create_subprocess_exec(
                'pylsp',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.clients['python'] = {
                'process': process,
                'language': 'python',
                'initialized': False
            }
            
            # LSP 초기화
            await self._initialize_lsp_client('python')
            
            logger.info("Python LSP 서버 시작 완료")
            
        except Exception as e:
            logger.warning(f"Python LSP 서버 시작 실패: {e}")
    
    async def _start_typescript_lsp(self):
        """TypeScript LSP 서버 시작"""
        try:
            # typescript-language-server 시작
            process = await asyncio.create_subprocess_exec(
                'typescript-language-server',
                '--stdio',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.clients['typescript'] = {
                'process': process,
                'language': 'typescript',
                'initialized': False
            }
            
            # LSP 초기화
            await self._initialize_lsp_client('typescript')
            
            logger.info("TypeScript LSP 서버 시작 완료")
            
        except Exception as e:
            logger.warning(f"TypeScript LSP 서버 시작 실패: {e}")
    
    async def _start_java_lsp(self):
        """Java LSP 서버 시작"""
        try:
            # Eclipse JDT Language Server 시작
            jdt_ls_path = Path.home() / '.local' / 'share' / 'eclipse-jdt-ls'
            if jdt_ls_path.exists():
                process = await asyncio.create_subprocess_exec(
                    'java',
                    '-jar',
                    str(jdt_ls_path / 'plugins' / 'org.eclipse.equinox.launcher_*.jar'),
                    '-configuration',
                    str(jdt_ls_path / 'config_linux'),
                    '-data',
                    str(jdt_ls_path / 'workspace'),
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                self.clients['java'] = {
                    'process': process,
                    'language': 'java',
                    'initialized': False
                }
                
                # LSP 초기화
                await self._initialize_lsp_client('java')
                
                logger.info("Java LSP 서버 시작 완료")
            
        except Exception as e:
            logger.warning(f"Java LSP 서버 시작 실패: {e}")
    
    async def _initialize_lsp_client(self, language: str):
        """LSP 클라이언트 초기화"""
        try:
            if language not in self.clients:
                return
            
            client = self.clients[language]
            process = client['process']
            
            # LSP 초기화 요청
            init_request = {
                'jsonrpc': '2.0',
                'id': self._get_next_request_id(),
                'method': 'initialize',
                'params': {
                    'processId': None,
                    'rootUri': None,
                    'capabilities': {
                        'textDocument': {
                            'definition': {'dynamicRegistration': True},
                            'references': {'dynamicRegistration': True},
                            'signatureHelp': {'dynamicRegistration': True},
                            'documentSymbol': {'dynamicRegistration': True}
                        }
                    }
                }
            }
            
            # 요청 전송
            request_data = json.dumps(init_request) + '\n'
            process.stdin.write(request_data.encode())
            await process.stdin.drain()
            
            # 응답 읽기
            response_data = await process.stdout.readline()
            if response_data:
                response = json.loads(response_data.decode())
                if 'result' in response:
                    client['initialized'] = True
                    logger.info(f"{language} LSP 클라이언트 초기화 완료")
            
        except Exception as e:
            logger.error(f"LSP 클라이언트 초기화 실패 {language}: {e}")
    
    def _get_language_from_file(self, filepath: str) -> str:
        """파일 확장자로부터 언어 결정"""
        ext = Path(filepath).suffix.lstrip('.').lower()
        language_map = {
            'py': 'python',
            'ts': 'typescript',
            'tsx': 'typescript',
            'js': 'typescript',
            'jsx': 'typescript',
            'java': 'java'
        }
        return language_map.get(ext, 'python')
    
    def _get_next_request_id(self) -> int:
        """다음 요청 ID 반환"""
        self._request_id += 1
        return self._request_id
    
    async def _send_lsp_request(self, language: str, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """LSP 요청 전송"""
        try:
            if language not in self.clients or not self.clients[language]['initialized']:
                return None
            
            client = self.clients[language]
            process = client['process']
            
            # LSP 요청 구성
            request = {
                'jsonrpc': '2.0',
                'id': self._get_next_request_id(),
                'method': method,
                'params': params
            }
            
            # 요청 전송
            request_data = json.dumps(request) + '\n'
            process.stdin.write(request_data.encode())
            await process.stdin.drain()
            
            # 응답 읽기
            response_data = await process.stdout.readline()
            if response_data:
                response = json.loads(response_data.decode())
                return response.get('result')
            
            return None
            
        except Exception as e:
            logger.error(f"LSP 요청 실패: {e}")
            return None
    
    async def get_definitions(self, filepath: str, position: LSPPosition) -> List[LSPLocation]:
        """정의로 이동 - 원본 executeGotoProvider 함수 포팅"""
        try:
            language = self._get_language_from_file(filepath)
            
            params = {
                'textDocument': {
                    'uri': f'file://{filepath}'
                },
                'position': {
                    'line': position.line,
                    'character': position.character
                }
            }
            
            result = await self._send_lsp_request(language, 'textDocument/definition', params)
            
            if not result:
                return []
            
            # 결과를 LSPLocation 객체로 변환
            locations = []
            if isinstance(result, list):
                for item in result:
                    location = LSPLocation(
                        uri=item['uri'],
                        range=LSPRange(
                            start=LSPPosition(
                                line=item['range']['start']['line'],
                                character=item['range']['start']['character']
                            ),
                            end=LSPPosition(
                                line=item['range']['end']['line'],
                                character=item['range']['end']['character']
                            )
                        )
                    )
                    locations.append(location)
            else:
                # 단일 결과인 경우
                location = LSPLocation(
                    uri=result['uri'],
                    range=LSPRange(
                        start=LSPPosition(
                            line=result['range']['start']['line'],
                            character=result['range']['start']['character']
                        ),
                        end=LSPPosition(
                            line=result['range']['end']['line'],
                            character=result['range']['end']['character']
                        )
                    )
                )
                locations.append(location)
            
            return locations
            
        except Exception as e:
            logger.error(f"정의 찾기 실패: {e}")
            return []
    
    async def get_references(self, filepath: str, position: LSPPosition) -> List[LSPLocation]:
        """참조 찾기 - 원본과 동일한 기능"""
        try:
            language = self._get_language_from_file(filepath)
            
            params = {
                'textDocument': {
                    'uri': f'file://{filepath}'
                },
                'position': {
                    'line': position.line,
                    'character': position.character
                }
            }
            
            result = await self._send_lsp_request(language, 'textDocument/references', params)
            
            if not result:
                return []
            
            # 결과를 LSPLocation 객체로 변환
            locations = []
            for item in result:
                location = LSPLocation(
                    uri=item['uri'],
                    range=LSPRange(
                        start=LSPPosition(
                            line=item['range']['start']['line'],
                            character=item['range']['start']['character']
                        ),
                        end=LSPPosition(
                            line=item['range']['end']['line'],
                            character=item['range']['end']['character']
                        )
                    )
                )
                locations.append(location)
            
            return locations
            
        except Exception as e:
            logger.error(f"참조 찾기 실패: {e}")
            return []
    
    async def get_signature_help(self, filepath: str, position: LSPPosition) -> Optional[LSPSignatureHelp]:
        """시그니처 도움말 - 원본 executeSignatureHelpProvider 함수 포팅"""
        try:
            language = self._get_language_from_file(filepath)
            
            params = {
                'textDocument': {
                    'uri': f'file://{filepath}'
                },
                'position': {
                    'line': position.line,
                    'character': position.character
                }
            }
            
            result = await self._send_lsp_request(language, 'textDocument/signatureHelp', params)
            
            if not result:
                return None
            
            return LSPSignatureHelp(
                signatures=result.get('signatures', []),
                active_signature=result.get('activeSignature'),
                active_parameter=result.get('activeParameter')
            )
            
        except Exception as e:
            logger.error(f"시그니처 도움말 실패: {e}")
            return None
    
    async def get_document_symbols(self, filepath: str) -> List[DocumentSymbol]:
        """문서 심볼 제공 - 원본 executeSymbolProvider 함수 포팅"""
        try:
            language = self._get_language_from_file(filepath)
            
            params = {
                'textDocument': {
                    'uri': f'file://{filepath}'
                }
            }
            
            result = await self._send_lsp_request(language, 'textDocument/documentSymbol', params)
            
            if not result:
                return []
            
            # 결과를 DocumentSymbol 객체로 변환
            symbols = []
            for item in result:
                symbol = DocumentSymbol(
                    name=item['name'],
                    range=LSPRange(
                        start=LSPPosition(
                            line=item['range']['start']['line'],
                            character=item['range']['start']['character']
                        ),
                        end=LSPPosition(
                            line=item['range']['end']['line'],
                            character=item['range']['end']['character']
                        )
                    ),
                    selection_range=LSPRange(
                        start=LSPPosition(
                            line=item['selectionRange']['start']['line'],
                            character=item['selectionRange']['start']['character']
                        ),
                        end=LSPPosition(
                            line=item['selectionRange']['end']['line'],
                            character=item['selectionRange']['end']['character']
                        )
                    ),
                    kind=item['kind']
                )
                symbols.append(symbol)
            
            return symbols
            
        except Exception as e:
            logger.error(f"문서 심볼 제공 실패: {e}")
            return []
    
    async def get_semantic_symbols(self, filepath: str) -> List[Dict[str, Any]]:
        """의미적 심볼 추출 - 요청하신 2.1 LSP 기반 심볼 추출 기능"""
        try:
            # 2.1.1 문서 심볼 추출
            document_symbols = await self.get_document_symbols(filepath)
            
            # 2.1.2 심볼 분류 및 가시성 분석
            semantic_symbols = []
            for symbol in document_symbols:
                # 심볼 분류
                symbol_type = self._classify_symbol_type(symbol.kind)
                
                # 가시성 분석
                visibility = self._analyze_visibility(symbol, filepath)
                
                # 의미적 정보 추가
                semantic_info = {
                    'name': symbol.name,
                    'type': symbol_type,
                    'kind': symbol.kind,
                    'visibility': visibility,
                    'range': {
                        'start': {
                            'line': symbol.range.start.line,
                            'character': symbol.range.start.character
                        },
                        'end': {
                            'line': symbol.range.end.line,
                            'character': symbol.range.end.character
                        }
                    },
                    'selection_range': {
                        'start': {
                            'line': symbol.selection_range.start.line,
                            'character': symbol.selection_range.start.character
                        },
                        'end': {
                            'line': symbol.selection_range.end.line,
                            'character': symbol.selection_range.end.character
                        }
                    }
                }
                
                semantic_symbols.append(semantic_info)
            
            return semantic_symbols
            
        except Exception as e:
            logger.error(f"의미적 심볼 추출 실패: {e}")
            return []
    
    def _classify_symbol_type(self, kind: int) -> str:
        """심볼 타입 분류 - 2.1.2 심볼 분류"""
        # LSP SymbolKind 매핑
        kind_map = {
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
        
        return kind_map.get(kind, 'unknown')
    
    def _analyze_visibility(self, symbol: DocumentSymbol, filepath: str) -> str:
        """가시성 분석 - 2.1.3 가시성 분석"""
        try:
            # 파일 내용 읽기
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            symbol_line = symbol.range.start.line
            
            if symbol_line < len(lines):
                line_content = lines[symbol_line]
                
                # Python 가시성 분석
                if filepath.endswith('.py'):
                    if line_content.strip().startswith('def _'):
                        return 'private'
                    elif line_content.strip().startswith('def __'):
                        return 'private'
                    elif line_content.strip().startswith('class _'):
                        return 'private'
                    else:
                        return 'public'
                
                # JavaScript/TypeScript 가시성 분석
                elif filepath.endswith(('.js', '.ts', '.jsx', '.tsx')):
                    if 'private' in line_content:
                        return 'private'
                    elif 'protected' in line_content:
                        return 'protected'
                    elif 'public' in line_content:
                        return 'public'
                    else:
                        return 'public'  # 기본값
                
                # Java 가시성 분석
                elif filepath.endswith('.java'):
                    if 'private' in line_content:
                        return 'private'
                    elif 'protected' in line_content:
                        return 'protected'
                    elif 'public' in line_content:
                        return 'public'
                    else:
                        return 'package'  # Java 기본 가시성
            
            return 'unknown'
            
        except Exception as e:
            logger.error(f"가시성 분석 실패: {e}")
            return 'unknown'
    
    async def shutdown(self):
        """LSP 서비스 종료"""
        try:
            for language, client in self.clients.items():
                try:
                    process = client['process']
                    if process.stdin:
                        # 종료 요청 전송
                        shutdown_request = {
                            'jsonrpc': '2.0',
                            'id': self._get_next_request_id(),
                            'method': 'shutdown',
                            'params': {}
                        }
                        
                        request_data = json.dumps(shutdown_request) + '\n'
                        process.stdin.write(request_data.encode())
                        await process.stdin.drain()
                        
                        # 프로세스 종료
                        process.terminate()
                        await process.wait()
                        
                except Exception as e:
                    logger.error(f"LSP 서버 종료 실패 {language}: {e}")
            
            self.clients.clear()
            logger.info("LSP 서비스 종료 완료")
            
        except Exception as e:
            logger.error(f"LSP 서비스 종료 실패: {e}")
