# Python Code Chunking System

이 프로젝트는 TypeScript 기반의 Continue 프로젝트의 코드 청킹 시스템을 Python으로 포팅한 것입니다. Tree-sitter를 사용하여 Java, JavaScript, Python 기반의 소스코드를 구조적으로 청킹할 수 있습니다.

## 기능

- **Tree-sitter 기반 파싱**: C++ 기반의 Tree-sitter 파서를 Python에서 직접 사용
- **스마트 청킹**: AST 노드별로 구조적 청킹 수행
- **다중 언어 지원**: Java, JavaScript, Python 등 다양한 언어 지원
- **pgvector 벡터 저장**: PostgreSQL + pgvector를 사용한 벡터 임베딩 및 유사도 검색
- **통합 메타데이터**: JSONB를 활용한 풍부한 코드 메타데이터 저장
- **크로스 파일 분석**: 파일 간 관계 자동 분석 (referenced_by, subclasses, dependencies, dependents)

## 설치

### 1. 가상환경 설정 (권장)

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 또는
.venv\Scripts\activate     # Windows
```

### 2. 의존성 설치

**옵션 B: 수동 설치**
```bash
pip install -r requirements.txt
```

**만약 sentence-transformers 설치에 문제가 있다면:**
```bash
# 호환되는 버전으로 설치
pip install "huggingface_hub>=0.19.0,<0.25.0"
pip install "sentence-transformers>=2.5.0,<3.0.0"
```

### 3. Tree-sitter 파서 설정

**3-1. 파서 소스 다운로드**
```bash
python setup_vendor.py
```

이 스크립트는 다음 파서들을 다운로드합니다:
- tree-sitter-python (v0.20.0)
- tree-sitter-javascript (v0.20.1)
- tree-sitter-java (v0.20.0)

**3-2. 파서 컴파일**
```bash
python build_parsers.py
```

이 스크립트는 다운로드된 소스를 컴파일하여 실행 가능한 `.so` 파일을 생성합니다:
- `build/languages-python.so`
- `build/languages-javascript.so`
- `build/languages-java.so`

## 사용법

### 0. PostgreSQL 및 pgvector 설정

```bash
# PostgreSQL 및 pgvector 설치 (macOS)
brew install postgresql pgvector
brew services start postgresql

# 데이터베이스 생성
psql postgres
CREATE DATABASE code_chunks;
\c code_chunks;
CREATE EXTENSION vector;

# 테이블 생성 (아래 SQL 실행)
```

```sql
CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    uuid TEXT UNIQUE NOT NULL,
    path TEXT NOT NULL,
    cachekey TEXT NOT NULL,
    content TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    index INTEGER NOT NULL,
    metadata JSONB,
    embedding vector(384)
);

CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON chunks USING gin (metadata);
CREATE INDEX ON chunks (path);
CREATE INDEX ON chunks (cachekey);
```

### 1. 기본 사용법

```python
import asyncio
from core.indexing.pgvector_index import PgVectorIndex
from core.embeddings.embeddings_provider import EmbeddingsProvider
from core.index import PathAndCacheKey

