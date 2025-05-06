import json
from langchain_community.llms import Ollama
from src.utils.convert import (
    convert_data,
    create_dict_conversion_prompt,
    create_list_conversion_prompt,
    create_string_conversion_prompt,
    parse_llm_response
)


def get_test_llm():
    """테스트용 LLM 모델을 반환합니다."""
    # Note: Ollama is deprecated but we'll keep it for compatibility
    # In a future update, we should switch to: from langchain_ollama import OllamaLLM
    return Ollama(model="llama3", temperature=0.7)


def test_convert_data_dict():
    """딕셔너리 형식 변환 기능을 테스트합니다."""
    try:
        llm = get_test_llm()
        
        # 테스트 케이스: 딕셔너리 형식
        dict_target = {
            "id": "project_overview",
            "name": "프로젝트 개요",
            "description": "프로젝트의 전반적인 목적과 배경에 대해 설명해주세요.",
            "required": True,
            "example": {
                "목적": "사용자 경험 향상",
                "배경": "기존 시스템의 문제점 해결",
                "주요기능": "결제 프로세스 간소화"
            }
        }
        
        user_message = """
        이 프로젝트는 사용자와의 대화를 통해 요구사항을 수집하고 문서화하는 것을 목적으로 합니다.
        기존의 요구사항 수집 방식은 정형화되지 않아 누락되는 정보가 많았습니다. 
        AI를 활용하여 체계적으로 정보를 수집하고 문서화함으로써 요구사항 수집 과정의 효율성을 높이는 것이 주요 목표입니다.
        """
        
        print("==== 딕셔너리 변환 테스트 ====")
        
        # 명시적으로 필요한 데이터만 전달
        result = convert_data(
            llm, 
            dict_target["name"], 
            dict_target["description"], 
            dict_target["example"], 
            user_message
        )
        print(f"결과: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 검증
        assert result is not None, "변환 결과가 None이어서는 안 됩니다."
        assert isinstance(result, dict), "딕셔너리 타입 변환 결과는 딕셔너리여야 합니다."
        
        # 키 확인
        for key in dict_target["example"].keys():
            assert key in result, f"결과에 예시 키 '{key}'가 없습니다."
        
    except Exception as e:
        assert False, f"테스트 중 오류 발생: {str(e)}"


def test_convert_data_list():
    """리스트 형식 변환 기능을 테스트합니다."""
    try:
        llm = get_test_llm()
        
        # 테스트 케이스: 리스트 형식
        list_target = {
            "id": "stakeholders",
            "name": "이해관계자",
            "description": "프로젝트와 관련된 이해관계자들을 알려주세요.",
            "required": True,
            "example": [
                {"name": "사용자", "role": "앱을 사용하는 최종 사용자", "interests": "사용 편의성"},
                {"name": "관리자", "role": "시스템 관리 담당자", "interests": "시스템 안정성과 보안"}
            ]
        }
        
        user_message = """
        이 프로젝트의 이해관계자는 크게 세 그룹입니다. 
        첫째, 개발자들인데 이들은 코드의 품질과 유지보수성에 관심이 있습니다. 
        둘째, 제품 관리자로 제품의 기능과 사용자 만족도에 초점을 맞춥니다. 
        셋째, 최종 사용자들은 시스템의 사용성과 성능에 관심이 있습니다.
        """
        
        print("==== 리스트 변환 테스트 ====")
        
        # 명시적으로 필요한 데이터만 전달
        result = convert_data(
            llm, 
            list_target["name"], 
            list_target["description"], 
            list_target["example"], 
            user_message
        )
        print(f"결과: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 검증
        assert result is not None, "변환 결과가 None이어서는 안 됩니다."
        assert isinstance(result, list), "리스트 타입 변환 결과는 리스트여야 합니다."
        assert len(result) > 0, "결과 리스트는 비어있지 않아야 합니다."
        
        # 첫 항목 구조 확인 (딕셔너리인 경우)
        if list_target["example"] and isinstance(list_target["example"][0], dict):
            expected_keys = list_target["example"][0].keys()
            for key in expected_keys:
                assert key in result[0], f"결과의 첫 항목에 예시 키 '{key}'가 없습니다."
        
    except Exception as e:
        assert False, f"테스트 중 오류 발생: {str(e)}"


def test_convert_data_string():
    """문자열 형식 변환 기능을 테스트합니다."""
    try:
        llm = get_test_llm()
        
        # 테스트 케이스: 문자열 형식
        string_target = {
            "id": "project_summary",
            "name": "프로젝트 요약",
            "description": "프로젝트를 한 문장으로 요약해주세요.",
            "required": True,
            "example": "이 프로젝트는 온라인 쇼핑몰의 결제 시스템을 개선하여 사용자 경험을 향상시키는 것을 목적으로 합니다."
        }
        
        user_message = """
        이 프로젝트는 AI를 활용하여 사용자와의 대화를 통해 요구사항을 수집하고 문서화하는 시스템을 개발하여
        요구사항 수집 과정의 효율성을 높이는 것이 목표입니다.
        """
        
        print("==== 문자열 변환 테스트 ====")
        
        # 명시적으로 필요한 데이터만 전달
        result = convert_data(
            llm, 
            string_target["name"], 
            string_target["description"], 
            string_target["example"], 
            user_message
        )
        print(f"결과: {result}")
        
        # 검증
        assert result is not None, "변환 결과가 None이어서는 안 됩니다."
        assert isinstance(result, str), "문자열 타입 변환 결과는 문자열이어야 합니다."
        assert len(result) > 0, "결과 문자열은 비어있지 않아야 합니다."
        
    except Exception as e:
        assert False, f"테스트 중 오류 발생: {str(e)}"


if __name__ == "__main__":
    print("===== 딕셔너리 변환 테스트 =====")
    test_convert_data_dict()
    print("\n===== 리스트 변환 테스트 =====")
    test_convert_data_list()
    print("\n===== 문자열 변환 테스트 =====")
    test_convert_data_string()
    print("\n모든 테스트가 성공적으로 완료되었습니다.") 