"""
Main entry point for the Python chunking system.
"""
import asyncio
import sys
import argparse
import hashlib
from pathlib import Path
from typing import List
from core.index import PathAndCacheKey, RefreshIndexResults, IndexResultType
from core.indexing.pgvector_index import PgVectorIndex  # 변경
from core.embeddings.embeddings_provider import EmbeddingsProvider


class MockMarkCompleteCallback:
    """Mock callback for marking operations complete"""
    def __call__(self, items, result_type):
        # Silent completion - don't print to avoid cluttering output
        pass


def get_files_from_directory(directory_path: Path) -> List[PathAndCacheKey]:
    """
    디렉토리를 순회하여 모든 파일에 대한 PathAndCacheKey 리스트 생성
    
    Args:
        directory_path: 순회할 디렉토리 경로
        
    Returns:
        PathAndCacheKey 객체들의 리스트
    """
    # 지원되는 소스 코드 파일 확장자
    SUPPORTED_EXTENSIONS = {
        '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.cc', '.cxx',
        '.h', '.hpp', '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.kts',
        '.m', '.mm', '.scala', '.r', '.R', '.lua', '.pl', '.pm', '.sh', '.bash',
        '.sql', '.html', '.css', '.scss', '.sass', '.less', '.vue', '.dart',
        '.md', '.txt', '.json', '.yaml', '.yml', '.xml', '.toml', '.ini', '.cfg'
    }
    
    # 제외할 디렉토리 패턴
    EXCLUDED_DIRS = {
        '__pycache__', '.git', '.svn', '.hg', 'node_modules', '.venv', 'venv',
        'env', '.env', 'dist', 'build', 'target', '.idea', '.vscode', '.vs',
        'bin', 'obj', 'out', '.pytest_cache', '.mypy_cache', '.tox'
    }
    
    # 제외할 파일 패턴
    EXCLUDED_EXTENSIONS = {
        '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib', '.exe', '.bin',
        '.class', '.o', '.a', '.lib', '.jar', '.war', '.ear',
        '.min.js', '.min.css', '.map'
    }
    
    test_files = []
    
    if not directory_path.exists():
        print(f"Error: Directory '{directory_path}' does not exist")
        return test_files
    
    if not directory_path.is_dir():
        print(f"Error: '{directory_path}' is not a directory")
        return test_files
    
    # 디렉토리 내의 모든 파일 순회 (재귀적으로)
    for file_path in directory_path.rglob('*'):
        # 디렉토리는 건너뛰기
        if not file_path.is_file():
            continue
        
        # 제외할 디렉토리에 포함된 파일은 건너뛰기
        if any(excluded_dir in file_path.parts for excluded_dir in EXCLUDED_DIRS):
            continue
        
        # 파일 확장자 확인
        file_extension = file_path.suffix.lower()
        
        # 제외할 확장자는 건너뛰기
        if file_extension in EXCLUDED_EXTENSIONS:
            continue
        
        # 지원되는 확장자만 포함
        if file_extension in SUPPORTED_EXTENSIONS:
            # 파일 경로를 기반으로 고유한 cache_key 생성
            cache_key = hashlib.md5(str(file_path).encode()).hexdigest()
            
            test_files.append(
                PathAndCacheKey(
                    path=str(file_path),
                    cache_key=cache_key
                )
            )
    
    return test_files


async def main():
    """Main function demonstrating the chunking system"""
    print("Python Code Chunking System - Real Implementation")
    print("=" * 50)
    
    # 커맨드 라인 인자 파싱
    parser = argparse.ArgumentParser(description='Process code files in a directory for chunking')
    parser.add_argument(
        'directory',
        nargs='?',
        default='test_files',
        help='Directory path to process (default: test_files)'
    )
    args = parser.parse_args()
    
    # 디렉토리 경로 설정
    if Path(args.directory).is_absolute():
        target_dir = Path(args.directory)
    else:
        target_dir = Path(__file__).parent / args.directory
    
    print(f"Target directory: {target_dir}")
    print()
    
    # Initialize embeddings provider
    embeddings_provider = EmbeddingsProvider(max_embedding_chunk_size=500)
    
    # Initialize PgVector index with base_path for relative paths
    index = PgVectorIndex(embeddings_provider, base_path=str(target_dir))
    
    # 디렉토리에서 파일 목록 가져오기
    test_files = get_files_from_directory(target_dir)
    
    if not test_files:
        print("No files found to process")
        return
    
    print(f"Found {len(test_files)} files to process:")
    for file_info in test_files:
        print(f"  - {file_info.path}")
    print()
    
    # Create refresh results
    results = RefreshIndexResults(
        compute=test_files,
        add_tag=[],
        delete=[]
    )
    
    # Callback
    mark_complete = MockMarkCompleteCallback()
    
    print("Processing real code files...")
    
    # Update index
    async for progress in index.update("test_tag", results, mark_complete):
        print(f"Progress: {progress.desc} - {progress.status} ({progress.progress})")
    
    print("\nTesting retrieval with real queries...")
    
    # Test different queries
    queries = [
        "calculator class",
        "add method function",
        "divide by zero error",
        "main function",
        "history calculation"
    ]
    
    for query in queries:
        print(f"\n--- Query: '{query}' ---")
        chunks = await index.retrieve(query, n_retrieve=3)
        print(f"Retrieved {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks, 1):
            filename = Path(chunk.filepath).name
            print(f"  {i}. {filename}:{chunk.start_line}-{chunk.end_line}")
            
            # 메타데이터 출력
            if chunk.metadata:
                if chunk.metadata.symbol_type and chunk.metadata.symbol_name:
                    print(f"     Symbol: {chunk.metadata.symbol_type} '{chunk.metadata.symbol_name}'")
                if chunk.metadata.imports:
                    imports_str = ', '.join(chunk.metadata.imports[:3])
                    if len(chunk.metadata.imports) > 3:
                        imports_str += f" ... (+{len(chunk.metadata.imports) - 3})"
                    print(f"     Imports: {imports_str}")
            
            content_preview = chunk.content.replace('\n', ' ').strip()[:80]
            print(f"     Content: {content_preview}...")
            print()


if __name__ == "__main__":
    asyncio.run(main())
