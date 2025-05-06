"""
수집 대상 항목을 정의하는 모듈입니다.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List, Iterator, Tuple, cast

from src.utils.paths import get_project_paths
from src.entities import TargetItem, Target

logger = logging.getLogger(__name__)

# 전역 변수로 targets 캐싱
_cached_targets: Optional[Dict[str, TargetItem]] = None


def get_targets() -> Dict[str, TargetItem]:
    """
    target.json 파일에서 타겟 항목들을 로드하고 캐싱하여 반환합니다.
    """
    global _cached_targets
    
    # 캐시된 값이 있으면 그대로 반환
    if _cached_targets is not None:
        return _cached_targets
    
    # 타겟 로드 및 캐싱
    target = load_target()
    _cached_targets = get_target_items(target)
    
    return _cached_targets


def load_target() -> Target:
    """
    target.json 파일을 로드하여 수집할 대상 항목들을 반환합니다.
    target.json은 필수 정적 리소스 파일입니다.
    """
    paths = get_project_paths()
    target_file = paths["target_file"]
    
    # target.json 파일이 없는 경우 오류 발생
    if not target_file.exists():
        raise FileNotFoundError(
            f"필수 target.json 파일이 없습니다: {target_file}\n"
            f"resources/data 폴더에 target.json 파일을 생성해주세요.\n"
            f"예시 형식:\n"
            f'{{"project_overview": {{"name": "프로젝트 개요", "description": "프로젝트의 주요 목적", "required": true, "example": "예시 데이터"}}}}'
        )
    
    try:
        # 파일 로드
        with open(target_file, "r", encoding="utf-8") as f:
            target_data = json.load(f)
        
        # 각 항목에 id 필드 추가
        target_items: Dict[str, TargetItem] = {}
        for target_id, item in target_data.items():
            # TypedDict에 맞게 데이터 변환
            target_item: TargetItem = {
                "name": item["name"],
                "description": item["description"],
                "required": item.get("required", True),
                "example": item["example"],
                "id": target_id
            }
            target_items[target_id] = target_item
            
        # Target 객체 생성
        target: Target = {"__root__": target_items}
        
        logger.info(f"target.json 파일을 성공적으로 로드했습니다. {len(target_items)}개 항목이 있습니다.")
        return target
    
    except json.JSONDecodeError as e:
        logger.error(f"target.json 파일 파싱 중 오류 발생: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"target.json 파일 로드 중 오류 발생: {str(e)}")
        raise


# Helper 함수들
def get_target_items(target: Target) -> Dict[str, TargetItem]:
    """대상 항목 사전 반환"""
    return target["__root__"]


def get_required_target_items(target: Target) -> Dict[str, TargetItem]:
    """필수 대상 항목만 반환"""
    items = get_target_items(target)
    return {
        target_id: item 
        for target_id, item in items.items() 
        if item.get("required", True)
    }


def get_missing_target_items(target: Target, results: Dict[str, Any]) -> Dict[str, TargetItem]:
    """아직 수집되지 않은 필수 대상 항목 반환"""
    required_items = get_required_target_items(target)
    return {
        target_id: item 
        for target_id, item in required_items.items() 
        if target_id not in results
    }


def find_first_missing_target(target: Target, results: Dict[str, Any]) -> Optional[Tuple[str, TargetItem]]:
    """아직 수집되지 않은 첫 번째 필수 대상 항목 찾기"""
    missing_items = get_missing_target_items(target, results)
    if not missing_items:
        return None
    
    # 첫 번째 항목 반환
    target_id = next(iter(missing_items))
    return target_id, missing_items[target_id] 