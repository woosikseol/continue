"""
Main entry point for the Python chunking system.
"""
import asyncio
import sys
from pathlib import Path
from core.index import PathAndCacheKey, RefreshIndexResults, IndexResultType
from core.indexing.lance_db_index import LanceDbIndex
from core.embeddings.embeddings_provider import EmbeddingsProvider


class MockMarkCompleteCallback:
    """Mock callback for marking operations complete"""
    def __call__(self, items, result_type):
        print(f"Marked {len(items)} items as {result_type.value}")


async def main():
    """Main function demonstrating the chunking system"""
    print("Python Code Chunking System - Real Implementation")
    print("=" * 50)
    
    # Initialize embeddings provider
    embeddings_provider = EmbeddingsProvider(max_embedding_chunk_size=500)
    
    # Initialize LanceDB index
    index = LanceDbIndex(embeddings_provider)
    
    # Real test files
    test_files_dir = Path(__file__).parent / "test_files"
    test_files = [
        PathAndCacheKey(
            path=str(test_files_dir / "Calculator.py"),
            cache_key="py_calculator_hash"
        ),
        PathAndCacheKey(
            path=str(test_files_dir / "Calculator.js"), 
            cache_key="js_calculator_hash"
        ),
        PathAndCacheKey(
            path=str(test_files_dir / "Calculator.java"),
            cache_key="java_calculator_hash"
        ),
    ]
    
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
