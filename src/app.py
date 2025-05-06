import streamlit as st
import logging
import re
import html
from typing import List, Dict

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

def render_sidebar():
    """사이드바 UI 요소 렌더링"""
    with st.sidebar:
        st.header("Model Settings")
        model = st.selectbox(
            "Select Ollama Model",
            ["llama3", "llama2", "mistral", "gemma"],
            index=0
        )
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        
        # 에이전트 상태의 모델 설정 업데이트
        StateManager.set_model_settings(model, temperature)
        
        st.markdown("---")
        render_results_section()
        
        # 초기화 버튼 추가
        st.markdown("---")
        st.header("Conversation Management")
        if st.button("Reset", use_container_width=True, type="primary"):
            # 상태 초기화
            if StateManager.reset():
                st.session_state.initialized = False
                st.success("Conversation has been reset. Refreshing page...")
                st.rerun()
            else:
                st.error("An error occurred while resetting the conversation.")
        
        st.markdown("---")
        st.markdown("### Information")
        st.markdown("""
        This app is an interactive agent that collects data defined in target.json.
        
        Please ensure the selected model is installed in Ollama.
        
        How to install models in Ollama:
        ```
        ollama pull [model_name]
        ```
        """)
        
        return model, temperature

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
    
    model, temperature = render_sidebar()
    render_chat_messages()
    
    if not st.session_state.initialized:
        # 에이전트 초기화 및 응답 표시
        with st.spinner("Thinking..."):
            _, new_messages = Agent.initialize_chat(model, temperature)
            
            for msg in new_messages:
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])
                    
        st.session_state.initialized = True
        st.rerun()
    
    user_input = st.chat_input("Enter your message...")
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
            
        st.rerun()

if __name__ == "__main__":
    main() 