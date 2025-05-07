import streamlit as st
import logging
import re
import html
from typing import List, Dict, Tuple

# 로깅을 INFO 레벨 메시지로 표시하도록 구성
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True  # 기존 구성 덮어쓰기
)

from src.agent import Agent
from src.state import StateManager

logger = logging.getLogger(__name__)


def configure_page():
    """Streamlit 페이지 설정 구성"""
    st.set_page_config(
        page_title="Data Collection Agent",
        page_icon="📋",
        layout="wide"
    )

def initialize_session_state():
    """세션 상태 변수 초기화"""
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
    if "last_model_settings" not in st.session_state:
        st.session_state.last_model_settings = None

def render_sidebar() -> Tuple[str, float, str, str]:
    """사이드바 UI 요소 렌더링 및 모델 설정 관리"""
    with st.sidebar:
        st.header("Model Settings")
        
        # 이전에 모델이 선택되었는지 확인
        is_model_selected = StateManager.is_model_selected()
        
        # 저장된 모델 설정 가져오기
        saved_model_name, saved_temperature, saved_model_type, saved_api_key = StateManager.get_model_settings()
        
        # 모델 유형 기본값 설정 (모델이 선택되지 않았으면 None)
        model_type_index = 0  # 기본값은 None
        if is_model_selected:
            if saved_model_type == "ollama":
                model_type_index = 1
            elif saved_model_type == "openai":
                model_type_index = 2
        
        # 모델 유형 선택
        model_type = st.radio(
            "Select Model Type",
            ["None", "Ollama (Local)", "OpenAI (API)"],
            index=model_type_index
        )
        
        # 초기 상태 설정
        model = None
        temperature = None
        api_key = None
        model_type_id = None  # 내부 식별자로 사용될 모델 유형
        is_valid_configuration = False  # 유효한 모델 구성인지 여부
        
        # 모델 유형에 따라 다른 모델 선택 옵션 표시
        if model_type == "Ollama (Local)":
            # 저장된 설정에서 Ollama 모델 기본값 설정
            ollama_models = ["llama3", "llama2", "mistral", "gemma"]
            default_model_index = 0
            if is_model_selected and saved_model_type == "ollama" and saved_model_name in ollama_models:
                default_model_index = ollama_models.index(saved_model_name)
            
            model = st.selectbox(
                "Select Ollama Model",
                ollama_models,
                index=default_model_index
            )
            model_type_id = "ollama"
            is_valid_configuration = True  # Ollama는 API 키가 필요없으므로 항상 유효
            
            # 모델 설정 업데이트
            current_settings = (model, 0.2, model_type_id, None)
            if st.session_state.last_model_settings != current_settings:
                StateManager.set_model_settings(model, 0.2, model_type_id, None)
                st.session_state.initialized = False
                st.session_state.last_model_settings = current_settings
            
        elif model_type == "OpenAI (API)":
            # 저장된 설정에서 OpenAI 모델 기본값 설정
            openai_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
            default_model_index = 0
            if is_model_selected and saved_model_type == "openai" and saved_model_name in openai_models:
                default_model_index = openai_models.index(saved_model_name)
            
            model = st.selectbox(
                "Select OpenAI Model",
                openai_models,
                index=default_model_index
            )
            # API 키 입력 필드 (저장된 API 키를 기본값으로 설정)
            api_key_value = ""
            if is_model_selected and saved_model_type == "openai" and saved_api_key:
                api_key_value = saved_api_key
                
            api_key = st.text_input(
                "OpenAI API Key", 
                value=api_key_value,
                help="Enter your OpenAI API key"
            )
            model_type_id = "openai"
            # API 키가 입력되었는지 확인 (None이 아니고 공백이 아닌지)
            is_valid_configuration = api_key is not None and api_key.strip() != ""
            
            # API 키가 입력된 경우에만 모델 설정 업데이트
            if is_valid_configuration:
                current_settings = (model, 0.2, model_type_id, api_key)
                if st.session_state.last_model_settings != current_settings:
                    StateManager.set_model_settings(model, 0.2, model_type_id, api_key)
                    st.session_state.initialized = False
                    st.session_state.last_model_settings = current_settings
                
        else:
            # None 선택 시 안내 메시지 표시 및 모델 상태 설정 초기화
            st.info("👆 Please select a model type to continue")
            # None 선택 시 상태에서 모델 설정 제거
            if st.session_state.last_model_settings is not None:
                StateManager.set_model_selected(False)
                st.session_state.initialized = False
                st.session_state.last_model_settings = None
        
        # 모델 유형이 선택된 경우에만 온도 설정 표시
        if model_type != "None":
            # 저장된 온도값을 기본값으로 설정
            default_temperature = 0.2
            if is_model_selected:
                default_temperature = saved_temperature
            
            temperature = st.slider(
                "Temperature", 
                0.0, 1.0, default_temperature, 0.1
            )
            
            # 온도 설정이 변경된 경우 모델 설정 업데이트
            if is_valid_configuration:
                current_settings = (model, temperature, model_type_id, api_key)
                if st.session_state.last_model_settings != current_settings:
                    StateManager.set_model_settings(model, temperature, model_type_id, api_key)
                    st.session_state.initialized = False
                    st.session_state.last_model_settings = current_settings
        else:
            # 모델이 None일 때는 temperature 값을 None으로 설정
            temperature = None
        
        st.markdown("---")
        render_results_section()
        
        # 모델이 선택된 경우에만 초기화 버튼 활성화
        st.markdown("---")
        st.header("Conversation Management")
        if st.button("Reset", use_container_width=True, disabled=not StateManager.is_model_selected()):
            # 상태 초기화
            if StateManager.reset():
                st.session_state.initialized = False
                st.success("Conversation has been reset. Refreshing page...")
                st.rerun()
            else:
                st.error("An error occurred while resetting the conversation.")
        
        st.markdown("---")
        st.markdown("### Information")
        
        # 모델 유형에 따라 다른 안내 메시지 표시
        if model_type == "Ollama (Local)":
            st.markdown("""
            This app is an interactive agent that collects data defined in target.json.
            
            Please ensure the selected model is installed in Ollama.
            
            How to install models in Ollama:
            ```
            ollama pull [model_name]
            ```
            """)
        elif model_type == "OpenAI (API)":
            st.markdown("""
            This app is an interactive agent that collects data defined in target.json.
            
            Using OpenAI models requires a valid API key.
            """)
        
        return model, temperature, model_type_id, api_key

