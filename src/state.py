"""
LangGraph 워크플로우의 상태를 정의하는 모듈입니다.
"""

import json
import os
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Literal, Optional, Union, Any, Tuple, cast
from copy import deepcopy

from src.utils.paths import get_project_paths
from src.entities import State, TargetItem

logger = logging.getLogger(__name__)

# 메모리 캐시를 위한 전역 변수
_STATE_CACHE: Optional[State] = None
_STATE_HASH: Optional[str] = None

def _calculate_state_hash(state: State) -> str:
    """
    상태 객체의 해시 값을 계산하여 변경 여부를 확인하는데 사용합니다.
    """
    # JSON 문자열로 변환하고 해시 계산
    state_json = json.dumps(state, sort_keys=True)
    return hashlib.md5(state_json.encode('utf-8')).hexdigest()

def _save_state(state: State) -> bool:
    """
    (내부 함수) 상태 데이터를 state.json 파일에 저장합니다.
    상태가 변경된 경우에만 파일에 씁니다.
    """
    global _STATE_CACHE, _STATE_HASH
    
    # 현재 상태의 해시 계산
    current_hash = _calculate_state_hash(state)
    
    # 해시가 이전과 동일하면 저장하지 않음 (변경 없음)
    if _STATE_HASH == current_hash:
        logger.debug("상태가 변경되지 않았습니다. 파일 쓰기를 건너뜁니다.")
        return True
    
    paths = get_project_paths()
    state_file = paths["state_file"]
    
    try:
        # 디렉토리가 없는 경우 생성
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # State 객체를 JSON으로 직렬화 가능한 사전으로 변환
        serializable_state = dict(state)
        
        # 파일에 저장
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(serializable_state, f, ensure_ascii=False, indent=2)
        
        # 메모리 캐시 업데이트
        _STATE_CACHE = deepcopy(state)
        _STATE_HASH = current_hash
        
        logger.info(f"state.json 파일을 성공적으로 저장했습니다: {state_file}")
        return True
    
    except Exception as e:
        logger.error(f"state.json 파일 저장 중 오류 발생: {str(e)}")
        return False


def _load_state() -> State:
    """
    (내부 함수) state.json 파일을 로드하여 저장된 상태 데이터를 반환합니다.
    캐시된 상태가 있으면 파일을 다시 읽지 않고 캐시된 상태를 반환합니다.
    파일이 없는 경우 빈 상태 객체를 반환합니다.
    """
    global _STATE_CACHE, _STATE_HASH
    
    # 캐시된 상태가 있으면 반환
    if _STATE_CACHE is not None:
        logger.debug("캐시된 상태를 반환합니다.")
        return deepcopy(_STATE_CACHE)  # 원본 보존을 위해 깊은 복사 사용
    
    paths = get_project_paths()
    state_file = paths["state_file"]
    
    # 기본 상태 객체 생성
    default_state: State = {
        "messages": [],
        "node_result": "",
        "model_name": "llama3",
        "temperature": 0.7,
        "results": {},
        "current_target": None
    }
    
    if not state_file.exists():
        logger.info(f"state.json 파일이 없습니다. 필요 시 새로 생성될 예정입니다: {state_file}")
        _STATE_CACHE = deepcopy(default_state)
        _STATE_HASH = _calculate_state_hash(default_state)
        return deepcopy(default_state)
    
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state_data = json.load(f)
        
        # JSON 데이터를 State 타입으로 캐스팅
        state: State = cast(State, state_data)
        
        # 결과가 없으면 빈 사전 초기화
        if "results" not in state:
            state["results"] = {}
            
        # 필수 필드가 있는지 확인하고 없으면 기본값 설정
        for key in default_state:
            if key not in state:
                state[key] = default_state[key]
                
        logger.info(f"state.json 파일을 성공적으로 로드했습니다.")
        
        # 메모리 캐시 업데이트
        _STATE_CACHE = deepcopy(state)
        _STATE_HASH = _calculate_state_hash(state)
        
        return deepcopy(state)
    
    except json.JSONDecodeError as e:
        logger.error(f"state.json 파일 파싱 중 오류 발생: {str(e)}")
        # 파싱 오류 시 기본 상태 객체 반환
        _STATE_CACHE = deepcopy(default_state)
        _STATE_HASH = _calculate_state_hash(default_state)
        return deepcopy(default_state)
    except Exception as e:
        logger.error(f"state.json 파일 로드 중 오류 발생: {str(e)}")
        _STATE_CACHE = deepcopy(default_state)
        _STATE_HASH = _calculate_state_hash(default_state)
        return deepcopy(default_state)


