"""
LangGraph 워크플로우의 상태를 관리하는 모듈

이 모듈은 대화 에이전트의 상태를 관리하는 기능을 제공합니다:
1. 대화 메시지 저장 및 로드
2. 모델 설정 관리
3. 수집된 결과 데이터 관리
4. 상태 파일로의 영구 저장

상태는 메모리 내 캐싱과 파일 기반 영구 저장소를 통해 관리됩니다.
캐싱을 통해 파일 I/O를 최소화하고 성능을 향상시킵니다.
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

# === 메모리 캐싱 변수 ===
# 상태 객체의 메모리 내 캐시
_STATE_CACHE: Optional[State] = None
# 캐시된 상태의 해시값 (변경 여부 확인용)
_STATE_HASH: Optional[str] = None

def _calculate_state_hash(state: State) -> str:
    """
    상태 객체의 해시값을 계산합니다.
    
    이 해시값은 상태가 변경되었는지 확인하는 데 사용되며,
    변경이 없는 경우 파일 쓰기 작업을 건너뛰어 성능을 향상시킵니다.
    
    Args:
        state: 해시값을 계산할 상태 객체
        
    Returns:
        str: 상태 객체의 MD5 해시값
    """
    # 상태를 정렬된 JSON 문자열로 변환 후 해시 계산
    state_json = json.dumps(state, sort_keys=True)
    return hashlib.md5(state_json.encode('utf-8')).hexdigest()

def _save_state(state: State) -> bool:
    """
    상태 데이터를 state.json 파일에 저장합니다.
    
    성능 최적화를 위해 상태가 변경된 경우에만 파일에 씁니다.
    
    Args:
        state: 저장할 상태 객체
        
    Returns:
        bool: 저장 성공 여부
    """
    global _STATE_CACHE, _STATE_HASH
    
    # 현재 상태의 해시 계산
    current_hash = _calculate_state_hash(state)
    
    # 해시가 동일하면 (변경 없음) 저장 건너뛰기
    if _STATE_HASH == current_hash:
        logger.debug("상태가 변경되지 않았습니다. 파일 쓰기를 건너뜁니다.")
        return True
    
    # 프로젝트 경로 가져오기
    paths = get_project_paths()
    state_file = paths["state_file"]
    
    try:
        # 디렉토리가 없으면 생성
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # State 객체를 JSON으로 직렬화
        serializable_state = dict(state)
        
        # 파일에 저장
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(serializable_state, f, ensure_ascii=False, indent=2)
        
        # 메모리 캐시 업데이트
        _STATE_CACHE = deepcopy(state)
        _STATE_HASH = current_hash
        
        logger.info(f"상태 파일을 성공적으로 저장했습니다: {state_file}")
        return True
    
    except Exception as e:
        logger.error(f"상태 파일 저장 중 오류 발생: {str(e)}")
        return False


def _load_state() -> State:
    """
    state.json 파일에서 상태 데이터를 로드합니다.
    
    캐시된 상태가 있으면 파일을 다시 읽지 않고 캐시를 반환합니다.
    파일이 없는 경우 기본 상태 객체를 반환합니다.
    
    Returns:
        State: 로드된 상태 객체 또는 기본 상태
    """
    global _STATE_CACHE, _STATE_HASH
    
    # 캐시된 상태가 있으면 반환 (성능 최적화)
    if _STATE_CACHE is not None:
        logger.debug("캐시된 상태를 반환합니다.")
        return deepcopy(_STATE_CACHE)  # 원본 보존을 위해 깊은 복사 사용
    
    # 프로젝트 경로 가져오기
    paths = get_project_paths()
    state_file = paths["state_file"]
    
    # 기본 상태 객체 정의
    default_state: State = {
        "messages": [],      # 대화 메시지
        "node_result": "",   # 워크플로우 노드 결과
        "results": {},       # 수집된 데이터
        "current_target": None,  # 현재 타겟
        "model": None        # 모델 설정
    }
    
    # 상태 파일이 없으면 기본 상태 반환
    if not state_file.exists():
        logger.info(f"상태 파일이 없습니다. 필요시 새로 생성됩니다: {state_file}")
        _STATE_CACHE = deepcopy(default_state)
        _STATE_HASH = _calculate_state_hash(default_state)
        return deepcopy(default_state)
    
    try:
        # 파일에서 상태 데이터 로드
        with open(state_file, "r", encoding="utf-8") as f:
            state_data = json.load(f)
        
        # JSON 데이터를 State 타입으로 변환
        state: State = cast(State, state_data)
        
        # 필수 필드가 없으면 기본값으로 초기화
        if "results" not in state:
            state["results"] = {}
            
        for key in default_state:
            if key not in state:
                state[key] = default_state[key]
                
        logger.info(f"상태 파일을 성공적으로 로드했습니다")
        
        # 메모리 캐시 업데이트
        _STATE_CACHE = deepcopy(state)
        _STATE_HASH = _calculate_state_hash(state)
        
        return deepcopy(state)
    
    except json.JSONDecodeError as e:
        # JSON 파싱 오류 처리
        logger.error(f"상태 파일 파싱 중 오류 발생: {str(e)}")
        _STATE_CACHE = deepcopy(default_state)
        _STATE_HASH = _calculate_state_hash(default_state)
        return deepcopy(default_state)
    except Exception as e:
        # 기타 오류 처리
        logger.error(f"상태 파일 로드 중 오류 발생: {str(e)}")
        _STATE_CACHE = deepcopy(default_state)
        _STATE_HASH = _calculate_state_hash(default_state)
        return deepcopy(default_state)


def _invalidate_cache() -> None:
    """
    메모리 캐시를 무효화합니다.
    
    다음 _load_state() 호출 시 파일에서 상태를 다시 로드하도록 합니다.
    외부 프로세스에서 파일이 변경된 경우 사용합니다.
    """
    global _STATE_CACHE, _STATE_HASH
    _STATE_CACHE = None
    _STATE_HASH = None
    logger.debug("상태 캐시가 무효화되었습니다")


def _reset_state() -> bool:
    """
    상태를 완전히 초기화합니다.
    
    1. state.json 파일 삭제
    2. 메모리 캐시 초기화
    3. 기본 상태로 재설정
    
    Returns:
        bool: 초기화 성공 여부
    """
    global _STATE_CACHE, _STATE_HASH
    
    # 프로젝트 경로 가져오기
    paths = get_project_paths()
    state_file = paths["state_file"]
    
    try:
        # 파일이 존재하면 삭제
        if state_file.exists():
            state_file.unlink()
            logger.info(f"상태 파일을 삭제했습니다: {state_file}")
        
        # 기본 상태 객체 생성
        default_state: State = {
            "messages": [],
            "node_result": "",
            "results": {},
            "current_target": None,
            "model": None
        }
        
        # 메모리 캐시 초기화
        _STATE_CACHE = deepcopy(default_state)
        _STATE_HASH = _calculate_state_hash(default_state)
        
        return True
    
    except Exception as e:
        logger.error(f"상태 초기화 중 오류 발생: {str(e)}")
        return False


class StateManager:
    """
    상태 관리를 위한 유틸리티 클래스
    
    이 클래스는 애플리케이션의 다양한 부분에서 상태에 접근하고 수정하기 위한
    정적 메서드를 제공합니다. 내부적으로는 _load_state()와 _save_state() 함수를
    사용하여 상태의 일관성을 유지합니다.
    """
    
    @staticmethod
    def get_messages() -> List[Dict]:
        """
        상태에서 대화 메시지 목록을 가져옵니다.
        
        Returns:
            List[Dict]: 메시지 목록
        """
        state = _load_state()
        return state.get("messages", [])
    
    @staticmethod
    def get_results() -> Dict:
        """
        상태에서 수집된 결과 데이터를 가져옵니다.
        
        Returns:
            Dict: 수집된 결과 데이터
        """
        state = _load_state()
        return state.get("results", {})
    
    @staticmethod
    def get_node_result() -> str:
        """
        상태에서 워크플로우 노드 결과를 가져옵니다.
        
        Returns:
            str: 노드 결과 문자열
        """
        state = _load_state()
        return state.get("node_result", "")
    
    @staticmethod
    def get_current_target() -> Optional[TargetItem]:
        """
        상태에서 현재 처리 중인 타겟을 가져옵니다.
        
        Returns:
            Optional[TargetItem]: 현재 타겟 또는 None
        """
        state = _load_state()
        return state.get("current_target")
    
    @staticmethod
    def get_model_settings() -> Tuple[str, float, str, Optional[str]]:
        """
        상태에서 모델 설정을 가져옵니다.
        
        Returns:
            Tuple[str, float, str, Optional[str]]: 
                (모델 이름, 온도, 모델 유형, API 키)
        """
        state = _load_state()
        model = state.get("model")
        
        if model is None:
            # 모델이 선택되지 않은 경우 기본값 반환
            return "llama3", 0.7, "ollama", None
        
        return (
            model.get("name", "llama3"), 
            model.get("temperature", 0.7),
            model.get("type", "ollama"),
            model.get("api_key")
        )
    
    @staticmethod
    def set_model_settings(model_name: str, temperature: float, model_type: str = "ollama", api_key: Optional[str] = None) -> None:
        """
        상태에 모델 설정을 업데이트합니다.
        
        Args:
            model_name: 사용할 모델 이름
            temperature: 모델 온도 설정 (높을수록 무작위성 증가)
            model_type: 모델 유형 ("ollama" 또는 "openai")
            api_key: OpenAI 모델 사용 시 필요한 API 키
        """
        state = _load_state()
        
        # 새 모델 설정 생성
        state["model"] = {
            "name": model_name,
            "temperature": temperature,
            "type": model_type,
            "api_key": api_key
        }
        
        _save_state(state)
    
    @staticmethod
    def append_message(message: Dict) -> List[Dict]:
        """
        상태에 새 메시지를 추가합니다.
        
        Args:
            message: 추가할 메시지 객체
            
        Returns:
            List[Dict]: 업데이트된 메시지 목록
        """
        state = _load_state()
        messages = state.get("messages", [])
        messages.append(message)
        state["messages"] = messages
        _save_state(state)
        return messages
    
    @staticmethod
    def update_state(state_update: Dict) -> State:
        """
        상태를 업데이트하고 저장합니다.
        
        Args:
            state_update: 업데이트할 상태 필드
            
        Returns:
            State: 업데이트된 상태
        """
        state = _load_state()
        state.update(state_update)
        _save_state(state)
        return state
    
    @staticmethod
    def load() -> State:
        """
        현재 상태를 로드합니다.
        
        Returns:
            State: 현재 상태 객체
        """
        return _load_state()
    
    @staticmethod
    def save(state: State) -> bool:
        """
        제공된 상태를 저장합니다.
        
        Args:
            state: 저장할 상태 객체
            
        Returns:
            bool: 저장 성공 여부
        """
        return _save_state(state)
    
    @staticmethod
    def invalidate_cache() -> None:
        """
        캐시를 무효화합니다.
        
        외부에서 상태 파일이 변경된 경우 호출하세요.
        다음 로드 시 파일에서 다시 읽습니다.
        """
        _invalidate_cache()
        
    @staticmethod
    def reset() -> bool:
        """
        상태를 완전히 초기화합니다.
        
        모든 메시지, 결과 데이터, 모델 설정을 초기화합니다.
        
        Returns:
            bool: 초기화 성공 여부
        """
        return _reset_state()
    
    @staticmethod
    def is_model_selected() -> bool:
        """
        모델이 선택되었는지 확인합니다.
        
        Returns:
            bool: 모델이 선택되었으면 True, 아니면 False
        """
        state = _load_state()
        return state.get("model") is not None
    
    @staticmethod
    def set_model_selected(selected: bool) -> None:
        """
        모델 선택 상태를 설정합니다.
        
        Args:
            selected: 모델 선택 여부 (True/False)
        """
        state = _load_state()
        
        if not selected:
            # 모델 선택 해제
            state["model"] = None
        elif state.get("model") is None and selected:
            # 모델 선택 설정 (기본 모델)
            state["model"] = {
                "name": "llama3",
                "temperature": 0.7,
                "type": "ollama",
                "api_key": None
            }
        
        _save_state(state)