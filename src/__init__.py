"""
데이터 수집 에이전트 패키지

이 패키지는 LangGraph를 사용한 대화형 데이터 수집 에이전트를 제공합니다.
"""

from src.entities import (
    State, TargetItem, Target,
    RESULT_TARGET_FOUND, RESULT_ALL_TARGETS_COMPLETE, RESULT_ERROR,
    RESULT_QUESTION_GENERATED, RESULT_ANSWER_SUFFICIENT, RESULT_ANSWER_INSUFFICIENT
)

from src.state import StateManager
from src.target import get_targets, find_first_missing_target
from src.agent import Agent

__all__ = [
    # Types
    "State", "TargetItem", "Target",
    
    # Constants
    "RESULT_TARGET_FOUND", "RESULT_ALL_TARGETS_COMPLETE", "RESULT_ERROR",
    "RESULT_QUESTION_GENERATED", "RESULT_ANSWER_SUFFICIENT", "RESULT_ANSWER_INSUFFICIENT",
    
    # Functions and classes
    "StateManager",
    "get_targets", "find_first_missing_target",
    "Agent"
]
