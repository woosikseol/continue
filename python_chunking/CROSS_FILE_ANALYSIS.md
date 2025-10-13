# 크로스 파일 분석 (Cross-File Analysis)

## 📋 개요

Python 청킹 시스템에 **크로스 파일 분석** 기능이 추가되었습니다. 이제 파일 간의 관계를 자동으로 분석하여 4가지 메타데이터를 제공합니다.

## ✨ 새로 추가된 메타데이터

### 1. `referenced_by` - 누가 나를 참조하는가?

**설명**: 현재 심볼을 참조하는 다른 파일/청크들의 위치

**예시**:
```python
# chunk_document 함수 (chunk/chunk.py)
referenced_by: [
    "pgvector_index.py:41",
    "pgvector_index.py:320",
    "lance_db_index.py:48"
]
```

**활용**:
- 함수나 클래스가 어디에서 사용되는지 추적
- 리팩토링 시 영향 범위 파악
- 사용되지 않는 코드 감지

---

### 2. `subclasses` - 누가 나를 상속하는가?

**설명**: 현재 클래스를 상속하는 자식 클래스들

**예시**:
```python
# Calculator 클래스
subclasses: [
    "ScientificCalculator",
    "GraphingCalculator",
    "ProgrammerCalculator"
]
```

**활용**:
- 클래스 계층 구조 파악
- 상속 관계 시각화
- 인터페이스 변경 시 영향 받는 클래스 파악

---

### 3. `dependencies` - 내가 의존하는 파일들

**설명**: 현재 파일이 import한 심볼들이 실제로 어떤 파일에서 왔는지

**예시**:
```python
# chunk/chunk.py
imports: ["basic_chunker", "code_chunker", "extract_metadata_from_node"]
dependencies: [
    "chunk/basic.py",
    "chunk/code.py",
    "chunk/metadata.py"
]
```

**활용**:
- 의존성 그래프 생성
- 순환 의존성 감지
- 모듈 간 결합도 분석

---

### 4. `dependents` - 누가 나를 의존하는가?

**설명**: 현재 파일을 import하는 다른 파일들

**예시**:
```python
# chunk/metadata.py
exports: ["extract_node_text", "extract_symbol_name", ...]
dependents: [
    "chunk/code.py",
    "chunk/chunk.py"
]
```

**활용**:
- 역의존성 추적
- 파일 삭제/변경 시 영향 범위 파악
- 핵심 모듈 식별

---

## 🔧 구현 방식

### 2-Pass 접근법

#### Pass 1: 단일 파일 분석
```python
for file in all_files:
    chunks = extract_chunks(file)
    for chunk in chunks:
        # 단일 파일 내에서 추출 가능한 메타데이터
        chunk.metadata.symbol_type = "class"
        chunk.metadata.symbol_name = "Calculator"
        chunk.metadata.imports = ["numpy", "pandas"]
        chunk.metadata.references_to = ["add", "subtract"]
        chunk.metadata.extends = "BaseCalculator"
```

#### Pass 2: 크로스 파일 분석
```python
# 1. 심볼 맵 구축
symbol_map = {"Calculator": [chunk1, chunk2, ...], ...}
file_exports = {"Calculator.py": ["Calculator", "add"], ...}

# 2. 역방향 관계 구축
for chunk in all_chunks:
    # referenced_by
    for other_chunk in all_chunks:
        if chunk.symbol_name in other_chunk.references_to:
            chunk.referenced_by.append(other_chunk.location)
    
    # subclasses
    if other_chunk.extends == chunk.symbol_name:
        chunk.subclasses.append(other_chunk.symbol_name)
    
    # dependencies
    for imported in chunk.imports:
        for file, exports in file_exports.items():
            if imported in exports:
                chunk.dependencies.append(file)
    
    # dependents (dependencies의 역방향)
    for dep_file in chunk.dependencies:
        dep_chunks[dep_file].dependents.append(chunk.file)
```

---

## 📊 통계 예시

### core/indexing 디렉토리 분석 결과

```
총 청크 수: 57
referenced_by가 있는 청크: 37 (64.9%)
subclasses가 있는 청크: 0 (0.0%)
dependencies가 있는 청크: 14 (24.6%)
dependents가 있는 청크: 30 (52.6%)
```

### 가장 많이 참조되는 심볼 (Top 5)

| 심볼 | 타입 | 참조 횟수 | 파일 |
|------|------|----------|------|
| `initialize` | function | 9 | pgvector_index.py |
| `initialize` | function | 9 | lance_db_index.py |
| `extract_node_text` | function | 9 | chunk/metadata.py |
| `extract_symbol_name` | function | 8 | chunk/metadata.py |
| `find_child_by_type` | function | 7 | chunk/metadata.py |

