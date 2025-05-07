import json
import textwrap
from typing import Dict, List, Any, Union
from src.utils.model import invoke

def dedent_prompt(text):
    """문자열의 들여쓰기를 제거하여 가독성을 높입니다."""
    return textwrap.dedent(text)


def create_dict_conversion_prompt(name: str, description: str, example: Dict[str, Any], user_message: str):
    """딕셔너리(객체) 형식 변환을 위한 프롬프트 생성"""
    # 데이터 준비
    example_json = json.dumps(example, ensure_ascii=False, indent=2)
    keys = list(example.keys())
    keys_str = ", ".join(keys)
    
    # 들여쓰기가 있는 템플릿
    template = """\
    <goal>
        You are a professional JSON conversion assistant. You need to convert the user's plain text response into accurate JSON format.
        
        <n>{name}</n>
        <description>{description}</description>
        <example>
        ```json
        {example_json}
        ```
        </example>
        
        <keys>{keys}</keys>
    </goal>

    <task>
        Extract the necessary information from the text above and create a JSON object that exactly matches the target JSON structure.
        The response must be in valid JSON format. The key names must exactly match the example.
        
        <user_input>
        ```
        {user_message}
        ```
        </user_input>
    </task>

    <thinking>
        Please use Chain of Thought (CoT) method to break down your thinking process:
        1. Analyze the target JSON structure and identify all required keys and data types.
        2. Identify information for each key from the user's response.
        3. For each key:
           - Check if the information is clearly provided.
           - If information is only partially provided, estimate the most appropriate value.
           - If information is not provided, use a reasonable default value.
        4. Ensure all values are in the appropriate format (string, number, object, array, etc.).
        5. Verify that the final JSON object matches the example structure.
    </thinking>

    <output>
        Return only the JSON object without additional explanations or meta information. Do not include your thinking process in the final output.
        The result must be in valid JSON format.
    </output>
    """
    
    # 들여쓰기 제거 및 변수 대입
    return dedent_prompt(template).format(
        name=name,
        description=description,
        example_json=example_json,
        keys=keys_str,
        user_message=user_message
    )


def create_list_conversion_prompt(name: str, description: str, example: List[Any], user_message: str):
    """리스트(배열) 형식 변환을 위한 프롬프트 생성"""
    # 데이터 준비
    example_json = json.dumps(example, ensure_ascii=False, indent=2)
    
    # 예시 항목의 구조 분석
    if len(example) > 0 and isinstance(example[0], dict):
        example_item = example[0]
        keys = list(example_item.keys())
        item_structure = f"Each item should include the following keys: {', '.join(keys)}"
    else:
        item_structure = "Pay attention to the format of each item"
    
    # 들여쓰기가 있는 템플릿
    template = """\
    <goal>
        You are a professional JSON conversion assistant. You need to convert the user's plain text response into accurate JSON array format.
        
        <n>{name}</n>
        <description>{description}</description>
        <example>
        ```json
        {example_json}
        ```
        </example>
        
        <structure>{item_structure}</structure>
    </goal>

    <task>
        Extract the necessary information from the text above and create a JSON array that exactly matches the target JSON structure.
        The response must be in valid JSON format. The format must exactly match the example.
        
        <user_input>
        ```
        {user_message}
        ```
        </user_input>
    </task>

    <thinking>
        Please use Chain of Thought (CoT) method to break down your thinking process:
        1. Analyze the structure of the target JSON array and the format of each item.
        2. Identify independent items in the user's response (e.g., separated paragraphs, numbered items, bullet points, etc.).
        3. For each item:
           - Extract all necessary information.
           - Structure the item to match the example format.
           - For complex items, correctly map each field.
        4. Combine all items into an array.
        5. Verify that the final JSON array matches the example structure.
    </thinking>

    <output>
        Return only the JSON array without additional explanations or meta information. Do not include your thinking process in the final output.
        The result must be in valid JSON format.
    </output>
    """
    
    # 들여쓰기 제거 및 변수 대입
    return dedent_prompt(template).format(
        name=name,
        description=description,
        example_json=example_json,
        item_structure=item_structure,
        user_message=user_message
    )


