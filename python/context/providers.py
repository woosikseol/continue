"""
컨텍스트 제공자들
원본 TypeScript context providers의 Python 포팅
다양한 소스에서 컨텍스트 정보 제공
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from continue_types import ContextItemWithId, ContextItemId, Position, Range

logger = logging.getLogger(__name__)

@dataclass
class ContextProviderConfig:
    """컨텍스트 제공자 설정"""
    max_items: int = 10
    include_documentation: bool = True
    include_examples: bool = True

class ContextProvider:
    """컨텍스트 제공자 - 원본 TypeScript context providers의 Python 포팅"""
    
    def __init__(self, config: Optional[ContextProviderConfig] = None):
        self.config = config or ContextProviderConfig()
        self._context_cache: Dict[str, List[ContextItemWithId]] = {}
        
        logger.info("컨텍스트 제공자 초기화 완료")
    
    async def get_context(self, query: str, filepath: str) -> List[ContextItemWithId]:
        """컨텍스트 제공 - 원본과 동일한 기능"""
        try:
            # 캐시 확인
            cache_key = f"{query}:{filepath}"
            if cache_key in self._context_cache:
                return self._context_cache[cache_key]
            
            context_items = []
            
            # 파일 컨텍스트
            file_context = await self._get_file_context(filepath)
            context_items.extend(file_context)
            
            # 코드베이스 컨텍스트
            codebase_context = await self._get_codebase_context(query, filepath)
            context_items.extend(codebase_context)
            
            # 문서 컨텍스트
            if self.config.include_documentation:
                doc_context = await self._get_documentation_context(query)
                context_items.extend(doc_context)
            
            # 예제 컨텍스트
            if self.config.include_examples:
                example_context = await self._get_example_context(query)
                context_items.extend(example_context)
            
            # 결과 제한
            context_items = context_items[:self.config.max_items]
            
            # 캐시 저장
            self._context_cache[cache_key] = context_items
            
            return context_items
            
        except Exception as e:
            logger.error(f"컨텍스트 제공 실패: {e}")
            return []
    
    async def _get_file_context(self, filepath: str) -> List[ContextItemWithId]:
        """파일 컨텍스트 제공"""
        try:
            if not Path(filepath).exists():
                return []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 파일 내용을 청크로 분할
            chunks = self._split_content_into_chunks(content)
            
            context_items = []
            for i, chunk in enumerate(chunks):
                item = ContextItemWithId(
                    id=ContextItemId(
                        provider_title="file",
                        item_id=f"{filepath}:{i}"
                    ),
                    content=chunk,
                    name=f"{Path(filepath).name} (chunk {i+1})",
                    description=f"File content from {filepath}",
                    icon="📄"
                )
                context_items.append(item)
            
            return context_items
            
        except Exception as e:
            logger.error(f"파일 컨텍스트 제공 실패: {e}")
            return []
    
    async def _get_codebase_context(self, query: str, filepath: str) -> List[ContextItemWithId]:
        """코드베이스 컨텍스트 제공"""
        try:
            # 현재 파일의 디렉토리에서 관련 파일들 찾기
            current_dir = Path(filepath).parent
            related_files = []
            
            # 같은 디렉토리의 파일들
            for file_path in current_dir.glob("*.py"):
                if file_path.name != Path(filepath).name:
                    related_files.append(file_path)
            
            # 하위 디렉토리의 파일들
            for file_path in current_dir.rglob("*.py"):
                if file_path.name != Path(filepath).name and len(related_files) < 5:
                    related_files.append(file_path)
            
            context_items = []
            for file_path in related_files[:5]:  # 최대 5개 파일
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 쿼리와 관련된 부분만 추출
                    relevant_content = self._extract_relevant_content(content, query)
                    
                    if relevant_content:
                        item = ContextItemWithId(
                            id=ContextItemId(
                                provider_title="codebase",
                                item_id=str(file_path)
                            ),
                            content=relevant_content,
                            name=file_path.name,
                            description=f"Related code from {file_path}",
                            icon="📁"
                        )
                        context_items.append(item)
                        
                except Exception as e:
                    logger.debug(f"파일 읽기 실패 {file_path}: {e}")
                    continue
            
            return context_items
            
        except Exception as e:
            logger.error(f"코드베이스 컨텍스트 제공 실패: {e}")
            return []
    
    async def _get_documentation_context(self, query: str) -> List[ContextItemWithId]:
        """문서 컨텍스트 제공"""
        try:
            # 간단한 문서 컨텍스트 시뮬레이션
            doc_items = []
            
            # Python 표준 라이브러리 문서
            if "import" in query.lower() or "module" in query.lower():
                item = ContextItemWithId(
                    id=ContextItemId(
                        provider_title="documentation",
                        item_id="python_imports"
                    ),
                    content="Python import statements allow you to use modules and packages in your code. Common patterns include:\n- import module_name\n- from module_name import function_name\n- import module_name as alias",
                    name="Python Imports",
                    description="Documentation about Python import statements",
                    icon="📚"
                )
                doc_items.append(item)
            
            # 함수 정의 문서
            if "def" in query.lower() or "function" in query.lower():
                item = ContextItemWithId(
                    id=ContextItemId(
                        provider_title="documentation",
                        item_id="python_functions"
                    ),
                    content="Python functions are defined using the 'def' keyword. They can have parameters, return values, and docstrings for documentation.",
                    name="Python Functions",
                    description="Documentation about Python function definitions",
                    icon="📚"
                )
                doc_items.append(item)
            
            return doc_items
            
        except Exception as e:
            logger.error(f"문서 컨텍스트 제공 실패: {e}")
            return []
    
    async def _get_example_context(self, query: str) -> List[ContextItemWithId]:
        """예제 컨텍스트 제공"""
        try:
            example_items = []
            
            # 쿼리에 따른 예제 제공
            if "class" in query.lower():
                item = ContextItemWithId(
                    id=ContextItemId(
                        provider_title="examples",
                        item_id="class_example"
                    ),
                    content="class MyClass:\n    def __init__(self, value):\n        self.value = value\n    \n    def get_value(self):\n        return self.value",
                    name="Class Example",
                    description="Example of a Python class definition",
                    icon="💡"
                )
                example_items.append(item)
            
            if "async" in query.lower() or "await" in query.lower():
                item = ContextItemWithId(
                    id=ContextItemId(
                        provider_title="examples",
                        item_id="async_example"
                    ),
                    content="async def fetch_data():\n    async with aiohttp.ClientSession() as session:\n        async with session.get('https://api.example.com') as response:\n            return await response.json()",
                    name="Async Example",
                    description="Example of async/await usage",
                    icon="💡"
                )
                example_items.append(item)
            
            return example_items
            
        except Exception as e:
            logger.error(f"예제 컨텍스트 제공 실패: {e}")
            return []
    
    def _split_content_into_chunks(self, content: str, chunk_size: int = 1000) -> List[str]:
        """내용을 청크로 분할"""
        try:
            lines = content.split('\n')
            chunks = []
            current_chunk = []
            current_size = 0
            
            for line in lines:
                line_size = len(line) + 1  # +1 for newline
                
                if current_size + line_size > chunk_size and current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = [line]
                    current_size = line_size
                else:
                    current_chunk.append(line)
                    current_size += line_size
            
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
            
            return chunks
            
        except Exception as e:
            logger.error(f"내용 분할 실패: {e}")
            return [content]
    
    def _extract_relevant_content(self, content: str, query: str) -> Optional[str]:
        """쿼리와 관련된 내용 추출"""
        try:
            lines = content.split('\n')
            relevant_lines = []
            
            query_words = query.lower().split()
            
            for line in lines:
                line_lower = line.lower()
                # 쿼리 단어 중 하나라도 포함된 라인
                if any(word in line_lower for word in query_words if len(word) > 2):
                    relevant_lines.append(line)
            
            if relevant_lines:
                # 관련 라인들 주변의 컨텍스트도 포함
                context_lines = []
                for i, line in enumerate(lines):
                    if line in relevant_lines:
                        # 앞뒤 2줄씩 포함
                        start = max(0, i - 2)
                        end = min(len(lines), i + 3)
                        context_lines.extend(lines[start:end])
                
                return '\n'.join(context_lines)
            
            return None
            
        except Exception as e:
            logger.error(f"관련 내용 추출 실패: {e}")
            return None
    
    def clear_cache(self):
        """컨텍스트 캐시 초기화"""
        self._context_cache.clear()
        logger.info("컨텍스트 캐시 초기화 완료")
    
    async def get_context_for_position(self, filepath: str, position: Position) -> List[ContextItemWithId]:
        """특정 위치의 컨텍스트 제공"""
        try:
            if not Path(filepath).exists():
                return []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 위치 주변의 코드 추출
            start_line = max(0, position.line - 5)
            end_line = min(len(lines), position.line + 6)
            
            context_content = ''.join(lines[start_line:end_line])
            
            item = ContextItemWithId(
                id=ContextItemId(
                    provider_title="position",
                    item_id=f"{filepath}:{position.line}:{position.character}"
                ),
                content=context_content,
                name=f"Context around line {position.line + 1}",
                description=f"Code context around position in {Path(filepath).name}",
                icon="📍"
            )
            
            return [item]
            
        except Exception as e:
            logger.error(f"위치 컨텍스트 제공 실패: {e}")
            return []
