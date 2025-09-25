# Continue Python AST 분석 기능 문서

## 개요

Continue 프로젝트의 Python 포팅 버전에서 구현된 AST(Abstract Syntax Tree) 분석 기능에 대한 상세 문서입니다. 이 기능은 요청하신 모든 단계를 포함하여 코드의 구문적 구조를 트리 형태로 분석하고 구조적 메트릭을 계산합니다.

## 구현된 기능

### 1. AST 파싱 단계 (Parsing)

#### 1.1 Tree-sitter 파싱
- **기능**: 소스 코드를 AST로 변환
- **구현 위치**: `util/tree_sitter_service.py`
- **주요 메서드**: `get_ast()`, `get_parser_for_file()`
- **지원 언어**: Python, JavaScript, TypeScript, Java, C++, Go, Rust 등

```python
async def get_ast(self, filepath: str, contents: Optional[str] = None) -> Optional[Node]:
    """AST 생성 - 원본 getAst 함수 포팅"""
    # Tree-sitter를 사용하여 소스 코드를 AST로 파싱
    parser = self.get_parser_for_file(filepath)
    tree = parser.parse(bytes(contents, 'utf8'))
    return tree.root_node
```

#### 1.2 언어별 파서 활용
- **Python**: `tree-sitter-python` 파서 사용
- **JavaScript**: `tree-sitter-javascript` 파서 사용  
- **TypeScript**: `tree-sitter-typescript` 파서 사용
- **Java**: `tree-sitter-java` 파서 사용

#### 1.3 에러 처리
- 파싱 실패 시 부분적 AST 생성
- 언어별 파서 로드 실패 시 기본 파서 사용
- 예외 처리 및 로깅

### 2. AST 노드 추출 (Node Extraction)

#### 2.1 루트 노드 식별
- **기능**: 모듈/파일의 최상위 노드 식별
- **구현**: `extract_ast_metadata()` 메서드
- **메타데이터**: 타입, 텍스트, 위치 정보, 자식 수

```python
def extract_ast_metadata(self, node: Node, filepath: str) -> Dict[str, Any]:
    """1.2 AST 노드 추출 및 메타데이터 수집"""
    metadata = {
        'root_node': {
            'type': node.type,
            'text': node.text.decode('utf8')[:200] + "...",
            'start_position': [node.start_point[0], node.start_point[1]],
            'end_position': [node.end_point[0], node.end_point[1]],
            'children_count': len(node.children),
            'byte_range': [node.start_byte, node.end_byte]
        }
    }
```

#### 2.2 자식 노드 순회
- **기능**: 재귀적으로 모든 하위 노드 탐색
- **구현**: `_extract_all_nodes()` 메서드
- **특징**: 깊이 우선 탐색, 경로 추적

#### 2.3 노드 메타데이터
각 노드에 대해 다음 정보를 추출:
- **타입**: 노드의 구문 타입
- **텍스트**: 노드의 원본 텍스트
- **위치**: 시작/끝 위치 (라인, 컬럼)
- **바이트 범위**: 시작/끝 바이트 인덱스
- **깊이**: 트리에서의 중첩 깊이
- **경로**: 루트부터 노드까지의 경로
- **부모-자식 관계**: 계층적 관계 정보

### 3. 트리 구조 구성 (Tree Structure Building)

#### 3.1 계층적 구조
- **기능**: 부모-자식 관계 설정
- **구현**: `_build_hierarchical_structure()` 메서드
- **특징**: 중첩된 JSON 구조로 트리 표현

```python
def _build_hierarchical_structure(self, node: Node) -> Dict[str, Any]:
    """계층적 구조 구성"""
    structure = {
        'type': current_node.type,
        'depth': depth,
        'children': [],
        'metadata': {
            'start_position': [current_node.start_point[0], current_node.start_point[1]],
            'end_position': [current_node.end_point[0], current_node.end_point[1]],
            'text_preview': current_node.text.decode('utf8')[:50] + "..."
        }
    }
```

#### 3.2 깊이 계산
- **기능**: 각 노드의 중첩 깊이 계산
- **구현**: `_analyze_depths()` 메서드
- **통계**: 최대/최소 깊이, 깊이별 노드 분포

#### 3.3 경로 추적
- **기능**: 루트부터 각 노드까지의 경로 기록
- **구현**: `_track_paths()` 메서드
- **특징**: 리프 노드까지의 전체 경로 추적

### 4. 구조적 메트릭 계산 (Structural Metrics)

#### 4.1 기본 메트릭
- **노드 수**: 총 AST 노드 개수
- **최대 깊이**: 가장 깊은 중첩 레벨
- **노드 타입 분포**: 타입별 노드 개수

#### 4.2 복잡도 메트릭
- **Cyclomatic Complexity**: 순환 복잡도 계산
- **평균 자식 수**: 노드당 평균 자식 수
- **리프 노드 비율**: 리프 노드의 비율
- **분기 인수**: 트리의 분기 특성

```python
def get_structural_metrics(self, node: Node) -> Dict[str, Any]:
    """구조적 메트릭 계산 - 요청하신 모든 단계 구현"""
    structural_metrics = {
        'total_nodes': total_nodes,
        'max_depth': max_depth,
        'node_types': node_types,
        'complexity': complexity,
        'average_children_per_node': self._calculate_average_children(node),
        'leaf_node_ratio': self._calculate_leaf_node_ratio(node),
        'branching_factor': self._calculate_branching_factor(node)
    }
```

## 사용 방법

### 1. 단일 파일 분석

