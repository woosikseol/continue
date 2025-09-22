# Continue Python Core

원본 TypeScript Continue 프로젝트의 Python 포팅 버전입니다. Tree-sitter와 LSP를 사용하여 Java, JavaScript, Python 기반의 소스코드를 분석하고 자동완성을 제공합니다.

## 특징

- **원본과 동일한 구조**: TypeScript 원본과 동일한 디렉토리 구조와 기능
- **Tree-sitter 사용**: 원본과 동일한 Tree-sitter (C++ 기반, WebAssembly) 파서 직접 사용
- **LSP 지원**: Language Server Protocol을 통한 정확한 의미론적 분석
- **다중 언어 지원**: Java, JavaScript, TypeScript, Python, C++, Go, Rust 등
- **AST 분석**: 코드의 구문적 구조를 트리 형태로 표현하여 정확한 분석

## AST 구문적 구조 분석

이 프로젝트는 AST(Abstract Syntax Tree)를 사용하여 코드의 구문적 구조를 분석합니다:

- **구문적 구조**: 코드의 형태적, 문법적 구조를 분석
- **트리 형태**: 계층적, 중첩적 구조를 트리로 표현
- **노드와 엣지**: 각 코드 요소를 노드로, 관계를 엣지로 표현
- **계층적 관계**: 포함 관계와 형제 관계로 구조 표현
- **구조적 탐색**: 트리 순회로 전체 코드 구조 분석

## 설치

### 요구사항

- Python 3.12 (venv 사용 권장)
- tree-sitter 0.22.x

### 설치 방법

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# Tree-sitter 언어 파서 설치 (선택사항)
# 각 언어별 파서를 vendor/ 디렉토리에 설치
# 예: git clone https://github.com/tree-sitter/tree-sitter-python vendor/tree-sitter-python
```

### 최소 설치 (핵심 기능만)

```bash
# Tree-sitter만 설치 (핵심 기능)
pip install tree-sitter

# 또는 최소 requirements.txt 사용
pip install tree-sitter>=0.25.0
```

### 자동 설치 스크립트

```bash
# 자동 설치 스크립트 실행
python install.py
```

## 사용법

### 기본 파일 분석

```bash
# 파일 분석
python analyze_file.py test_example.py

# 결과를 파일로 저장
python analyze_file.py test_example.py result.json
```

### Python 모듈로 사용

```python
import asyncio
from python.core import Core, CoreConfig
from python.types import Position

async def main():
    # Core 초기화
    config = CoreConfig(
        workspace_paths=["/path/to/workspace"],
        enable_tree_sitter=True,
        enable_lsp=True
    )
    core = Core(config)
    await core.initialize()
    
    # 파일 분석
    result = await core.analyze_file("test.py")
    print(f"AST 노드 수: {result['tree_sitter']['node_count']}")
    print(f"최대 깊이: {result['tree_sitter']['max_depth']}")
    
    # 자동완성
    position = Position(line=10, character=5)
    completions = await core.get_completions("test.py", position)
    for completion in completions:
        print(f"완성: {completion['label']}")
    
    # 종료
    await core.shutdown()

asyncio.run(main())
```

## 프로젝트 구조

```
python/
├── __init__.py                 # 메인 모듈
├── core.py                    # 핵심 Core 클래스
├── types.py                   # 타입 정의
├── analyze_file.py            # 메인 분석 스크립트
├── requirements.txt           # 의존성
├── README.md                  # 이 파일
├── autocomplete/              # 자동완성 시스템
│   ├── __init__.py
│   └── completion_provider.py
├── config/                    # 설정 관리
│   ├── __init__.py
│   └── config_handler.py
├── context/                   # 컨텍스트 제공자
│   ├── __init__.py
│   └── providers.py
├── indexing/                  # 인덱싱 시스템
│   ├── __init__.py
│   └── codebase_indexer.py
├── llm/                       # LLM 제공자
│   ├── __init__.py
│   └── llm_provider.py
└── util/                      # 유틸리티
    ├── __init__.py
    ├── tree_sitter_service.py # Tree-sitter 서비스
    └── lsp_service.py         # LSP 서비스
```

## 지원 언어

- **Python** (.py, .pyw, .pyi)
- **JavaScript** (.js, .jsx, .mjs, .cjs)
- **TypeScript** (.ts, .tsx, .mts, .cts)
- **Java** (.java)
- **C++** (.cpp, .hpp, .cc, .cxx, .hxx, .cp, .hh, .inc)
- **C** (.c, .h)
- **Go** (.go)
- **Rust** (.rs)
- **그 외 다수 언어 지원**

## 원본과의 차이점

이 Python 포팅은 원본 TypeScript Continue 프로젝트와 다음과 같은 차이점이 있습니다:

1. **언어**: TypeScript → Python
2. **런타임**: Node.js → Python 3.12
3. **패키지 관리**: npm → pip
4. **타입 시스템**: TypeScript → Python typing

하지만 핵심 기능과 구조는 원본과 동일하게 유지됩니다:

- Tree-sitter 파서 사용
- LSP 프로토콜 지원
- AST 기반 코드 분석
- 자동완성 시스템
- 컨텍스트 제공

## 개발

### 테스트

```bash
# 기본 테스트
python analyze_file.py test_example.py

# 여러 파일 테스트
python analyze_file.py *.py
```

### 디버깅

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 라이선스

원본 Continue 프로젝트와 동일한 라이선스를 따릅니다.

## 기여

이 프로젝트는 원본 TypeScript Continue 프로젝트의 Python 포팅입니다. 기여 시 원본의 구조와 기능을 유지해주세요.