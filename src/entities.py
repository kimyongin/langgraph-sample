"""
공통 타입 정의 모듈

이 모듈은 애플리케이션 전반에서 사용되는 공통 타입을 정의합니다.
순환 참조를 방지하기 위해 타입 정의를 중앙화합니다.
"""

from typing import Dict, List, Optional, Any, TypedDict, Union, Literal


class TargetItem(TypedDict):
    """수집 대상 항목 타입"""
    name: str  # 항목 이름
    description: str  # 항목 설명
    required: bool  # 필수 여부
    example: Any  # 예시 데이터
    id: Optional[str]  # 항목 ID


class Target(TypedDict):
    """타겟 컨테이너 타입"""
    __root__: Dict[str, TargetItem]  # 대상 항목 매핑 (ID → 항목 정보)


class State(TypedDict):
    """LangGraph 워크플로우의 상태를 정의하는 타입"""
    messages: List[Dict[str, Any]]  # 채팅 기록
    node_result: str  # 현재 노드의 실행 결과 (문자열 상수)
    model_name: str  # Ollama 모델 이름
    temperature: float  # 생성 온도 파라미터
    results: Dict[str, Any]  # 수집된 결과 (대상 id를 키로 사용)
    current_target: Optional[TargetItem]  # 현재 처리 중인 대상


# 노드 결과 상수 정의
# find_missing.py 결과 상수
RESULT_TARGET_FOUND = "target_found"
RESULT_ALL_TARGETS_COMPLETE = "all_targets_complete"
RESULT_ERROR = "error"

# generate_question.py 결과 상수
RESULT_QUESTION_GENERATED = "question_generated"

# process_answer.py 결과 상수
RESULT_ANSWER_SUFFICIENT = "answer_sufficient"
RESULT_ANSWER_INSUFFICIENT = "answer_insufficient"