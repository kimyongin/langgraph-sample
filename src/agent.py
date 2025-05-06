from typing import Dict, List, Any, Tuple
from langgraph.graph import StateGraph, END
import logging

from src.nodes.find_missing import find_missing
from src.nodes.generate_question import generate_question
from src.nodes.process_answer import process_answer
from src.state import State, StateManager
from src.entities import RESULT_TARGET_FOUND, RESULT_ALL_TARGETS_COMPLETE, RESULT_ANSWER_SUFFICIENT

logger = logging.getLogger(__name__)

class Agent:
    """대화형 에이전트 로직을 캡슐화하는 클래스"""
    
    @staticmethod
    def add_user_message(content: str) -> Tuple[List[Dict], List[Dict]]:
        """
        사용자 메시지를 추가하고 에이전트 응답을 처리
        
        (모든 메시지, 새 AI 메시지만) 포함하는 튜플 반환
        """
        # 사용자 메시지를 상태에 추가
        StateManager.append_message({"role": "human", "content": content})
        messages = StateManager.get_messages()
        
        # 상태에서 모델 설정 가져오기
        model_name, temperature = StateManager.get_model_settings()
        
        # 에이전트로 처리
        result = Agent._run_collector(messages, model_name, temperature)
        
        # 새 AI 메시지 가져오기
        all_messages = result.get("messages", [])
        new_messages = []
        
        if len(all_messages) > len(messages):
            new_messages = [msg for msg in all_messages[len(messages):] if msg["role"] == "ai"]
        
        return all_messages, new_messages
    
    @staticmethod
    def initialize_chat(model_name: str = "llama3", temperature: float = 0.7) -> Tuple[List[Dict], List[Dict]]:
        """
        에이전트와의 채팅 초기화 또는 재설정
        
        (모든 메시지, 새 AI 메시지만) 포함하는 튜플 반환
        """
        # 모델 설정 업데이트
        StateManager.set_model_settings(model_name, temperature)
        
        # 기존 메시지 가져오기
        messages = StateManager.get_messages()
        
        # 에이전트로 처리
        result = Agent._run_collector(messages, model_name, temperature)
        
        # 새 AI 메시지 가져오기
        all_messages = result.get("messages", [])
        new_messages = []
        
        if len(all_messages) > len(messages):
            new_messages = [msg for msg in all_messages[len(messages):] if msg["role"] == "ai"]
        
        return all_messages, new_messages
    
    @staticmethod
    def _create_collector_graph(entry_point: str) -> Any:
        """지정된 진입점으로 LangGraph 생성"""
        workflow = StateGraph(State)
        
        # 노드 추가
        # find_missing: 수집되지 않은 타겟 데이터를 찾는 노드
        workflow.add_node("find_missing", find_missing)
        # generate_question: 사용자에게 질문을 생성하는 노드
        workflow.add_node("generate_question", generate_question)
        # process_answer: 사용자의 답변을 처리하는 노드
        workflow.add_node("process_answer", process_answer)
        
        # 엣지 추가
        # find_missing 노드에서 다음 실행 흐름을 결정하는 조건부 엣지
        workflow.add_conditional_edges(
            "find_missing", 
            lambda state: (
                # 모든 타겟이 완료되었으면 워크플로우 종료
                "EXIT" if state.get("node_result") == RESULT_ALL_TARGETS_COMPLETE 
                # 아직 수집되지 않은 타겟이 있으면 질문 생성 노드로 이동
                else "generate_question" if state.get("node_result") == RESULT_TARGET_FOUND 
                # 그 외의 경우 워크플로우 종료 (예: 오류 발생 시)
                else "EXIT"
            ),
            {
                # RESULT_TARGET_FOUND 결과일 경우 generate_question 노드로 이동
                "generate_question": "generate_question",
                # RESULT_ALL_TARGETS_COMPLETE 결과이거나 기타 경우에는 워크플로우 종료
                "EXIT": END
            }
        )
        
        # generate_question 노드는 질문 생성 후 항상 종료 (사용자 응답 대기)
        # 사용자가 응답하면 process_answer 노드가 외부에서 호출됨
        workflow.add_conditional_edges(
            "generate_question", 
            lambda _: "EXIT",
            {"EXIT": END}
        )
        
        # process_answer 노드에서 다음 실행 흐름을 결정하는 조건부 엣지
        workflow.add_conditional_edges(
            "process_answer", 
            lambda state: (
                # 사용자 응답이 충분한 정보를 포함하고 있으면 다시 find_missing 노드로 돌아가
                # 아직 수집되지 않은 다른 타겟이 있는지 확인
                "find_missing" if state.get("node_result") == RESULT_ANSWER_SUFFICIENT 
                # 응답이 부족하거나 처리할 수 없으면 워크플로우 종료 (다음 사용자 입력 대기)
                else "EXIT"
            ),
            {
                # RESULT_ANSWER_SUFFICIENT 결과일 경우 find_missing 노드로 돌아감
                "find_missing": "find_missing", 
                # 그 외의 경우에는 워크플로우 종료하고 다음 사용자 입력 대기
                "EXIT": END
            }
        )
        
        # 워크플로우의 진입점 설정 (process_answer 또는 find_missing)
        workflow.set_entry_point(entry_point)
        # 컴파일된 워크플로우 반환
        return workflow.compile()
    
    @staticmethod
    def _run_collector(messages: List[Dict], model_name: str = "llama3", temperature: float = 0.7) -> State:
        """메시지 처리 및 업데이트된 상태 반환"""
        saved_state = StateManager.load()
        
        # 대화 상태에 따른 진입점 결정
        if len(messages) == 0:
            # 메시지가 없으면 find_missing으로 시작
            entry_point = "find_missing"
        elif messages[-1].get("role") == "human":
            # 마지막 메시지가 사용자의 메시지면 process_answer 처리
            entry_point = "process_answer"
        elif messages[-1].get("role") == "ai":
            # 마지막 메시지가 AI의 메시지면 워크플로우 종료
            entry_point = END
        else:
            # 기타 경우 (예: 시스템 메시지) find_missing으로 시작
            entry_point = "find_missing"
        logger.info(f"Entry point: {entry_point}")

        # 초기 상태 구성
        state: State = {
            "messages": messages,
            "node_result": "",
            "model_name": model_name,
            "temperature": temperature,
            "results": saved_state.get("results", {}),
            "current_target": saved_state.get("current_target")
        }
        
        # 그래프 생성 및 실행
        graph = Agent._create_collector_graph(entry_point)
        
        try:
            result = graph.invoke(state)
            
            # 모든 대상이 완료되면 요약 메시지 추가
            if result.get("node_result") == RESULT_ALL_TARGETS_COMPLETE:
                result["messages"].append({
                    "role": "ai", 
                    "content": Agent._create_summary_message(result)
                })
            
            # 결과 저장
            StateManager.save(result)
            return result
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            return {**state, "node_result": "error"}
    
    @staticmethod
    def _create_summary_message(result: State) -> str:
        """수집된 모든 결과 데이터에서 요약 메시지 생성"""
        summary_message = "All information has been successfully collected. Here is a summary of all collected information:\n\n"
        
        for target_id, target_result in result.get("results", {}).items():
            target_name = target_result["name"]
            target_data = target_result["data"]
            
            summary_message += f"**{target_name}**:\n"
            
            if isinstance(target_data, list):
                for item in target_data:
                    if isinstance(item, dict) and "name" in item and "description" in item:
                        summary_message += f"- {item['name']}: {item['description']}\n"
                    else:
                        summary_message += f"- {item}\n"
            elif isinstance(target_data, dict):
                for key, value in target_data.items():
                    summary_message += f"- {key}: {value}\n"
            else:
                summary_message += f"- {target_data}\n"
            
            summary_message += "\n"
        
        summary_message += "Conversation completed. Thank you!"
        return summary_message
