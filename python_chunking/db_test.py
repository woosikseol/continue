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
        # pandas 출력 옵션 설정
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 100)
        
        columns_to_display = [col for col in df.columns if col not in ['vector', 'embedding']]
        print(df[columns_to_display])
        print(f"\n총 {len(df)}개의 행이 있습니다.")
        
        # 메타데이터 상세 출력
        print("\n--- [ 메타데이터 상세 ] ---")
        for idx, row in df.iterrows():
            print(f"\n청크 #{idx}:")
            print(f"  파일: {row['path']}")
            print(f"  라인: {row['start_line']}-{row['end_line']}")
            print(f"  인덱스: {row['index']}")
            
            # 메타데이터 파싱 및 출력
            if row['metadata']:
                import json
                try:
                    metadata = json.loads(row['metadata'])
                    if metadata.get('symbol_type') or metadata.get('symbol_name'):
                        print(f"  심볼: {metadata.get('symbol_type', 'N/A')} '{metadata.get('symbol_name', 'N/A')}'")
                    if metadata.get('imports'):
                        print(f"  Import: {', '.join(metadata['imports'][:3])}{'...' if len(metadata['imports']) > 3 else ''}")
                    if metadata.get('exports'):
                        print(f"  Export: {', '.join(metadata['exports'])}")
                    if metadata.get('references_to'):
                        refs = ', '.join(metadata['references_to'][:5])
                        if len(metadata['references_to']) > 5:
                            refs += f" ... (+{len(metadata['references_to']) - 5})"
                        print(f"  참조: {refs}")
                except:
                    print(f"  메타데이터: {row['metadata'][:100]}...")
            else:
                print("  메타데이터: 없음")
        
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