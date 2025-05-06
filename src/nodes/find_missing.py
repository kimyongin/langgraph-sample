from typing import Dict, Any, Tuple, Optional, List
from src.state import State
from src.target import TargetItem, Target, find_first_missing_target, get_targets
import logging
from src.utils.decorator import node
from src.entities import RESULT_TARGET_FOUND, RESULT_ALL_TARGETS_COMPLETE, RESULT_ERROR

logger = logging.getLogger(__name__)

@node
def find_missing(state: State) -> State:
    """외부에서 타겟이 제공되는 LangGraph 노드 함수"""
    # 타겟 모듈에서 타겟 가져오기
    targets = get_targets()
    return find_missing_with_targets(state, targets) 


def find_missing_with_targets(state: State, targets: Dict[str, TargetItem]) -> State:
    """상태와 타겟을 가지고 다음 처리할 항목을 찾는 함수"""
    try:        
        # 처리할 타겟 찾기
        targets_wrapped: Target = {"__root__": targets}
        results = state.get("results", {})        
        missing_target = find_first_missing_target(targets_wrapped, results)
        
        if missing_target:
            # 타겟을 찾았을 때
            target_id, target_item = missing_target
            logger.info(f"처리할 타겟을 찾았습니다: {target_id}")
            
            # 현재 타겟 설정 - id 포함
            target_copy = dict(target_item)
            target_copy["id"] = target_id
            
            # 직접 상태 업데이트
            state["current_target"] = target_copy
            state["node_result"] = RESULT_TARGET_FOUND
            return state
        else:
            # 모든 필수 타겟이 완료되었을 때
            logger.info("모든 필수 타겟이 완료되었습니다")
            
            # 직접 상태 업데이트
            state["current_target"] = None
            state["node_result"] = RESULT_ALL_TARGETS_COMPLETE
            return state
    
    except Exception as e:
        # 예외 처리 - 오류 정보 로깅
        logger.error(f"find_missing 노드에서 오류 발생: {str(e)}")
        
        # 직접 상태 업데이트
        state["node_result"] = RESULT_ERROR
        state["error"] = str(e)
        return state


