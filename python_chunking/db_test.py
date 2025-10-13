import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from pathlib import Path
from core.indexing.pgvector_index import PgVectorIndex
from core.embeddings.embeddings_provider import EmbeddingsProvider

CONNECTION_STRING = "postgresql://localhost/code_chunks"


async def main():
    # PostgreSQL 연결 및 데이터 조회
    conn = psycopg2.connect(CONNECTION_STRING)
    print(f"✅ PostgreSQL에 성공적으로 연결되었습니다: {CONNECTION_STRING}")
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # 테이블 존재 확인
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'chunks'
            );
        """)
        table_exists = cur.fetchone()['exists']
        
        if not table_exists:
            print("⚠️  테이블 'chunks'가 존재하지 않습니다.")
            conn.close()
            return
        
        print("✅ 테이블 'chunks'을 찾았습니다.")
        
        # 전체 데이터 조회 (embedding 제외)
        cur.execute("""
            SELECT id, uuid, path, cachekey, content, start_line, end_line, index, metadata
            FROM chunks
            ORDER BY path, start_line
        """)
        rows = cur.fetchall()
        
        print("\n--- [ 테이블 데이터 ] ---")
        if not rows:
            print("테이블 'chunks'에는 데이터가 없습니다.")
        else:
            print(f"총 {len(rows)}개의 행이 있습니다.\n")
            
            # 메타데이터 상세 출력 (처음 10개만)
            print("--- [ 메타데이터 상세 (처음 10개) ] ---")
            for idx, row in enumerate(rows[:10]):
                print(f"\n청크 #{idx}:")
                print(f"  ID: {row['id']}")
                print(f"  파일: {row['path']}")
                print(f"  라인: {row['start_line']}-{row['end_line']}")
                print(f"  인덱스: {row['index']}")
                
                # 메타데이터 파싱 및 출력
                if row['metadata']:
                    try:
                        metadata = row['metadata'] if isinstance(row['metadata'], dict) else json.loads(row['metadata'])
                        if metadata.get('symbol_type') or metadata.get('symbol_name'):
                            print(f"  심볼: {metadata.get('symbol_type', 'N/A')} '{metadata.get('symbol_name', 'N/A')}'")
                        if metadata.get('imports'):
                            imports_list = metadata['imports'][:3]
                            imports_str = ', '.join(imports_list)
                            if len(metadata['imports']) > 3:
                                imports_str += '...'
                            print(f"  Import: {imports_str}")
                        if metadata.get('exports'):
                            print(f"  Export: {', '.join(metadata['exports'][:3])}{'...' if len(metadata['exports']) > 3 else ''}")
                        if metadata.get('references_to'):
                            refs = ', '.join(metadata['references_to'][:5])
                            if len(metadata['references_to']) > 5:
                                refs += f" ... (+{len(metadata['references_to']) - 5})"
                            print(f"  참조: {refs}")
                        
                        # 크로스 파일 메타데이터 (새로 추가됨)
                        if metadata.get('referenced_by'):
                            ref_by = ', '.join(metadata['referenced_by'][:3])
                            if len(metadata['referenced_by']) > 3:
                                ref_by += f" ... (+{len(metadata['referenced_by']) - 3})"
                            print(f"  ✨ Referenced by: {ref_by}")
                        if metadata.get('subclasses'):
                            print(f"  ✨ Subclasses: {', '.join(metadata['subclasses'])}")
                        if metadata.get('dependencies'):
                            print(f"  ✨ Dependencies: {', '.join(metadata['dependencies'])}")
                        if metadata.get('dependents'):
                            print(f"  ✨ Dependents: {', '.join(metadata['dependents'])}")
                    except Exception as e:
                        print(f"  메타데이터 파싱 오류: {e}")
                else:
                    print("  메타데이터: 없음")
            
            # 파일별 청크 개수
            print("\n--- [ 파일별 청크 개수 ] ---")
            cur.execute("""
                SELECT path, COUNT(*) as count
                FROM chunks
                GROUP BY path
                ORDER BY count DESC
            """)
            file_counts = cur.fetchall()
            for fc in file_counts:
                print(f"  {Path(fc['path']).name}: {fc['count']}개")
    
    conn.close()

    # PgVectorIndex 초기화 및 검색 테스트
    print("\n\nTesting retrieval with real queries...")
    queries = [
        "calculator class",
        "add method function",
        "divide by zero error",
        "main function",
        "history calculation",
    ]

    # base_path를 설정하여 상대 경로를 절대 경로로 변환
    base_path = Path(__file__).parent / "test_files"
    index = PgVectorIndex(EmbeddingsProvider(), base_path=str(base_path))
    await index.initialize()

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