def create_string_conversion_prompt(name: str, description: str, example: str, user_message: str):
    """단순 문자열 형식 변환을 위한 프롬프트 생성"""
    # 들여쓰기가 있는 템플릿
    template = """\
    <goal>
        You are a professional text conversion assistant. You need to properly organize the user's response.
        
        <n>{name}</n>
        <description>{description}</description>
        <example>"{example}"</example>
    </goal>

    <task>
        Extract the necessary information from the text above and refine it to match the example format.
        
        <user_input>
        ```
        {user_message}
        ```
        </user_input>
    </task>

    <thinking>
        Please use Chain of Thought (CoT) method to break down your thinking process:
        1. Understand what information is needed based on the item name and description.
        2. Analyze the example format to determine the appropriate style, length, and level of detail.
        3. Identify relevant information in the user's response.
        4. Remove unnecessary details or repetitive content.
        5. Refine the text to match the example format while maintaining the user's core message.
        6. Ensure the final output is purposeful and conveys information in a way similar to the example.
    </thinking>

    <output>
        Return only the refined text without additional explanations or meta information. Do not include your thinking process in the final output.
    </output>
    """
    
    # 들여쓰기 제거 및 변수 대입
    return dedent_prompt(template).format(
        name=name,
        description=description,
        example=example,
        user_message=user_message
    )


def convert_data(name: str, description: str, example: Union[Dict, List, str], user_message: str):
    """
    사용자의 일반 텍스트 응답을 example에 정의된 형식으로 변환합니다.
    
    Args:
        name: 항목 이름
        description: 항목 설명
        example: 예시 데이터 구조 (dict, list, str)
        user_message: 사용자의 응답 텍스트
    """
    example_type = type(example)
    
    # 예시의 형태에 따라 다른 프롬프트 전략 사용
    if isinstance(example, dict):
        # 객체(딕셔너리) 형식일 경우
        prompt = create_dict_conversion_prompt(name, description, example, user_message)
    elif isinstance(example, list):
        # 배열 형식일 경우
        prompt = create_list_conversion_prompt(name, description, example, user_message)
    else:
        # 단순 문자열 형식일 경우
        prompt = create_string_conversion_prompt(name, description, example, user_message)
    
    # 중앙 invoke 함수 호출
    result = invoke(prompt)
    
    # 결과 추출 및 파싱
    return parse_llm_response(result, example_type)


def parse_llm_response(llm_response, example_type):
    """LLM 응답에서 원하는 형식을 추출하고 파싱합니다."""
    # 불필요한 마크다운 코드 블록이 있으면 제거
    if "```json" in llm_response:
        # 마크다운 JSON 코드 블록 찾기
        start_index = llm_response.find("```json") + 7
        end_index = llm_response.find("```", start_index)
        if end_index != -1:
            llm_response = llm_response[start_index:end_index].strip()
    elif "```" in llm_response:
        # 일반 마크다운 코드 블록 찾기
        start_index = llm_response.find("```") + 3
        end_index = llm_response.find("```", start_index)
        if end_index != -1:
            llm_response = llm_response[start_index:end_index].strip()
    
    # 예시 타입에 따른 파싱 처리
    if example_type == dict:
        try:
            # JSON 딕셔너리 형식 파싱 시도
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = llm_response[json_start:json_end]
                return json.loads(json_str)
            else:
                # JSON 형식이 아니면 원본 반환
                return llm_response
        except json.JSONDecodeError:
            # 파싱 오류 시 원본 반환
            return llm_response
    
    elif example_type == list:
        try:
            # JSON 배열 형식 파싱 시도
            json_start = llm_response.find('[')
            json_end = llm_response.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = llm_response[json_start:json_end]
                return json.loads(json_str)
            else:
                # JSON 형식이 아니면 원본 반환
                return llm_response
        except json.JSONDecodeError:
            # 파싱 오류 시 원본 반환
            return llm_response
    
    else:
        # 문자열 형식일 경우 그대로 반환
        return llm_response.strip('"\'').strip() 