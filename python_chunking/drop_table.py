import psycopg2
import sys
import argparse
from psycopg2.extras import RealDictCursor

CONNECTION_STRING = "postgresql://localhost/code_chunks"
TABLE_NAME = "chunks"

def main():
    parser = argparse.ArgumentParser(description='PostgreSQL chunks 테이블의 데이터를 삭제합니다.')
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='--force 옵션을 표시 (실제로는 항상 바로 삭제됩니다)'
    )
    parser.add_argument(
        '--drop-table',
        action='store_true',
        help='데이터뿐만 아니라 테이블 자체도 삭제 (주의: 테이블 구조도 삭제됩니다!)'
    )
    args = parser.parse_args()
    
    try:
        # PostgreSQL 연결
        conn = psycopg2.connect(CONNECTION_STRING)
        print(f"✅ PostgreSQL에 연결되었습니다: {CONNECTION_STRING}")
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 테이블 존재 확인
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (TABLE_NAME,))
            table_exists = cur.fetchone()['exists']
            
            if not table_exists:
                print(f"⚠️  테이블 '{TABLE_NAME}'가 존재하지 않습니다.")
                return
            
            print(f"✅ 테이블 '{TABLE_NAME}'을 찾았습니다.")
            
            # 현재 데이터 개수 확인
            cur.execute(f"SELECT COUNT(*) as count FROM {TABLE_NAME}")
            current_count = cur.fetchone()['count']
            print(f"현재 데이터 개수: {current_count}개")
            
            if current_count == 0 and not args.drop_table:
                print("삭제할 데이터가 없습니다.")
                return
            
            # 바로 삭제 실행
            if args.force:
                print("⚠️  --force 옵션이 지정되어 삭제합니다.")
            else:
                if args.drop_table:
                    print(f"⚠️  테이블 '{TABLE_NAME}'과 모든 데이터({current_count}개)를 삭제합니다.")
                else:
                    print(f"⚠️  {current_count}개의 데이터를 삭제합니다.")
            
            # 삭제 실행
            if args.drop_table:
                # 테이블 자체를 삭제
                cur.execute(f"DROP TABLE IF EXISTS {TABLE_NAME} CASCADE")
                conn.commit()
                print(f"✅ 테이블 '{TABLE_NAME}'이 완전히 삭제되었습니다.")
            else:
                # 데이터만 삭제 (테이블 구조는 유지)
                cur.execute(f"DELETE FROM {TABLE_NAME}")
                conn.commit()
                print(f"✅ 테이블 '{TABLE_NAME}'의 모든 데이터가 삭제되었습니다.")
                
                # 삭제 후 확인
                cur.execute(f"SELECT COUNT(*) as count FROM {TABLE_NAME}")
                remaining_count = cur.fetchone()['count']
                print(f"남은 데이터 개수: {remaining_count}개")
        
        conn.close()
        print("✅ 데이터베이스 연결이 종료되었습니다.")
            
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL 오류 발생: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()