async def main():
    # 임베딩 프로바이더 초기화
    embeddings_provider = EmbeddingsProvider()
    
    # PgVector 인덱스 초기화 (base_path 지정하여 상대 경로 사용)
    index = PgVectorIndex(
        embeddings_provider,
        base_path="/path/to/your/project"
    )
    await index.initialize()
    
    # 파일 청킹
    file_item = PathAndCacheKey(path="example.py", cache_key="hash123")
    chunks = await index.get_chunks(file_item, "your code content here")
    
    # 임베딩 생성 및 저장 (상대 경로로 저장됨)
    embeddings = await index.get_embeddings(chunks)
    await index.insert_chunks(chunks, embeddings)
    
    # 검색 (절대 경로로 반환됨)
    results = await index.retrieve("calculator class", n_retrieve=10)
    
    # 필터링 검색 (상대 경로로 필터링)
    results = await index.retrieve(
        "add function",
        n_retrieve=5,
        filters={"path": "example.py"}
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. 실행

**디렉토리 인덱싱:**
```bash
# 특정 디렉토리의 코드 파일 인덱싱
python main.py ./test_files

# 다른 디렉토리 인덱싱
python main.py /path/to/your/code
```

**데이터 확인 및 검색:**
```bash
# 저장된 데이터 확인 및 벡터 검색 테스트
python db_test.py
```

**데이터 삭제:**
```bash
# 대화형으로 데이터 삭제 (확인 요청)
python drop_table.py

# 확인 없이 즉시 삭제 (주의!)
python drop_table.py --force

# 테이블 자체를 삭제 (주의!)
python drop_table.py --drop-table --force
```

**완전한 설치 및 실행 순서:**
```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. PostgreSQL 및 pgvector 설정
psql postgres < PGVECTOR_SETUP.sql

# 3. Tree-sitter 파서 설정
python setup_vendor.py    # 소스 다운로드
python build_parsers.py   # 파서 컴파일

# 4. 코드 인덱싱
python main.py ./test_files

# 5. 데이터 확인
python db_test.py
```

## 아키텍처

### 청킹 프로세스 (2-Pass)

#### Pass 1: 단일 파일 분석
1. **파일 타입 확인**: 확장자를 기반으로 코드 파일인지 확인
2. **Tree-sitter 파싱**: 지원되는 언어의 경우 Tree-sitter로 AST 생성
3. **스마트 축소**: `getSmartCollapsedChunks`로 AST 노드별 구조적 청킹
4. **토큰 검증**: 최대 토큰 수 제한 확인
5. **메타데이터 추출**: 심볼, imports, exports, 참조 관계 등
6. **벡터 임베딩 및 저장**: PostgreSQL + pgvector에 저장

#### Pass 2: 크로스 파일 분석
1. **심볼 맵 구축**: 모든 심볼 정의 수집
2. **referenced_by**: 누가 나를 참조하는가
3. **subclasses**: 누가 나를 상속하는가
4. **dependencies**: 내가 의존하는 파일들
5. **dependents**: 누가 나를 의존하는가
6. **업데이트된 메타데이터 재저장**

### 지원 언어

- **Python**: `.py`, `.pyw`, `.pyi`
- **JavaScript**: `.js`, `.jsx`, `.mjs`, `.cjs`
- **Java**: `.java`
- **TypeScript**: `.ts`, `.tsx`, `.mts`, `.cts`
- **C/C++**: `.c`, `.h`, `.cpp`, `.hpp`
- 기타 다수 언어 지원

### 청킹 전략

- **코드 파일**: Tree-sitter 기반 구조적 청킹
- **비코드 파일**: 토큰 기반 기본 청킹
- **스마트 축소**: 클래스, 함수, 메서드 단위로 축소
- **토큰 제한**: 최대 청크 크기 내에서 토큰 수 제한

## 프로젝트 구조

```
python_chunking/
├── core/
│   ├── index.py                    # 핵심 타입 정의
│   ├── llm/
│   │   └── count_tokens.py         # 토큰 카운팅
│   ├── indexing/
│   │   ├── lance_db_index.py       # LanceDB 인덱스
│   │   └── chunk/
│   │       ├── basic.py            # 기본 청킹
│   │       ├── code.py             # 코드 청킹
│   │       └── chunk.py            # 청킹 조정
│   └── util/
│       ├── tree_sitter.py          # Tree-sitter 유틸리티
│       └── uri.py                  # URI 유틸리티
├── vendor/                         # Tree-sitter 파서들
├── main.py                         # 메인 실행 파일
├── setup_vendor.py                # 파서 설정 스크립트
└── requirements.txt               # 의존성
```

## 원본과의 차이점

- **언어**: TypeScript → Python
- **파서**: 동일한 Tree-sitter (C++ 기반) 사용
- **구조**: 원본과 동일한 디렉토리 구조 유지
- **기능**: 동일한 청킹 로직과 결과

## 라이선스

원본 Continue 프로젝트와 동일한 라이선스를 따릅니다.