def _invalidate_cache() -> None:
    """
    (내부 함수) 캐시를 무효화하여 다음 로드 시 파일에서 다시 읽도록 합니다.
    외부 프로세스에서 파일이 변경된 경우에 사용할 수 있습니다.
    """
    global _STATE_CACHE, _STATE_HASH
    _STATE_CACHE = None
    _STATE_HASH = None
    logger.debug("상태 캐시가 무효화되었습니다.")


def _reset_state() -> bool:
    """
    (내부 함수) 상태를 완전히 초기화합니다.
    - state.json 파일 삭제
    - 메모리 캐시 초기화
    """
    global _STATE_CACHE, _STATE_HASH
    
    paths = get_project_paths()
    state_file = paths["state_file"]
    
    try:
        # 파일이 존재하면 삭제
        if state_file.exists():
            state_file.unlink()
            logger.info(f"state.json 파일을 성공적으로 삭제했습니다: {state_file}")
        
        # 기본 상태 객체 생성
        default_state: State = {
            "messages": [],
            "node_result": "",
            "model_name": "llama3",
            "temperature": 0.7,
            "results": {},
            "current_target": None
        }
        
        # 메모리 캐시 초기화
        _STATE_CACHE = deepcopy(default_state)
        _STATE_HASH = _calculate_state_hash(default_state)
        
        return True
    
    except Exception as e:
        logger.error(f"상태 초기화 중 오류 발생: {str(e)}")
        return False


class StateManager:
    """상태 관리를 위한 유틸리티 클래스"""
    
    @staticmethod
    def get_messages() -> List[Dict]:
        """상태에서 메시지를 가져옵니다."""
        state = _load_state()
        return state.get("messages", [])
    
    @staticmethod
    def get_results() -> Dict:
        """상태에서 결과를 가져옵니다."""
        state = _load_state()
        return state.get("results", {})
    
    @staticmethod
    def get_node_result() -> str:
        """상태에서 노드 결과를 가져옵니다."""
        state = _load_state()
        return state.get("node_result", "")
    
    @staticmethod
    def get_current_target() -> Optional[TargetItem]:
        """상태에서 현재 대상을 가져옵니다."""
        state = _load_state()
        return state.get("current_target")
    
    @staticmethod
    def get_model_settings() -> Tuple[str, float]:
        """상태에서 모델 설정을 가져옵니다."""
        state = _load_state()
        return state.get("model_name", "llama3"), state.get("temperature", 0.7)
    
    @staticmethod
    def set_model_settings(model_name: str, temperature: float) -> None:
        """상태에 모델 설정을 업데이트합니다."""
        state = _load_state()
        state["model_name"] = model_name
        state["temperature"] = temperature
        _save_state(state)
    
    @staticmethod
    def append_message(message: Dict) -> List[Dict]:
        """상태에 메시지를 추가합니다."""
        state = _load_state()
        messages = state.get("messages", [])
        messages.append(message)
        state["messages"] = messages
        _save_state(state)
        return messages
    
    @staticmethod
    def update_state(state_update: Dict) -> State:
        """상태를 업데이트하고 저장합니다."""
        state = _load_state()
        state.update(state_update)
        _save_state(state)
        return state
    
    @staticmethod
    def load() -> State:
        """상태를 로드합니다."""
        return _load_state()
    
    @staticmethod
    def save(state: State) -> bool:
        """상태를 저장합니다."""
        return _save_state(state)
    
    @staticmethod
    def invalidate_cache() -> None:
        """캐시를 무효화합니다. 파일이 외부에서 변경된 경우 호출하세요."""
        _invalidate_cache()
        
    @staticmethod
    def reset() -> bool:
        """
        상태를 완전히 초기화합니다.
        - state.json 파일 삭제
        - 메모리 캐시 초기화
        - 기본 상태로 재설정
        
        Returns:
            bool: 초기화 성공 여부
        """
        return _reset_state()