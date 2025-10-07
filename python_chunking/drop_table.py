import lancedb

DB_PATH = "/Users/woosik/repository/continue/python_chunking/data/lancedb"
TABLE_NAME = "chunks"

try:
    # 데이터베이스 연결
    db = lancedb.connect(DB_PATH)
    print(f"✅ LanceDB에 연결되었습니다: {DB_PATH}")
    
    # 테이블 열기
    table = db.open_table(TABLE_NAME)
    print(f"✅ 테이블 '{TABLE_NAME}'을 열었습니다.")
    
    # 현재 데이터 개수 확인 (다른 방법)
    df = table.to_pandas()
    current_count = len(df)
    print(f"현재 데이터 개수: {current_count}개")
    
    if current_count > 0:
        # 모든 데이터 삭제
        db.drop_table(TABLE_NAME)
        print(f"✅ 테이블 '{TABLE_NAME}'이 삭제되었습니다.")
        
    else:
        print("삭제할 데이터가 없습니다.")
        
except Exception as e:
    print(f"❌ 오류 발생: {e}")