"""
데코레이터 유틸리티 모듈

이 모듈은 프로젝트에서 사용되는 함수 데코레이터를 제공합니다.
주로 LangGraph 노드 함수를 위한 불변성과 로깅 기능을 지원합니다.
"""

from typing import Any, Callable
from copy import deepcopy
import functools
import logging
import json
import inspect

from src.entities import State

# 로깅 설정
logger = logging.getLogger(__name__)


def node(func: Callable[[State], State]) -> Callable[[State], State]:
    """
    LangGraph 노드를 위한 통합 데코레이터
    immutable과 node_logger 데코레이터를 결합하여 제공합니다.
    이 데코레이터를 사용하면 노드 함수는 State 입력을 변경하지 않고,
    함수 호출 전후에 상태 정보가 로깅됩니다.
    """
    # 먼저 immutable 적용 후 node_logger 적용
    # 순서가 중요: immutable이 먼저 적용되어 상태를 복사한 후, node_logger가 로깅 수행
    return node_logger(node_immutable(func))


def node_immutable(func: Callable[[State], State]) -> Callable[[State], State]:
    """
    함수가 입력 상태를 변경하지 않도록 보장하는 데코레이터
    입력 상태의 깊은 복사본을 만들어 함수에 전달하고 결과를 반환합니다.
    """
    @functools.wraps(func)
    def wrapper(state: State, *args, **kwargs) -> State:
        # 입력 상태의 깊은 복사본 만들기
        state_copy = deepcopy(state)
        
        # 함수 실행 및 결과 반환
        return func(state_copy, *args, **kwargs)
    
    return wrapper


def node_logger(func: Callable[[State], State]) -> Callable[[State], State]:
    """
    LangGraph 노드 함수 호출과 반환값을 로깅하는 데코레이터
    각 노드의 입력과 출력 State를 요약하여 로깅합니다.
    """
    @functools.wraps(func)
    def wrapper(state: State, *args, **kwargs) -> State:
        func_name = func.__name__
        module_name = func.__module__

        # 노드 실행 시작 로깅
        logger.info(f"===== 노드 시작: {module_name}.{func_name} =====")
        
        # State 객체 요약
        if hasattr(state, "get"):
            messages_count = len(state.get("messages", []))
            current_target = state.get("current_target")
            current_target_id = current_target.get("id") if current_target else "None"
            results_count = len(state.get("results", {}))
            
            logger.info(f"입력: messages={messages_count}개, current_target={current_target_id}, results={results_count}개")
        
        # 함수 실행 (state는 원본 그대로 전달)
        result = func(state, *args, **kwargs)
        
        # 함수 반환값 로깅
        if hasattr(result, "get"):
            new_node_result = result.get("node_result")
            new_messages_count = len(result.get("messages", []))
            new_current_target = result.get("current_target")
            new_current_target_id = new_current_target.get("id") if new_current_target else "None"
            new_results_count = len(result.get("results", {}))
            
            logger.info(f"출력: node_result={new_node_result}, messages={new_messages_count}개, current_target={new_current_target_id}, results={new_results_count}개")
        
        logger.info(f"===== 노드 종료: {module_name}.{func_name} =====")
        
        return result
    
    return wrapper 