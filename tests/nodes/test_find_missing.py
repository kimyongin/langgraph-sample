import pytest
from src.nodes.find_missing import find_missing, RESULT_TARGET_FOUND, RESULT_ALL_TARGETS_COMPLETE
from src.state import State


def test_find_missing_required_target():
    # Setup state with a required target not in results
    state = State({
        "targets": {
            "target1": {"required": True},
            "target2": {"required": True}
        },
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


def test_find_missing_all_required_complete():
    # Setup state with all required targets in results
    state = State({
        "targets": {
            "target1": {"required": True},
            "target2": {"required": True},
            "target3": {"required": False}
        },
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


def test_find_missing_skip_non_required():
    # Setup state with only non-required targets missing
    state = State({
        "targets": {
            "target1": {"required": True},
            "target2": {"required": False}
        },
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