from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI
import os
import json
import httpx
from pathlib import Path
from typing import Optional
import logging

def _read_state():
    """state.json 파일에서 상태 정보를 읽어옵니다."""
    state_path = Path("resources/data/state.json")
    if not state_path.exists():
        raise ValueError("state.json 파일이 존재하지 않습니다. 애플리케이션을 먼저 실행해주세요.")
    
    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    
    return state

def _get_llm_instance(model_name: str = "llama3", temperature: float = 0.7, 
                     model_type: str = "ollama", api_key: Optional[str] = None):
    """
    모델 타입에 따라 적절한 LLM 객체를 초기화하고 반환합니다.
    
    Args:
        model_name: 모델 이름 (llama3, gpt-3.5-turbo, gpt-4 등)
        temperature: 생성 온도 파라미터
        model_type: 모델 타입 ("ollama" 또는 "openai")
        api_key: OpenAI API 키 (model_type이 "openai"일 때만 사용)
    """
    logger = logging.getLogger(__name__)
    
    if model_type == "openai":
        if not api_key:
            logger.error("API 키가 없습니다. OpenAI 모델을 초기화할 수 없습니다.")
            raise ValueError("OpenAI 모델을 사용하려면 API 키가 필요합니다.")
            
        logger.info(f"OpenAI 모델 초기화: {model_name}, API 키 길이: {len(api_key) if api_key else 0}")
        
        # SSL 인증서 검증 우회 설정
        os.environ["OPENAI_VERIFY_SSL_CERTS"] = "false"
        os.environ["REQUESTS_CA_BUNDLE"] = ""
        os.environ["SSL_CERT_FILE"] = ""
        
        # SSL 검증을 비활성화한 httpx 클라이언트 생성
        http_client = httpx.Client(verify=False)
        
        return ChatOpenAI(
            model=model_name, 
            temperature=temperature, 
            openai_api_key=api_key,
            http_client=http_client
        )
    else:
        logger.info(f"Ollama 모델 초기화: {model_name}")
        return Ollama(model=model_name, temperature=temperature)

def invoke(prompt: str):
    """
    state.json 파일을 참조하여 적절한 LLM 객체를 생성하고 프롬프트를 처리합니다.
    
    Args:
        prompt: 모델에 전달할 프롬프트 문자열
        
    Returns:
        처리된 응답 (문자열)
    """
    # state.json에서 모델 설정 읽기
    state = _read_state()
    model_config = state.get("model")    

    model_name = model_config.get("name")
    temperature = model_config.get("temperature")
    model_type = model_config.get("type")
    api_key = model_config.get("api_key")
    
    # LLM 객체 생성
    llm = _get_llm_instance(model_name, temperature, model_type, api_key)
    
    # 프롬프트 처리
    result = llm.invoke(prompt)
    
    # AIMessage 객체일 경우 content 속성 추출
    if hasattr(result, 'content'):
        result = result.content
    
    return result 