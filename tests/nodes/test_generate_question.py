import pytest
from unittest.mock import patch
from src.nodes.generate_question import generate_question, RESULT_QUESTION_GENERATED
from src.state import State


def test_generate_question_with_real_llm():
    """실제 LLM을 사용하여 질문 생성을 테스트합니다."""
    # Setup state
    state = State({
        "messages": [],
        "current_target": {
            "id": "test_target",
            "name": "Test Target",
            "description": "Test description",
            "example": "Test example"
        },
        "node_result": None,
        "model_name": "llama3",  # 사용 가능한 모델명으로 변경
        "temperature": 0.5
    })
    
    # Execute
    result = generate_question(state)
    
    # 콘솔에 LLM 응답 출력
    print("\n----- LLM 응답 내용 -----")
    print(result["messages"][0]["content"])
    print("-------------------------\n")
    
    # Verify
    assert result["node_result"] == RESULT_QUESTION_GENERATED
    assert len(result["messages"]) == 1
    assert result["messages"][0]["role"] == "ai"
    assert result["messages"][0]["content"] is not None  # 응답 내용이 있는지만 확인 