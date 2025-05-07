import pytest
from unittest.mock import patch, MagicMock
from src.nodes.find_missing import find_missing, RESULT_TARGET_FOUND, RESULT_ALL_TARGETS_COMPLETE
from src.state import State


@patch('src.nodes.find_missing.get_targets')
def test_find_missing_required_target(mock_get_targets):
    """필수 타겟 중 하나가 누락된 경우를 테스트합니다."""
    # get_targets 함수를 모의하여 테스트 타겟 데이터 반환
    mock_get_targets.return_value = {
        "target1": {"required": True, "name": "Target 1", "description": "Test 1", "example": "Example 1"},
        "target2": {"required": True, "name": "Target 2", "description": "Test 2", "example": "Example 2"}
    }
    
    # Setup state with a required target not in results
    state = State({
        "results": {
            "target2": "some result"
        },
        "current_target": None,
        "node_result": None
    })
    
    # Execute
    result = find_missing(state)
    
    # Verify
    assert result["current_target"]["id"] == "target1"
    assert result["node_result"] == RESULT_TARGET_FOUND


@patch('src.nodes.find_missing.get_targets')
def test_find_missing_all_required_complete(mock_get_targets):
    """모든 필수 타겟이 완료된 경우를 테스트합니다."""
    # get_targets 함수를 모의하여 테스트 타겟 데이터 반환
    mock_get_targets.return_value = {
        "target1": {"required": True, "name": "Target 1", "description": "Test 1", "example": "Example 1"},
        "target2": {"required": True, "name": "Target 2", "description": "Test 2", "example": "Example 2"},
        "target3": {"required": False, "name": "Target 3", "description": "Test 3", "example": "Example 3"}
    }
    
    # Setup state with all required targets in results
    state = State({
        "results": {
            "target1": "result1",
            "target2": "result2"
        },
        "current_target": None,
        "node_result": None
    })
    
    # Execute
    result = find_missing(state)
    
    # Verify
    assert result["node_result"] == RESULT_ALL_TARGETS_COMPLETE
    assert result["current_target"] is None


@patch('src.nodes.find_missing.get_targets')
def test_find_missing_skip_non_required(mock_get_targets):
    """필수가 아닌 타겟만 누락된 경우를 테스트합니다."""
    # get_targets 함수를 모의하여 테스트 타겟 데이터 반환
    mock_get_targets.return_value = {
        "target1": {"required": True, "name": "Target 1", "description": "Test 1", "example": "Example 1"},
        "target2": {"required": False, "name": "Target 2", "description": "Test 2", "example": "Example 2"}
    }
    
    # Setup state with only non-required targets missing
    state = State({
        "results": {
            "target1": "result1"
        },
        "current_target": None,
        "node_result": None
    })
    
    # Execute
    result = find_missing(state)
    
    # Verify
    assert result["node_result"] == RESULT_ALL_TARGETS_COMPLETE
    assert result["current_target"] is None 