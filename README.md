# 데이터 수집 에이전트 (Data Collector)

이 프로젝트는 LangGraph를 활용한 대화형 데이터 수집 에이전트입니다. 사용자와의 대화를 통해 특정 정보를 수집하고 구조화된 형태로 저장합니다.

## 기능 개요

- **대화형 인터페이스**: Streamlit을 활용한 직관적인 웹 인터페이스
- **LLM 활용**: Ollama를 통한 로컬 LLM 모델 사용
- **상태 관리**: LangGraph를 통한 대화 흐름 제어 및 상태 관리
- **유연한 데이터 수집**: 다양한 유형의 데이터를 수집 가능
- **모듈형 설계**: 상태, 에이전트, 데이터 처리 로직이 명확히 분리된 구조

## 흐름 요약

애플리케이션의 전체 대화 흐름 시퀀스는 다음과 같습니다:

1. **사용자 입력 처리 (app.py)**
   - Streamlit 인터페이스를 통해 사용자 메시지 입력 받음
   - `Agent.add_user_message()` 호출하여 처리 시작
   - 응답 받은 후 UI에 메시지 표시

2. **에이전트 내부 처리 (agent.py)**
   - 메시지 처리 시작 시 처리 지점(Entry Point) 결정:
     - 대화 시작: `find_missing` 노드로 시작
     - 사용자 메시지 수신: `process_answer` 노드로 시작
   - StateGraph를 통한 노드 간 흐름 제어

3. **노드 처리 시퀀스 (agent.py 내부 흐름)**
   - **find_missing** 노드:
     - 수집되지 않은 데이터 항목 확인
     - 모든 데이터 수집 완료 시 → 종료(`END`)
     - 미수집 데이터 발견 시 → `generate_question` 노드로 이동
   
   - **generate_question** 노드:
     - 미수집 데이터를 수집하기 위한 질문 생성
     - 질문 생성 후 종료(`END`)하고 사용자 응답 대기
   
   - **process_answer** 노드:
     - 사용자 응답 처리 및 데이터 추출
     - 응답이 충분한 정보 포함 시 → `find_missing` 노드로 이동
     - 응답이 불충분할 경우 → 종료(`END`)하고 다음 사용자 입력 대기

4. **처리 결과 관리**
   - 상태 변경사항 저장 및 메시지 업데이트
   - 모든 데이터 수집 완료 시 요약 메시지 생성

이 흐름은 사용자와 에이전트 간의 자연스러운 대화를 통해 필요한 모든 데이터가 수집될 때까지 반복됩니다.

## 프로젝트 구조

```
.
├── src/                    # 소스 코드
│   ├── nodes/              # LangGraph 노드 함수
│   │   ├── find_missing.py   # 누락된 데이터 찾기
│   │   ├── generate_question.py # 질문 생성
│   │   ├── process_answer.py # 답변 처리
│   │   └── __init__.py
│   ├── utils/              # 유틸리티 함수
│   │   ├── convert.py      # 데이터 변환
│   │   ├── decorator.py    # 함수 데코레이터
│   │   ├── model.py        # 모델 관련 유틸리티
│   │   ├── paths.py        # 경로 관리
│   │   └── __init__.py
│   ├── agent.py            # LangGraph 에이전트 구현
│   ├── app.py              # Streamlit 애플리케이션
│   ├── entities.py         # 공통 타입 및 상수 정의
│   ├── state.py            # 상태 관리
│   ├── target.py           # 수집 대상 정의 및 관리
│   └── __init__.py
├── resources/              # 정적 리소스
│   └── data/               # 데이터 파일
│       ├── target.json     # 수집 대상 정의
│       └── state.json      # 상태 저장 파일
├── tests/                  # 테스트 코드
├── run.py                  # 애플리케이션 실행 스크립트
├── setup.py                # 설치 스크립트
├── pyproject.toml          # 프로젝트 설정
└── requirements.txt        # 의존성 목록
```

## 아키텍처

### 핵심 모듈

1. **entities.py**
   - 공통 타입 정의 (State, TargetItem, Target)
   - 노드 결과 상수 정의 
   - 모듈 간 순환 참조 문제 해결을 위한 중앙 타입 모듈

2. **state.py**
   - 상태 관리 로직
   - StateManager 클래스를 통한 상태 접근 및 수정 기능 제공
   - 내부 상태 저장 및 로드 함수

