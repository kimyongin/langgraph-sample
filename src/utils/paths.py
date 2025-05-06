"""
프로젝트 경로 유틸리티 모듈
"""
import os
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

def get_project_paths() -> Dict[str, Path]:
    """
    프로젝트의 주요 경로들을 반환합니다.
    resources 폴더와 data 폴더는 필수적으로 존재해야 합니다.
    """
    # 현재 스크립트 위치 기준으로 경로 찾기
    current_file = Path(__file__)
    utils_dir = current_file.parent
    src_dir = utils_dir.parent
    project_root = src_dir.parent
    
    # 리소스 디렉토리 (정적 리소스 포함 디렉토리)
    resources_dir = project_root / "resources"
    data_dir = resources_dir / "data"
    
    # 필수 디렉토리 확인
    if not resources_dir.exists():
        raise FileNotFoundError(f"필수 리소스 디렉토리가 없습니다: {resources_dir}. 'resources' 폴더를 프로젝트 루트에 생성해주세요.")
    
    if not data_dir.exists():
        raise FileNotFoundError(f"필수 데이터 디렉토리가 없습니다: {data_dir}. 'resources/data' 폴더를 생성해주세요.")
    
    return {
        "utils_dir": utils_dir,
        "src_dir": src_dir,
        "project_root": project_root,
        "resources_dir": resources_dir,
        "data_dir": data_dir,
        "target_file": data_dir / "target.json",
        "state_file": data_dir / "state.json"
    } 