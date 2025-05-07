from typing import Dict, List, Any, Tuple, Optional
from langgraph.graph import StateGraph, END
import logging

from src.nodes.find_missing import find_missing
from src.nodes.generate_question import generate_question
from src.nodes.process_answer import process_answer
from src.state import State, StateManager
from src.entities import RESULT_TARGET_FOUND, RESULT_ALL_TARGETS_COMPLETE, RESULT_ANSWER_SUFFICIENT

logger = logging.getLogger(__name__)

class Agent:
    """
    대화형 데이터 수집 에이전트
    
    이 클래스는 LangGraph를 사용하여 사용자와의 대화를 통해 데이터를 수집하는 에이전트를 구현합니다.
    프로세스 흐름은 다음과 같습니다:
    
    1. 수집해야 할 데이터 항목 찾기 (find_missing)
    2. 사용자에게 질문 생성 (generate_question)
    3. 사용자 응답 처리 (process_answer)
    4. 모든 데이터가 수집될 때까지 반복
    """
    
    @staticmethod
    def add_user_message(content: str) -> Tuple[List[Dict], List[Dict]]:
        """
        사용자 메시지를 추가하고 에이전트의 응답을 처리합니다.
        
        Args:
            content: 사용자가 입력한 메시지
            
        Returns:
            Tuple[List[Dict], List[Dict]]: (모든 메시지, 새 AI 메시지만) 포함하는 튜플
        """
        # 사용자 메시지를 상태에 추가
        StateManager.append_message({"role": "human", "content": content})
        messages = StateManager.get_messages()
        
        # 상태에서 모델 설정 가져오기
        model_name, temperature, model_type, api_key = StateManager.get_model_settings()
        
        # 에이전트로 처리
        result = Agent._run_collector(messages, model_name, temperature, model_type, api_key)
        
        # 새 AI 메시지 가져오기
        all_messages = result.get("messages", [])
        new_messages = []
        
        if len(all_messages) > len(messages):
            new_messages = [msg for msg in all_messages[len(messages):] if msg["role"] == "ai"]
        
        return all_messages, new_messages
    
    @staticmethod
    def initialize_chat(model_name: str, temperature: float, 
                        model_type: str, api_key: Optional[str]) -> Tuple[List[Dict], List[Dict]]:
        """
        에이전트와의 채팅을 초기화하거나 재설정합니다.
        
        Args:
            model_name: 사용할 모델 이름
            temperature: 모델 온도 설정 (높을수록 무작위성 증가)
            model_type: 모델 유형 ("ollama" 또는 "openai")
            api_key: OpenAI 모델 사용 시 필요한 API 키
            
        Returns:
            Tuple[List[Dict], List[Dict]]: (모든 메시지, 새 AI 메시지만) 포함하는 튜플
        """
        # 모델 설정 업데이트
        StateManager.set_model_settings(model_name, temperature, model_type, api_key)
        
        # 기존 메시지 가져오기
        messages = StateManager.get_messages()
        
        # 에이전트로 처리
        result = Agent._run_collector(messages, model_name, temperature, model_type, api_key)
        
        # 새 AI 메시지 가져오기
        all_messages = result.get("messages", [])
        new_messages = []
        
        if len(all_messages) > len(messages):
            new_messages = [msg for msg in all_messages[len(messages):] if msg["role"] == "ai"]
        
        return all_messages, new_messages
    
    @staticmethod
    def _create_collector_graph(entry_point: str) -> Any:
        """
        데이터 수집 워크플로우 그래프를 생성합니다.
        
        워크플로우 구조:
        
        [시작] -> [find_missing] -> (타겟 발견?) -> [generate_question] -> [종료]
                       ^                                                      ^
                       |                                                      |
                       +------ [process_answer] <-- (사용자 응답) ------------+
        
        Args:
            entry_point: 워크플로우 진입점 ("find_missing", "process_answer" 또는 END)
            
        Returns:
            컴파일된 LangGraph 워크플로우
        """
        workflow = StateGraph(State)
        
        # === 노드 추가 ===
        # 1. find_missing: 수집되지 않은 타겟 데이터 찾기
        workflow.add_node("find_missing", find_missing)
        
        # 2. generate_question: 사용자에게 질문 생성
        workflow.add_node("generate_question", generate_question)
        
        # 3. process_answer: 사용자의 답변 처리
        workflow.add_node("process_answer", process_answer)
        
        # === 엣지 추가 ===
        # 1. find_missing 노드에서의 분기
        workflow.add_conditional_edges(
            "find_missing", 
            lambda state: (
                # 모든 타겟이 완료되었으면 워크플로우 종료
                "EXIT" if state.get("node_result") == RESULT_ALL_TARGETS_COMPLETE 
                # 아직 수집되지 않은 타겟이 있으면 질문 생성
                else "generate_question" if state.get("node_result") == RESULT_TARGET_FOUND 
                # 그 외의 경우 종료 (예: 오류 발생)
                else "EXIT"
            ),
            {
                "generate_question": "generate_question",
                "EXIT": END
            }
        )
        
        # 2. generate_question 노드는 질문 생성 후 항상 종료 (사용자 응답 대기)
        workflow.add_conditional_edges(
            "generate_question", 
            lambda _: "EXIT",
            {"EXIT": END}
        )
        
        # 3. process_answer 노드에서의 분기
        workflow.add_conditional_edges(
            "process_answer", 
            lambda state: (
                # 사용자 응답이 충분하면 다음 타겟 찾기
                "find_missing" if state.get("node_result") == RESULT_ANSWER_SUFFICIENT 
                # 응답이 부족하면 워크플로우 종료 (다음 사용자 입력 대기)
                else "EXIT"
            ),
            {
                "find_missing": "find_missing", 
                "EXIT": END
            }
        )
        
        # 워크플로우 진입점 설정
        workflow.set_entry_point(entry_point)
        
        # 컴파일된 워크플로우 반환
        return workflow.compile()
    
    @staticmethod
    def _run_collector(messages: List[Dict], model_name: str, 
                      temperature: float, model_type: str, 
                      api_key: Optional[str]) -> State:
        """
        메시지와 모델 설정으로 데이터 수집 워크플로우를 실행합니다.
        
        Args:
            messages: 대화 메시지 목록
            model_name: 사용할 모델 이름
            temperature: 모델 온도 설정
            model_type: 모델 유형 ("ollama" 또는 "openai")
            api_key: OpenAI 모델의 API 키
            
        Returns:
            State: 워크플로우 실행 후 업데이트된 상태
        """
        # 저장된 상태 로드
        saved_state = StateManager.load()
        
        # 대화 상태에 따른 워크플로우 진입점 결정
        if len(messages) == 0:
            # 메시지가 없으면 수집할 데이터 찾기부터 시작
            entry_point = "find_missing"
        elif messages[-1].get("role") == "human":
            # 마지막 메시지가 사용자의 메시지면 응답 처리
            entry_point = "process_answer"
        elif messages[-1].get("role") == "ai":
            # 마지막 메시지가 AI의 메시지면 종료 (이미 질문이 생성됨)
            entry_point = END
        else:
            # 기타 경우 (예: 시스템 메시지) 데이터 찾기부터 시작
            entry_point = "find_missing"
            
        logger.info(f"Entry point: {entry_point}")

        # 초기 상태 구성
        state: State = {
            "messages": messages,
            "node_result": "",
            "results": saved_state.get("results", {}),
            "current_target": saved_state.get("current_target"),
            "model": {
                "name": model_name,
                "temperature": temperature,
                "type": model_type,
                "api_key": api_key
            }
        }
        
        # 워크플로우 그래프 생성 및 실행
        graph = Agent._create_collector_graph(entry_point)
        
        try:
            # 워크플로우 실행
            result = graph.invoke(state)
            
            # 모든 데이터가 수집되었으면 요약 메시지 추가
            if result.get("node_result") == RESULT_ALL_TARGETS_COMPLETE:
                result["messages"].append({
                    "role": "ai", 
                    "content": Agent._create_summary_message(result)
                })
            
            # 결과 저장 및 반환
            StateManager.save(result)
            return result
            
        except Exception as e:
            # 오류 처리
            logger.error(f"Error processing response: {str(e)}")
            return {**state, "node_result": "error"}
    
    @staticmethod
    def _create_summary_message(result: State) -> str:
        """
        수집된 모든 데이터를 요약하는 메시지를 생성합니다.
        
        Args:
            result: 수집된 데이터가 포함된 상태 객체
            
        Returns:
            str: 수집된 데이터 요약 메시지
        """
        summary_message = "All information has been successfully collected. Here is a summary of all collected information:\n\n"
        
        # 수집된 각 타겟 데이터 요약
        for target_id, target_result in result.get("results", {}).items():
            target_name = target_result["name"]
            target_data = target_result["data"]
            
            # 타겟 이름 표시
            summary_message += f"**{target_name}**:\n"
            
            # 데이터 유형에 따른 표시
            if isinstance(target_data, list):
                # 리스트 유형 데이터 처리
                for item in target_data:
                    if isinstance(item, dict) and "name" in item and "description" in item:
                        summary_message += f"- {item['name']}: {item['description']}\n"
                    else:
                        summary_message += f"- {item}\n"
            elif isinstance(target_data, dict):
                # 사전 유형 데이터 처리
                for key, value in target_data.items():
                    summary_message += f"- {key}: {value}\n"
            else:
                # 기타 유형 데이터 처리
                summary_message += f"- {target_data}\n"
            
            summary_message += "\n"
        
        summary_message += "Conversation completed. Thank you!"
        return summary_message