def render_results_section():
    """수집 결과 표시"""
    results = StateManager.get_results()
    st.header("Collected Data")
    if results:        
        for target_id in results:
            st.success(f"✅ {target_id}")
    else:
        st.info("No data has been collected yet.")

def render_chat_messages():
    """대화 메시지 표시"""
    messages = StateManager.get_messages()
    for message in messages:
        if message["role"] == "system":
            continue
        elif message["role"] == "human":
            with st.chat_message("user"):
                st.markdown(message["content"])
        elif message["role"] == "ai":
            with st.chat_message("assistant"):
                st.markdown(message["content"])
        elif message["role"] == "debug":
            with st.chat_message("debug"):
                st.markdown(message["content"])

def main():
    """메인 애플리케이션 흐름"""
    configure_page()
    initialize_session_state()
    
    st.title("📋 Data Collection Agent")
    st.markdown("An AI agent that collects information through conversations with users.")
    
    model, temperature, model_type, api_key = render_sidebar()
    
    # 모델이 선택되지 않은 경우 안내 메시지만 표시하고 함수 종료
    if not StateManager.is_model_selected():
        st.info("👈 모델을 선택해야 대화를 시작할 수 있습니다. 사이드바에서 모델을 선택해주세요.")
        return
    
    # ---- 이하 코드는 모델이 선택된 경우에만 실행됨 ----
    
    # 채팅 메시지 표시
    render_chat_messages()
    
    if not st.session_state.initialized:
        # 에이전트 초기화 및 응답 표시
        with st.spinner("Initializing agent..."):
            # 모든 매개변수를 명시적으로 전달
            model_settings = StateManager.get_model_settings()
            _, new_messages = Agent.initialize_chat(
                model_name=model_settings[0], 
                temperature=model_settings[1], 
                model_type=model_settings[2], 
                api_key=model_settings[3]
            )
            
            for msg in new_messages:
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])
                    
        st.session_state.initialized = True
    
    # 채팅 입력 필드 표시 (모델이 선택된 경우에만 실행)
    user_input = st.chat_input("Enter your message...", disabled=not StateManager.is_model_selected())
    if user_input:
        # UI에 사용자 메시지 추가
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # 에이전트로 처리하고 새 메시지 가져오기
        with st.spinner("Thinking..."):
            _, new_ai_messages = Agent.add_user_message(user_input)
            
            # 새 AI 응답 표시
            for msg in new_ai_messages:
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])
        
        # 필요한 경우에만 재실행 (사용자 입력 후 UI 업데이트를 위해)
        st.rerun()

if __name__ == "__main__":
    main() 