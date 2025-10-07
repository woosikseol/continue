# Python Code Chunking System

이 프로젝트는 TypeScript 기반의 Continue 프로젝트의 코드 청킹 시스템을 Python으로 포팅한 것입니다. Tree-sitter를 사용하여 Java, JavaScript, Python 기반의 소스코드를 구조적으로 청킹할 수 있습니다.

## 기능

- **Tree-sitter 기반 파싱**: C++ 기반의 Tree-sitter 파서를 Python에서 직접 사용
- **스마트 청킹**: AST 노드별로 구조적 청킹 수행
- **다중 언어 지원**: Java, JavaScript, Python 등 다양한 언어 지원
- **LanceDB 벡터 저장**: 벡터 임베딩을 통한 유사도 검색

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

### 기본 사용법

```python
import asyncio
from core.indexing.lance_db_index import LanceDbIndex
from core.index import ILLM, PathAndCacheKey

async def main():
    # 임베딩 프로바이더 초기화
    embeddings_provider = ILLM(max_embedding_chunk_size=1000)
    
    # LanceDB 인덱스 초기화
    index = LanceDbIndex(embeddings_provider)
    
    # 파일 청킹
    file_item = PathAndCacheKey(path="example.py", cache_key="hash123")
    chunks = await index.get_chunks(file_item, "your code content here")
    
    # 검색
    results = await index.retrieve("query", n_retrieve=10)

if __name__ == "__main__":
    asyncio.run(main())
```

### 실행

**전체 시스템 실행:**
```bash
python main.py
```

**간단한 테스트:**
```bash
python test_simple.py
```

**완전한 설치 및 실행 순서:**
```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. Tree-sitter 파서 설정
python setup_vendor.py    # 소스 다운로드
python build_parsers.py   # 파서 컴파일

# 3. 실행
python main.py           # 전체 시스템
python test_simple.py    # 간단한 테스트
```

## 아키텍처

### 청킹 프로세스

1. **파일 타입 확인**: 확장자를 기반으로 코드 파일인지 확인
2. **Tree-sitter 파싱**: 지원되는 언어의 경우 Tree-sitter로 AST 생성
3. **스마트 축소**: `getSmartCollapsedChunks`로 AST 노드별 구조적 청킹
4. **토큰 검증**: 최대 토큰 수 제한 확인
5. **벡터 임베딩**: LanceDB에 저장

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
