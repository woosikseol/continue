import asyncio
import lancedb
import pandas as pd
from pathlib import Path
from core.indexing.lance_db_index import LanceDbIndex
from core.embeddings.embeddings_provider import EmbeddingsProvider

DB_PATH = "/Users/woosik/repository/continue/python_chunking/data/lancedb"
TABLE_NAME = "chunks"


async def main():
    # 데이터베이스 연결 및 테이블 조회(요약)
    db = lancedb.connect(DB_PATH)
    print(f"✅ LanceDB에 성공적으로 연결되었습니다: {DB_PATH}")
    table = db.open_table(TABLE_NAME)
    print(f"✅ 테이블 '{TABLE_NAME}'을 열었습니다.")

    df = table.to_pandas()
    print("\n--- [ 테이블 데이터 ] ---")
    if df.empty:
        print(f"테이블 '{TABLE_NAME}'에는 데이터가 없습니다.")
    else:
        columns_to_display = [col for col in df.columns if col not in ['vector', 'embedding']]
        print(df[columns_to_display])
        print(f"\n총 {len(df)}개의 행이 있습니다.")
        print("\n--- [ 파일별 청크 개수 ] ---")
        print(df['path'].value_counts())

    # LanceDbIndex 초기화 및 검색 테스트
    print("\nTesting retrieval with real queries...")
    queries = [
        "calculator class",
        "add method function",
        "divide by zero error",
        "main function",
        "history calculation",
    ]

    index = LanceDbIndex(EmbeddingsProvider())
    await index.initialize()
    # retrieve 내부에서 테이블 오픈 보장

    for query in queries:
        print(f"\n--- Query: '{query}' ---")
        chunks = await index.retrieve(query, n_retrieve=5)
        print(f"Retrieved {len(chunks)} chunks")
        for i, chunk in enumerate(chunks, 1):
            filename = Path(chunk.filepath).name
            print(f"  {i}. {filename}:{chunk.start_line}-{chunk.end_line}")
            content_preview = chunk.content.replace('\n', ' ').strip()[:80]
            print(f"     Content: {content_preview}...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ 데이터를 확인하는 중 오류가 발생했습니다: {e}")