3. **agent.py**
   - LangGraph 워크플로우 구성
   - 대화 로직 관리
   - 사용자 메시지 처리 및 응답 생성

4. **target.py**
   - 수집 대상 정의 및 관리
   - 목표 데이터 구조 정의
   - 완료되지 않은 항목 식별

### LangGraph 노드

이 애플리케이션은 LangGraph를 사용하여 다음과 같은 노드로 구성된 워크플로우를 실행합니다:

1. **find_missing**: 아직 수집되지 않은 데이터 항목을 식별
2. **generate_question**: 누락된 데이터를 수집하기 위한 질문 생성
3. **process_answer**: 사용자의 응답을 처리하고 데이터 추출

### Streamlit 인터페이스

- 사용자 친화적인 채팅 인터페이스
- 실시간 응답 및 데이터 수집 상태 표시
- 다양한 Ollama 모델 선택 지원

## 설계 패턴

### 캡슐화

- **StateManager**: 단일 접근 지점을 통한 상태 관리
- **내부 함수**: `_load_state`, `_save_state`와 같은 내부 함수로 구현 세부 사항 숨김

### 불변성

- **데코레이터**: `node_immutable` 데코레이터를 통한 상태 불변성 보장
- **직접 상태 수정**: 노드 함수 내에서 안전하게 상태 수정

### 모듈화

- **중앙 타입 정의**: `entities.py`에서 모든 타입과 상수 정의
- **순환 참조 제거**: 타입 중앙화를 통한 순환 참조 문제 해결

## 설치 및 실행

### 요구사항

- Python 3.10 이상
- Ollama 설치 (https://ollama.ai/)

### 설치 방법

```bash
# 가상 환경 생성 및 활성화 (권장)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 또는
.venv\Scripts\activate     # Windows

# 개발자 모드로 패키지 설치
python -m pip install -e .

# 또는 의존성만 설치
pip install -r requirements.txt
```

### 필수 라이브러리

```
streamlit>=1.45.0
langchain>=0.3.0
langchain-core>=0.3.0
langchain-community>=0.3.0
langgraph>=0.4.0
ollama>=0.4.0
langsmith>=0.3.0
pytest>=7.0.0
```

### Ollama 모델 설치

```bash
# Ollama 설치 후 필요한 모델 다운로드
ollama pull llama3  # 기본 모델
# 또는 다른 모델 선택 가능
# ollama pull mistral
# ollama pull gemma
```

### 애플리케이션 실행

```bash
python run.py
```

또는 직접 Streamlit 실행:

```bash
streamlit run src/app.py
```

### 폴더 구조 설정

애플리케이션을 처음 실행하기 전에 다음 폴더 구조가 필요합니다:

```bash
mkdir -p resources/data
```

그리고 `resources/data/target.json` 파일을 생성해야 합니다:

```json
{
  "project_overview": {
    "name": "Project Overview",
    "description": "Main purpose and description of the project",
    "required": true,
    "example": ["AI agent that collects information through conversations with users.", "AI agent that derives insights through conversations with users."]
  },
  "target_audience": {
    "name": "Target Users",
    "description": "Main user segment for the project",
    "required": true,
    "example": ["Researchers", "Developers"]
  },
  "tech_stack": {
    "name": "Tech Stack",
    "description": "Main technologies and libraries used",
    "required": true,
    "example": ["Streamlit", "Python", "LangChain"]
  },
  "features": {
    "name": "Main Features",
    "description": "List of main application features",
    "required": true,
    "example": [
      {
        "name": "Interactive Data Collection",
        "description": "Information collection through natural conversation"
      },
      {
        "name": "JSON Format Storage",
        "description": "Store collected data in structured format"
      }
    ]
  }
}
```

## 개발 가이드

### 새로운 노드 추가

1. `src/nodes/` 디렉토리에 새로운 노드 함수 구현
2. `src/agent.py`에 노드 등록 및 워크플로우 연결
3. 항상 `@node` 데코레이터 사용하여 불변성 및 로깅 보장

### 테스트 실행

```bash
pytest
```

## 라이선스

MIT

## 참고 자료

- [LangGraph 문서](https://github.com/langchain-ai/langgraph)
- [Streamlit 문서](https://docs.streamlit.io/)
- [Ollama 문서](https://ollama.ai/)