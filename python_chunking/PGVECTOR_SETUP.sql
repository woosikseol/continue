-- PostgreSQL + pgvector 초기 설정 SQL 스크립트
-- 이 스크립트는 Python 청킹 시스템을 위한 데이터베이스 및 테이블을 설정합니다.

-- 1. 데이터베이스 생성
CREATE DATABASE code_chunks;

-- 2. 데이터베이스에 연결
\c code_chunks;

-- 3. pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 4. chunks 테이블 생성
CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    uuid TEXT UNIQUE NOT NULL,
    path TEXT NOT NULL,
    cachekey TEXT NOT NULL,
    content TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    index INTEGER NOT NULL,
    metadata JSONB,
    embedding vector(384)  -- all-MiniLM-L6-v2 모델의 임베딩 차원
);

-- 5. 인덱스 생성
-- HNSW 인덱스: 벡터 유사도 검색을 위한 인덱스 (코사인 거리)
CREATE INDEX IF NOT EXISTS chunks_embedding_idx 
ON chunks USING hnsw (embedding vector_cosine_ops);

-- GIN 인덱스: JSONB 메타데이터 검색을 위한 인덱스
CREATE INDEX IF NOT EXISTS chunks_metadata_idx 
ON chunks USING gin (metadata);

-- B-tree 인덱스: 파일 경로 검색을 위한 인덱스
CREATE INDEX IF NOT EXISTS chunks_path_idx 
ON chunks (path);

-- B-tree 인덱스: 캐시키 검색을 위한 인덱스
CREATE INDEX IF NOT EXISTS chunks_cachekey_idx 
ON chunks (cachekey);

-- 6. 테이블 확인
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE tablename = 'chunks';

-- 7. 인덱스 확인
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'chunks';

-- 8. pgvector 확장 확인
SELECT * FROM pg_extension WHERE extname = 'vector';

COMMENT ON TABLE chunks IS '코드 청크 및 벡터 임베딩을 저장하는 테이블';
COMMENT ON COLUMN chunks.uuid IS '청크의 고유 식별자';
COMMENT ON COLUMN chunks.path IS '소스 파일의 전체 경로';
COMMENT ON COLUMN chunks.cachekey IS '파일의 해시 값 (캐시 키)';
COMMENT ON COLUMN chunks.content IS '청크의 실제 코드 내용';
COMMENT ON COLUMN chunks.start_line IS '청크의 시작 라인 번호';
COMMENT ON COLUMN chunks.end_line IS '청크의 종료 라인 번호';
COMMENT ON COLUMN chunks.index IS '파일 내 청크의 순서';
COMMENT ON COLUMN chunks.metadata IS 'JSONB 형태의 코드 메타데이터 (심볼, imports, exports 등)';
COMMENT ON COLUMN chunks.embedding IS '384차원 벡터 임베딩 (all-MiniLM-L6-v2)';