### 가장 많은 dependents를 가진 파일

| 파일 | Dependents 수 | 의존하는 파일들 |
|------|--------------|----------------|
| `chunk/metadata.py` | 2 | chunk/code.py, chunk/chunk.py |
| `chunk/basic.py` | 1 | chunk/chunk.py |
| `chunk/code.py` | 1 | chunk/chunk.py |

---

## 🚀 사용 예시

### 인덱싱

```bash
# 자동으로 2-pass 분석 수행
python main.py ./core/indexing
```

출력:
```
=== Pass 1: Single File Analysis ===
Inserted 1 chunks into PostgreSQL
Inserted 13 chunks into PostgreSQL
...

=== Pass 2: Cross-File Analysis (58 chunks) ===
Inserted 58 chunks into PostgreSQL
```

### 데이터 확인

```bash
python db_test.py
```

출력 예시:
```
청크 #4:
  파일: chunk/chunk.py
  심볼: file 'chunk.py'
  Export: chunk_document_without_id, chunk_document, should_chunk
  ✨ Dependencies: chunk/basic.py, chunk/code.py, chunk/metadata.py

청크 #5:
  파일: chunk/chunk.py
  심볼: function 'chunk_document_without_id'
  ✨ Referenced by: chunk/chunk.py:0, chunk/chunk.py:51
  ✨ Dependencies: chunk/basic.py, chunk/code.py, chunk/metadata.py
```

### Python으로 직접 쿼리

```python
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect('postgresql://localhost/code_chunks')
cur = conn.cursor(cursor_factory=RealDictCursor)

# 특정 함수를 참조하는 모든 위치 찾기
cur.execute("""
    SELECT path, start_line, metadata->'referenced_by' as refs
    FROM chunks 
    WHERE metadata->>'symbol_name' = 'chunk_document'
    AND jsonb_array_length(metadata->'referenced_by') > 0
""")

for row in cur.fetchall():
    print(f"{row['path']}: {row['refs']}")
```

---

## 🎯 활용 시나리오

### 1. 리팩토링 영향 분석
```python
# initialize 함수를 변경하면 어디에 영향이 있을까?
referenced_by: [
    "pgvector_index.py:147",
    "pgvector_index.py:306",
    "lance_db_index.py:75",
    ...
]
# → 9곳에서 사용 중! 신중하게 변경 필요
```

### 2. 순환 의존성 감지
```python
# A.py → B.py → C.py → A.py 순환 감지
A.dependencies: ["B.py"]
B.dependencies: ["C.py"]
C.dependencies: ["A.py"]  # 순환!
```

### 3. 핵심 모듈 식별
```python
# 가장 많은 dependents = 가장 중요한 모듈
chunk/metadata.py: 2 dependents
→ 핵심 모듈! 변경 시 주의 필요
```

### 4. 데드 코드 감지
```python
# referenced_by가 비어있음 = 사용되지 않는 코드?
def unused_function():
    pass
# referenced_by: []  # 어디서도 호출되지 않음!
```

---

## ⚙️ 성능

### 시간 복잡도
- Pass 1 (단일 파일): O(n) - n은 파일 수
- Pass 2 (크로스 파일): O(c²) - c는 청크 수
  - 최적화: 심볼 맵을 사용하여 실제로는 O(c × s) - s는 평균 심볼 참조 수

### 실제 성능
```
8개 파일, 58개 청크:
- Pass 1: ~5초
- Pass 2: ~1초
총: ~6초
```

---

## 📈 미래 개선 사항

### 현재 제한사항
1. **Dynamic imports** 지원 안됨
2. **Alias imports** 부분 지원 (`import x as y`)
3. **상대 import** 경로 해석 개선 필요

### 향후 계획
1. ✅ referenced_by (완료)
2. ✅ subclasses (완료)
3. ✅ dependencies (완료)
4. ✅ dependents (완료)
5. 🔄 Call graph 생성
6. 🔄 의존성 그래프 시각화
7. 🔄 순환 의존성 자동 감지 및 보고

---

## 🎉 결론

크로스 파일 분석 기능으로:
- ✅ 코드 간 관계 파악 가능
- ✅ 리팩토링 안전성 향상
- ✅ 프로젝트 구조 이해 개선
- ✅ 코드 품질 분석 도구로 활용 가능

모든 분석이 자동으로 수행되므로 **사용자는 신경 쓸 필요 없음**!

