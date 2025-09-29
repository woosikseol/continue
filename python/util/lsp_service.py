"""
LSP 서비스
원본 TypeScript LSP 관련 코드의 Python 포팅
Language Server Protocol을 사용하여 정확한 의미론적 분석 제공
"""

import asyncio
import logging
import subprocess
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict

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
        # 백그라운드 reader task 관리
        self._reader_tasks: Dict[str, asyncio.Task] = {}
        self._response_futures: Dict[str, Dict[int, asyncio.Future]] = defaultdict(dict)
        self._message_queues: Dict[str, asyncio.Queue] = {}
    
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
        
        # TypeScript/JavaScript LSP 서버
        await self._start_typescript_lsp()
        
        # Java LSP 서버
        await self._start_java_lsp()
        
        logger.info("언어 서버들 초기화 완료")
    
    async def _start_python_lsp(self):
        """Python LSP 서버 시작 - 개선된 버전"""
        try:
            # Python LSP 서버 경로들 확인
            pylsp_paths = [
                # 현재 프로젝트 venv
                '/Users/woosik/repository/continue/python/.venv/bin/pylsp',
                # 시스템 전역 설치
                'pylsp',
                '/usr/local/bin/pylsp',
                '/opt/homebrew/bin/pylsp',
                # pip 사용자 설치
                str(Path.home() / '.local' / 'bin' / 'pylsp'),
                # conda 환경
                'python -m pylsp',
            ]
            
            process = None
            for pylsp_path in pylsp_paths:
                try:
                    if pylsp_path.startswith('python -m'):
                        # Python 모듈로 실행하는 경우
                        process = await asyncio.create_subprocess_exec(
                            'python', '-m', 'pylsp',
                            stdin=asyncio.subprocess.PIPE,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                            cwd=os.getcwd()
                        )
                    else:
                        # 직접 실행하는 경우
                        process = await asyncio.create_subprocess_exec(
                            pylsp_path,
                            stdin=asyncio.subprocess.PIPE,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                            cwd=os.getcwd()
                        )
                    
                    # 프로세스가 성공적으로 시작되었는지 확인
                    if process and process.returncode is None:
                        logger.info(f"Python LSP 서버 시작: {pylsp_path}")
                        break
                        
                except Exception as path_error:
                    logger.debug(f"Python LSP 경로 시도 실패 {pylsp_path}: {path_error}")
                    continue
            
            if not process or process.returncode is not None:
                raise Exception("Python LSP 서버를 찾을 수 없음")
            
            self.clients['python'] = {
                'process': process,
                'language': 'python',
                'initialized': False
            }
            
            # 1. 백그라운드 reader task 먼저 시작 (무한 대기 방지)
            await self._start_reader_task('python')
            
            # 2. LSP 초기화 (reader task가 준비된 후)
            await self._initialize_lsp_client('python')
            
            logger.info("Python LSP 서버 시작 완료")
            
        except Exception as e:
            logger.warning(f"Python LSP 서버 시작 실패: {e}")
            logger.info("Python LSP 서버 설치 방법: pip install python-lsp-server")
    
    async def _start_typescript_lsp(self):
        """TypeScript LSP 서버 시작 - 개선된 버전"""
        try:
            # typescript-language-server 경로 확인 및 시작
            ts_server_paths = [
                'typescript-language-server',
                '/usr/local/bin/typescript-language-server',
                '/opt/homebrew/bin/typescript-language-server',
                'npx typescript-language-server'
            ]
            
            process = None
            for ts_path in ts_server_paths:
                try:
                    if ts_path.startswith('npx'):
                        # npx로 실행하는 경우
                        process = await asyncio.create_subprocess_exec(
                            'npx', 'typescript-language-server', '--stdio',
                            stdin=asyncio.subprocess.PIPE,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                            cwd=os.getcwd()
                        )
                    else:
                        # 직접 실행하는 경우
                        process = await asyncio.create_subprocess_exec(
                            ts_path, '--stdio',
                            stdin=asyncio.subprocess.PIPE,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                            cwd=os.getcwd()
                        )
                    
                    # 프로세스가 성공적으로 시작되었는지 확인
                    if process and process.returncode is None:
                        logger.info(f"TypeScript LSP 서버 시작: {ts_path}")
                        break
                        
                except Exception as path_error:
                    logger.debug(f"TypeScript LSP 경로 시도 실패 {ts_path}: {path_error}")
                    continue
            
            if not process or process.returncode is not None:
                raise Exception("TypeScript LSP 서버를 찾을 수 없음")
            
            self.clients['typescript'] = {
                'process': process,
                'language': 'typescript',
                'initialized': False
            }
            
            # 1. 백그라운드 reader task 먼저 시작
            await self._start_reader_task('typescript')
            
            # 2. LSP 초기화
            await self._initialize_lsp_client('typescript')
            
            logger.info("TypeScript LSP 서버 시작 완료")
            
        except Exception as e:
            logger.warning(f"TypeScript LSP 서버 시작 실패: {e}")
            logger.info("TypeScript LSP 서버 설치 방법: npm install -g typescript-language-server typescript")
    
    async def _start_java_lsp(self):
        """Java LSP 서버 시작 - 개선된 버전"""
        try:
            # Java LSP 서버 경로들 확인
            java_lsp_paths = [
                # Eclipse JDT Language Server 경로들
                Path.home() / '.local' / 'share' / 'eclipse-jdt-ls',
                Path.home() / 'eclipse-jdt-ls',
                Path('/opt/eclipse-jdt-ls'),
                Path('/usr/local/share/eclipse-jdt-ls'),
                # VSCode 확장에서 사용하는 경로
                Path.home() / '.vscode' / 'extensions' / 'redhat.java-*' / 'server',
            ]
            
            # Homebrew 설치 경로들 확인 (libexec 구조)
            homebrew_paths = [
                # Intel Mac
                Path('/usr/local/Cellar/jdtls'),
                # Apple Silicon Mac  
                Path('/opt/homebrew/Cellar/jdtls'),
            ]
            
            # Homebrew jdtls 버전별 경로 추가
            for base_path in homebrew_paths:
                if base_path.exists():
                    import glob
                    version_dirs = glob.glob(str(base_path / '*'))
                    for version_dir in version_dirs:
                        libexec_path = Path(version_dir) / 'libexec'
                        if libexec_path.exists():
                            java_lsp_paths.append(libexec_path)
            
            process = None
            jdt_ls_path = None
            
            # 설치된 JDT LS 찾기
            for path in java_lsp_paths:
                if '*' in str(path):
                    # 와일드카드 패턴 처리
                    import glob
                    matching_paths = glob.glob(str(path))
                    if matching_paths:
                        jdt_ls_path = Path(matching_paths[0])
                        break
                elif path.exists():
                    jdt_ls_path = path
                    break
                elif 'jdtls' in str(path) and path.parent.exists():
                    # Homebrew 버전별 경로 확인
                    import glob
                    version_paths = glob.glob(str(path) + '*')
                    if version_paths:
                        # 최신 버전 선택
                        jdt_ls_path = Path(sorted(version_paths)[-1])
                        break
            
            if jdt_ls_path and jdt_ls_path.exists():
                # launcher jar 파일 찾기
                plugins_dir = jdt_ls_path / 'plugins'
                if plugins_dir.exists():
                    launcher_jars = list(plugins_dir.glob('org.eclipse.equinox.launcher_*.jar'))
                    if launcher_jars:
                        launcher_jar = launcher_jars[0]
                        
                        # 운영체제별 설정 디렉토리 (Homebrew는 libexec 구조 사용)
                        config_dirs = [
                            jdt_ls_path / 'config_mac',
                            jdt_ls_path / 'config_mac_arm',
                            jdt_ls_path / 'config_linux',
                            jdt_ls_path / 'config_linux_arm',
                            jdt_ls_path / 'config_win'
                        ]
                        
                        config_dir = None
                        for cfg in config_dirs:
                            if cfg.exists():
                                config_dir = cfg
                                break
                        
                        if not config_dir:
                            config_dir = jdt_ls_path / 'config_linux'  # 기본값
                        
                        # 워크스페이스 디렉토리
                        workspace_dir = jdt_ls_path / 'workspace'
                        workspace_dir.mkdir(exist_ok=True)
                        
                        # Java LSP 서버 실행
                        java_cmd = [
                            'java',
                            '-Declipse.application=org.eclipse.jdt.ls.core.id1',
                            '-Dosgi.bundles.defaultStartLevel=4',
                            '-Declipse.product=org.eclipse.jdt.ls.core.product',
                            '-Dlog.protocol=true',
                            '-Dlog.level=ALL',
                            '-jar', str(launcher_jar),
                            '-configuration', str(config_dir),
                            '-data', str(workspace_dir),
                            '--add-modules=ALL-SYSTEM',
                            '--add-opens', 'java.base/java.util=ALL-UNNAMED',
                            '--add-opens', 'java.base/java.lang=ALL-UNNAMED'
                        ]
                        
                        process = await asyncio.create_subprocess_exec(
                            *java_cmd,
                            stdin=asyncio.subprocess.PIPE,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                            cwd=os.getcwd()
                        )
                        
                        logger.info(f"Java LSP 서버 시작: {jdt_ls_path}")
                    else:
                        raise Exception("Eclipse JDT LS launcher jar를 찾을 수 없음")
                else:
                    raise Exception("Eclipse JDT LS plugins 디렉토리를 찾을 수 없음")
            else:
                # jdtls 명령어로 시도 (Homebrew 등으로 설치된 경우)
                jdtls_commands = [
                    'jdtls',
                    '/usr/local/bin/jdtls',
                    '/opt/homebrew/bin/jdtls',
                    'java -jar /usr/local/Cellar/jdtls/*/libexec/plugins/org.eclipse.equinox.launcher_*.jar'
                ]
                
                for cmd in jdtls_commands:
                    try:
                        if cmd.startswith('java -jar'):
                            # Java jar 명령어로 실행
                            import glob
                            jar_patterns = [
                                '/usr/local/Cellar/jdtls/*/libexec/plugins/org.eclipse.equinox.launcher_*.jar',
                                '/opt/homebrew/Cellar/jdtls/*/libexec/plugins/org.eclipse.equinox.launcher_*.jar'
                            ]
                            
                            jar_path = None
                            for pattern in jar_patterns:
                                jars = glob.glob(pattern)
                                if jars:
                                    jar_path = jars[0]
                                    break
                            
                            if jar_path:
                                process = await asyncio.create_subprocess_exec(
                                    'java', '-jar', jar_path,
                                    stdin=asyncio.subprocess.PIPE,
                                    stdout=asyncio.subprocess.PIPE,
                                    stderr=asyncio.subprocess.PIPE,
                                    cwd=os.getcwd()
                                )
                                logger.info(f"Java LSP 서버 시작: {jar_path}")
                                break
                        else:
                            # 직접 명령어 실행
                            process = await asyncio.create_subprocess_exec(
                                cmd,
                                stdin=asyncio.subprocess.PIPE,
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE,
                                cwd=os.getcwd()
                            )
                            logger.info(f"Java LSP 서버 시작: {cmd}")
                            break
                            
                    except Exception as e:
                        logger.debug(f"Java LSP 명령어 시도 실패 {cmd}: {e}")
                        continue
                
                if not process:
                    raise Exception("Java LSP 서버를 찾을 수 없음")
            
            if not process or process.returncode is not None:
                raise Exception("Java LSP 서버 프로세스 시작 실패")
            
            self.clients['java'] = {
                'process': process,
                'language': 'java',
                'initialized': False
            }
            
            # 1. 백그라운드 reader task 먼저 시작
            await self._start_reader_task('java')
            
            # 2. LSP 초기화
            await self._initialize_lsp_client('java')
            
            logger.info("Java LSP 서버 시작 완료")
            
        except Exception as e:
            logger.warning(f"Java LSP 서버 시작 실패: {e}")
            logger.info("Java LSP 서버 설치 방법:")
            logger.info("1. Eclipse JDT LS 다운로드: https://download.eclipse.org/jdtls/milestones/")
            logger.info("2. 또는 Homebrew: brew install jdtls")
    
    async def _initialize_lsp_client(self, language: str):
        """LSP 클라이언트 초기화 - 올바른 LSP 프로토콜"""
        try:
            if language not in self.clients:
                return
            
            client = self.clients[language]
            process = client['process']
            
            # 1. 올바른 LSP 초기화 요청
            init_request = {
                'jsonrpc': '2.0',
                'id': self._get_next_request_id(),
                'method': 'initialize',
                'params': {
                    'processId': os.getpid(),
                    'rootUri': f"file://{os.getcwd()}",
                    'capabilities': {
                        'textDocument': {
                            'documentSymbol': {'dynamicRegistration': True},
                            'definition': {'dynamicRegistration': True},
                            'references': {'dynamicRegistration': True},
                            'signatureHelp': {'dynamicRegistration': True},
                            'completion': {
                                'dynamicRegistration': True,
                                'completionItem': {
                                    'snippetSupport': True,
                                    'commitCharactersSupport': True
                                }
                            }
                        },
                        'workspace': {
                            'workspaceFolders': True,
                            'configuration': True
                        }
                    },
                    'clientInfo': {
                        'name': 'continue-python-analyzer',
                        'version': '1.0.0'
                    }
                }
            }
            
            # 2. Content-Length 헤더와 함께 요청 전송 (LSP 프로토콜 필수)
            content = json.dumps(init_request)
            content_bytes = content.encode('utf-8')
            request_data = f"Content-Length: {len(content_bytes)}\r\n\r\n{content}"
            
            process.stdin.write(request_data.encode())
            await process.stdin.drain()
            
            # 3. Future 생성 및 대기 (무한 대기 방지)
            request_id = init_request['id']
            future = asyncio.Future()
            self._response_futures[language][request_id] = future
            
            try:
                # 응답 대기 (백그라운드 reader가 처리) - 무한 대기 방지
                result = await asyncio.wait_for(future, timeout=30.0)  # 30초 내에 초기화 완료
                if result and isinstance(result, dict) and 'capabilities' in result:
                    client['initialized'] = True
                    logger.info(f"{language} LSP 클라이언트 초기화 성공")
                    
                    # 4. initialized 알림 전송
                    await self._send_initialized_notification_async(language)
                else:
                    logger.warning(f"{language} LSP 초기화 응답 부적절: {result}")
            except asyncio.TimeoutError:
                logger.error(f"{language} LSP 초기화 타임아웃 (30초)")
            except Exception as e:
                logger.error(f"{language} LSP 초기화 예외: {e}")
            finally:
                # Future 정리
                self._response_futures[language].pop(request_id, None)
                
        except Exception as e:
            logger.error(f"LSP 클라이언트 초기화 실패 {language}: {e}")
    
    # 제거됨: _read_lsp_response - 무한 대기 방지를 위해 삭제
    # 이제 reader task가 모든 응답을 처리함
    
    async def _send_initialized_notification_async(self, language: str):
        """initialized 알림 전송 - 비동기"""
        try:
            if language not in self.clients:
                return
                
            client = self.clients[language]
            process = client['process']
            
            # initialized 알림
            notification = {
                'jsonrpc': '2.0',
                'method': 'initialized',
                'params': {}
            }
            
            content = json.dumps(notification)
            content_bytes = content.encode('utf-8')
            request_data = f"Content-Length: {len(content_bytes)}\r\n\r\n{content}"
            
            process.stdin.write(request_data.encode())
            await process.stdin.drain()
            
            logger.info(f"{language} LSP initialized 알림 전송 완료")
            
        except Exception as e:
            logger.warning(f"{language} initialized 알림 전송 실패: {e}")
    
    async def _start_reader_task(self, language: str):
        """백그라운드 reader task 시작"""
        try:
            if language not in self.clients:
                return
                
            client = self.clients[language]
            process = client['process']
            
            # 메시지 큐 생성
            self._message_queues[language] = asyncio.Queue()
            
            # reader task 시작
            self._reader_tasks[language] = asyncio.create_task(
                self._reader_loop(language, process)
            )
            
            logger.info(f"{language} 백그라운드 reader task 시작")
            
        except Exception as e:
            logger.error(f"{language} reader task 시작 실패: {e}")
    
    async def _reader_loop(self, language: str, process):
        """백그라운드 reader 루프 - 무한 대기 방지"""
        try:
            while True:
                # 프로세스 상태 확인
                if process.returncode is not None:
                    logger.warning(f"{language} LSP 프로세스 종료됨: {process.returncode}")
                    break
                
                # 메시지 읽기
                message = await self._read_lsp_message(process)
                if message is None:
                    # 프로세스가 종료되었거나 읽기 실패
                    break
                
                # 메시지 처리
                await self._handle_lsp_message(language, message)
                
        except Exception as e:
            logger.error(f"{language} reader loop 실패: {e}")
        finally:
            # 모든 대기 중인 Future를 에러로 깨우기
            await self._cleanup_futures(language)
    
    async def _read_lsp_message(self, process) -> Optional[Dict[str, Any]]:
        """LSP 메시지 읽기 - 견고한 헤더 파싱"""
        try:
            # Content-Length 헤더 읽기 (견고한 파싱)
            content_length = 0
            while True:
                # 비동기 대기 없이 줄 읽기 (무한 대기 방지)
                try:
                    line_bytes = await asyncio.wait_for(process.stdout.readline(), timeout=0.1)
                except asyncio.TimeoutError:
                    # 데이터가 준비되지 않았으면 잠시 대기
                    await asyncio.sleep(0.01)
                    continue
                
                if not line_bytes:
                    # 프로세스가 정상적으로 종료됨
                    logger.info("LSP 프로세스 정상 종료")
                    return None
                
                line = line_bytes.decode('utf-8').strip()
                if line == '':
                    break  # 빈 줄 (헤더 끝)
                
                if line.startswith('Content-Length:'):
                    content_length = int(line.split(':', 1)[1].strip())
                # 다른 헤더는 무시 (Content-Type 등)
            
            # 메시지 본문 읽기 (비동기 대기 없이)
            if content_length > 0:
                try:
                    # 정확한 길이만큼 읽기 (무한 대기 방지)
                    message_data = await asyncio.wait_for(
                        process.stdout.readexactly(content_length), 
                        timeout=5.0  # 메시지 대기 시간 제한
                    )
                    message_json = json.loads(message_data.decode('utf-8'))
                    logger.debug(f"LSP 메시지 수신: {message_json.get('method', message_json.get('id', 'unknown'))}")
                    return message_json
                except asyncio.TimeoutError:
                    logger.warning(f"LSP 메시지 수신 타임아웃: {content_length} 바이트")
                    return None
                except json.JSONDecodeError as e:
                    logger.error(f"LSP 메시지 JSON 파싱 실패: {e}")
                    return None
            else:
                logger.warning("Content-Length가 0인 LSP 메시지")
                return None
                
        except Exception as e:
            logger.error(f"LSP 메시지 읽기 예외: {e}")
            # 예외 발생 시도 None 반환 (프로세스 종료 안함)
            return None
    
    async def _handle_lsp_message(self, language: str, message: Dict[str, Any]):
        """LSP 메시지 처리 - 요청-응답 매칭"""
        try:
            # 응답 메시지인 경우
            if 'id' in message and 'result' in message:
                request_id = message['id']
                if request_id in self._response_futures[language]:
                    future = self._response_futures[language].pop(request_id)
                    future.set_result(message['result'])
                    logger.debug(f"{language} 응답 처리 완료: {request_id}")
            
            # 에러 메시지인 경우
            elif 'id' in message and 'error' in message:
                request_id = message['id']
                if request_id in self._response_futures[language]:
                    future = self._response_futures[language].pop(request_id)
                    # 에러를 예외로 처리하지 않고 None으로 처리 (프로세스 종료 방지)
                    future.set_result(None)
                    logger.warning(f"{language} LSP 에러 응답: {message['error']} (ID: {request_id})")
            
            # 알림 메시지인 경우 (처리하지 않음)
            elif 'method' in message:
                logger.debug(f"{language} 알림 수신: {message['method']}")
                
        except Exception as e:
            logger.error(f"{language} 메시지 처리 예외: {e}")
            # 예외가 발생해도 프로세스를 종료하지 않음
    
    async def _cleanup_futures(self, language: str):
        """대기 중인 Future들 정리 - 강제 종료 아닌 정상 완료 처리"""
        try:
            completed_futures = 0
            for request_id, future in list(self._response_futures[language].items()):
                if not future.done():
                    # 예외 대신 빈 결과로 완료 처리 (종료 아닌 완료)
                    future.set_result(None)
                    completed_futures += 1
            self._response_futures[language].clear()
            if completed_futures > 0:
                logger.info(f"{language} Future {completed_futures}개 정상 완료 처리")
        except Exception as e:
            logger.error(f"{language} Future 정리 예외: {e}")
    
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
    
    async def _open_document(self, filepath: str, language: str):
        """파일을 LSP 서버에 열기 (textDocument/didOpen)"""
        try:
            # 파일 내용 읽기
            with open(filepath, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # LSP 언어 ID 매핑
            language_id_map = {
                'python': 'python',
                'typescript': 'typescript',
                'javascript': 'javascript',
                'java': 'java'
            }
            language_id = language_id_map.get(language, 'python')
            
            # textDocument/didOpen 알림 전송
            did_open_params = {
                'textDocument': {
                    'uri': f'file://{filepath}',
                    'languageId': language_id,
                    'version': 1,
                    'text': file_content
                }
            }
            
            # 알림 전송 (응답 대기 없음)
            await self._send_lsp_notification(language, 'textDocument/didOpen', did_open_params)
            
            # publishDiagnostics 알림을 기다리기 위해 잠시 대기
            await asyncio.sleep(0.1)
            
            logger.debug(f"{language} 파일 열기 완료: {filepath}")
            
        except Exception as e:
            logger.error(f"{language} 파일 열기 실패 {filepath}: {e}")
    
    async def _send_lsp_notification(self, language: str, method: str, params: Dict[str, Any]):
        """엘스피 알림 전송 (응답 없음)"""
        try:
            if language not in self.clients or not self.clients[language]['initialized']:
                return
            
            client = self.clients[language]
            process = client['process']
            
            # LSP 알림 구성
            notification = {
                'jsonrpc': '2.0',
                'method': method,
                'params': params
            }
            
            # Content-Length 헤더와 함께 전송
            content = json.dumps(notification)
            content_bytes = content.encode('utf-8')
            request_data = f"Content-Length: {len(content_bytes)}\r\n\r\n{content}"
            
            process.stdin.write(request_data.encode())
            await process.stdin.drain()
            
            logger.debug(f"{language} LSP 알림 전송: {method}")
            
        except Exception as e:
            logger.error(f"LSP 알림 전송 실패: {e}")
    
    async def _send_lsp_request(self, language: str, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """LSP 요청 전송 - 비동기 Future 기반"""
        try:
            if language not in self.clients or not self.clients[language]['initialized']:
                return None
            
            client = self.clients[language]
            process = client['process']
            
            # 요청 ID 생성
            request_id = self._get_next_request_id()
            
            # LSP 요청 구성
            request = {
                'jsonrpc': '2.0',
                'id': request_id,
                'method': method,
                'params': params
            }
            
            # Content-Length 헤더와 함께 전송 (바이트 길이 계산)
            content = json.dumps(request)
            content_bytes = content.encode('utf-8')
            request_data = f"Content-Length: {len(content_bytes)}\r\n\r\n{content}"
            
            process.stdin.write(request_data.encode())
            await process.stdin.drain()
            
            # Future 생성 및 대기
            future = asyncio.Future()
            self._response_futures[language][request_id] = future
            
            # 응답 대기 (무한 대기 방지)
            try:
                result = await future
                return result
            except Exception as e:
                logger.error(f"{language} LSP 요청 실패: {e}")
                return None
            finally:
                # Future 정리
                self._response_futures[language].pop(request_id, None)
            
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
        """문서 심볼 제공 - 파일 열기 후 심볼 추출"""
        try:
            language = self._get_language_from_file(filepath)
            
            # 1. 파일을 LSP 서버에 열기 (textDocument/didOpen)
            await self._open_document(filepath, language)
            
            # 2. 심볼 요청
            params = {
                'textDocument': {
                    'uri': f'file://{filepath}'
                }
            }
            
            result = await self._send_lsp_request(language, 'textDocument/documentSymbol', params)
            
            if not result:
                return []
            
            # 결과를 DocumentSymbol 객체로 변환 (SymbolInformation 형식 처리)
            symbols = []
            for item in result:
                # pylsp는 SymbolInformation 형식으로 응답 (location.range)
                if 'location' in item and 'range' in item['location']:
                    location_range = item['location']['range']
                    symbol = DocumentSymbol(
                        name=item['name'],
                        range=LSPRange(
                            start=LSPPosition(
                                line=location_range['start']['line'],
                                character=location_range['start']['character']
                            ),
                            end=LSPPosition(
                                line=location_range['end']['line'],
                                character=location_range['end']['character']
                            )
                        ),
                        selection_range=LSPRange(
                            start=LSPPosition(
                                line=location_range['start']['line'],
                                character=location_range['start']['character']
                            ),
                            end=LSPPosition(
                                line=location_range['end']['line'],
                                character=location_range['end']['character']
                            )
                        ),
                        kind=item['kind']
                    )
                    symbols.append(symbol)
                # DocumentSymbol 형식도 지원 (range 직접 접근)
                elif 'range' in item:
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
                                line=item.get('selectionRange', item['range'])['start']['line'],
                                character=item.get('selectionRange', item['range'])['start']['character']
                            ),
                            end=LSPPosition(
                                line=item.get('selectionRange', item['range'])['end']['line'],
                                character=item.get('selectionRange', item['range'])['end']['character']
                            )
                        ),
                        kind=item['kind']
                    )
                    symbols.append(symbol)
                else:
                    logger.warning(f"알 수 없는 심볼 형식: {item}")
            
            return symbols
            
        except Exception as e:
            logger.error(f"문서 심볼 제공 실패: {e}")
            logger.debug(f"심볼 응답 내용: {result}")
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
    
    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """LSP 서버들의 상태 반환"""
        status = {}
        for language, client in self.clients.items():
            process = client['process']
            status[language] = {
                'initialized': client.get('initialized', False),
                'process_running': process.returncode is None if process else False,
                'reader_task_active': language in self._reader_tasks and not self._reader_tasks[language].done(),
                'pending_requests': len(self._response_futures.get(language, {}))
            }
        return status
    
    def is_server_ready(self, language: str) -> bool:
        """특정 언어 서버가 준비되었는지 확인"""
        if language not in self.clients:
            return False
        
        client = self.clients[language]
        process = client['process']
        
        return (
            client.get('initialized', False) and
            process and process.returncode is None and
            language in self._reader_tasks and not self._reader_tasks[language].done()
        )
    
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
            
            # Reader task들 정리
            for language, task in self._reader_tasks.items():
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            self._reader_tasks.clear()
            self._response_futures.clear()
            self._message_queues.clear()
            self.clients.clear()
            logger.info("LSP 서비스 종료 완료")
            
        except Exception as e:
            logger.error(f"LSP 서비스 종료 실패: {e}")