```python
from analyze_file import FileAnalyzer

# 분석기 초기화
analyzer = FileAnalyzer()
await analyzer.initialize()

# 파일 분석
result = await analyzer.analyze_file("example.py")

# 결과 확인
print(f"총 노드 수: {result.analysis['total_nodes']}")
print(f"최대 깊이: {result.analysis['max_depth']}")
print(f"복잡도: {result.analysis['structural_metrics']['complexity']}")
```

### 2. 프로젝트 전체 분석

```python
from analyze_project import ProjectAnalyzer

# 프로젝트 분석기 초기화
analyzer = ProjectAnalyzer("/path/to/project")
await analyzer.initialize()

# 프로젝트 전체 분석
result = await analyzer.analyze_project()

# 결과 확인
print(f"총 파일 수: {result.total_files}")
print(f"언어 분포: {result.language_distribution}")
print(f"프로젝트 메트릭: {result.project_metrics}")
```

### 3. 명령줄 사용

```bash
# 단일 파일 분석
python analyze_file.py example.py result.json

# 프로젝트 전체 분석
python analyze_project.py /path/to/project project_analysis.json
```

## 지원 언어

### 주요 언어 (요청하신 언어들)
- **Python** (.py, .pyw, .pyi)
- **JavaScript** (.js, .jsx, .mjs, .cjs)
- **TypeScript** (.ts, .tsx, .mts, .cts)
- **Java** (.java)

### 추가 지원 언어
- **C/C++** (.c, .h, .cpp, .hpp)
- **Go** (.go)
- **Rust** (.rs)
- **C#** (.cs)
- **PHP** (.php)
- **Ruby** (.rb)
- **Lua** (.lua)
- **HTML** (.html)
- **CSS** (.css)
- **JSON** (.json)

## 출력 형식

### 단일 파일 분석 결과

```json
{
  "filepath": "example.py",
  "language": "python",
  "ast_root": {
    "type": "module",
    "text": "#!/usr/bin/env python3...",
    "start_position": [0, 0],
    "end_position": [148, 23],
    "children_count": 20
  },
  "symbols": [
    {
      "filepath": "example.py",
      "type": "function_definition",
      "name": "main",
      "range": {
        "start": {"line": 10, "character": 0},
        "end": {"line": 20, "character": 0}
      },
      "content": "def main():\n    pass"
    }
  ],
  "analysis": {
    "total_nodes": 1124,
    "max_depth": 19,
    "node_types": {
      "module": 1,
      "function_definition": 4,
      "identifier": 202
    },
    "structural_metrics": {
      "total_nodes": 1124,
      "max_depth": 19,
      "complexity": 8,
      "average_children_per_node": 2.3,
      "leaf_node_ratio": 0.65,
      "branching_factor": 1.2
    },
    "ast_metadata": {
      "root_node": {...},
      "node_extraction": [...],
      "tree_structure": {...}
    }
  }
}
```

### 프로젝트 분석 결과

```json
{
  "project_path": "/path/to/project",
  "total_files": 150,
  "successful_analyses": 145,
  "failed_analyses": 5,
  "analysis_results": [...],
  "project_metrics": {
    "total_nodes": 45000,
    "max_depth": 25,
    "average_nodes_per_file": 300,
    "total_node_types": 45,
    "most_common_node_types": {
      "identifier": 15000,
      "expression_statement": 8000
    },
    "complexity_stats": {
      "average": 12.5,
      "max": 45,
      "min": 1
    }
  },
  "language_distribution": {
    "python": 80,
    "javascript": 40,
    "typescript": 20,
    "java": 10
  },
  "structural_summary": {
    "files_with_structural_metrics": 145,
    "average_metrics": {
      "average_complexity": 12.5,
      "average_leaf_node_ratio": 0.65
    },
    "complexity_distribution": {
      "low": 50,
      "medium": 70,
      "high": 20,
      "very_high": 5
    }
  }
}
```

## 아키텍처

### 핵심 컴포넌트

1. **TreeSitterService** (`util/tree_sitter_service.py`)
   - Tree-sitter 파서 관리
   - AST 생성 및 분석
   - 구조적 메트릭 계산

2. **FileAnalyzer** (`analyze_file.py`)
   - 단일 파일 분석
   - 언어 감지
   - 결과 통합

3. **ProjectAnalyzer** (`analyze_project.py`)
   - 프로젝트 전체 분석
   - 다중 파일 처리
   - 통계 계산

4. **Core** (`core.py`)
   - 전체 시스템 조율
   - 서비스 통합
   - 설정 관리

### 데이터 흐름

```
소스 코드 → Tree-sitter 파싱 → AST 생성 → 노드 추출 → 구조 분석 → 메트릭 계산 → 결과 출력
```

## 성능 고려사항

### 최적화 기법
- **언어별 파서 캐싱**: 파서 재사용으로 성능 향상
- **병렬 처리**: 다중 파일 분석 시 비동기 처리
- **메모리 관리**: 대용량 파일 처리 시 메모리 효율성
- **에러 복구**: 파싱 실패 시 부분적 결과 제공

### 확장성
- **플러그인 아키텍처**: 새로운 언어 파서 추가 용이
- **모듈화**: 각 기능별 독립적 모듈
- **설정 기반**: 사용자 정의 분석 옵션

## 결론

이 AST 분석 기능은 Continue 프로젝트의 Python 포팅으로, 요청하신 모든 단계를 구현했습니다:

1. ✅ **AST 파싱**: Tree-sitter를 사용한 다중 언어 지원
2. ✅ **노드 추출**: 완전한 메타데이터 수집
3. ✅ **트리 구조**: 계층적 관계 및 경로 추적
4. ✅ **구조적 메트릭**: 복잡도 및 통계 계산

이 기능을 통해 코드의 구조적 특성을 정량적으로 분석하고, 코드 품질 평가 및 리팩토링 가이드라인을 제공할 수 있습니다.
