import json
import logging
from typing import Any, Dict, List, Optional, Union
from src.state import State
from src.target import TargetItem
from src.utils.model import get_llm
from src.utils.convert import convert_data, dedent_prompt
from src.utils.decorator import node
from src.entities import RESULT_ANSWER_SUFFICIENT, RESULT_ANSWER_INSUFFICIENT, RESULT_ERROR

logger = logging.getLogger(__name__)

@node
def process_answer(state: State) -> State:
    try:      
        # current_target이 None인지 확인
        current_target = state.get("current_target")
        if not current_target:
            logger.warning("처리할 타겟이 없습니다. 불충분 상태로 반환합니다.")
            state["node_result"] = RESULT_ANSWER_INSUFFICIENT
            return state
        
        # 프롬프트 템플릿
        template = """\
        <goal>
            You are an assistant collecting specific information from users.  
            Collect information clearly specified below:
            <name>{name}</name>
            <description>{description} (explicitly state required fields here)</description>
            <example>{example}</example> <!-- Reference only, NOT for evaluation -->
        </goal>

        <task>
            Evaluate if "<messages>" sufficiently fulfills "<goal>" and generate an XML response.
            "<messages>" contains explicit conversation history between you and the user.
            <messages>{messages}</messages>
        </task>

        <rules>
            1. Evaluation MUST rely exclusively on explicit user responses in "<messages>".
            2. Do NOT infer, assume, or imagine information not explicitly stated.
            3. NEVER use "<example>" for evaluation.
            4. Mark as SUFFICIENT only if user explicitly provides clearly relevant, usable information.
            5. Mark as INSUFFICIENT if the user response is:
                - Vague or uncertain (e.g., "hmm", "thinking...", "maybe", "not sure")
                - Explicitly stating ignorance (e.g., "I don't know")
                - Irrelevant to the required fields
        </rules>

        <thinking>
            Follow these explicit evaluation steps (CoT):
            1. Clearly restate exactly what required fields must be provided.
            2. List explicitly provided information from "<messages>".
            3. Confirm explicitly that no assumptions or inferred details are made.
            4. Confirm explicitly that all rules above are precisely followed.
            5. Provide an explicit reason for sufficient or insufficient judgment.
        </thinking>

        <output>
            Provide response strictly in this XML format only:

            <sufficient>
                <code>SUFFICIENT</code>
                <reason>Clearly state exactly why explicitly provided information meets the requirement.</reason>
                <result>Explicitly provided fields and their values.</result>
            </sufficient>

            <insufficient>
                <code>INSUFFICIENT</code>
                <reason>Clearly specify the exact reason why information is insufficient (e.g., vague, unclear, irrelevant).</reason>
                <result>Provide precise questions to collect missing required information.</result>
            </insufficient>
        </output>
        """
        
        # 들여쓰기 제거 및 변수 대체
        prompt = dedent_prompt(template).format(
            name=current_target["name"],
            description=current_target["description"],
            example=json.dumps(current_target["example"], ensure_ascii=False, indent=2),
            messages=state["messages"]
        )
        
        # 답변 평가
        llm = get_llm(model_name=state["model_name"], temperature=state["temperature"])
        evaluation = llm.invoke(prompt)
        state["messages"].append({"role": "debug", "content": evaluation})
        
        # 충분성에 따른 처리
        if "<code>SUFFICIENT</code>" in evaluation:           
            # 충분한 답변 처리
            return handle_sufficient_answer(state, llm, current_target, evaluation)
        else:
            # 불충분한 답변 처리
            return handle_insufficient_answer(state, evaluation)
        
    except Exception as e:
        logger.error(f"응답 처리 중 오류 발생: {str(e)}", exc_info=True)
        state["node_result"] = RESULT_ERROR
        state["error"] = str(e)
        return state


def extract_result(evaluation: str, tag_name: str) -> Optional[str]:
    """XML 평가에서 결과 추출"""
    result = None
    if f"<{tag_name}>" in evaluation and "<result>" in evaluation:
        start_index = evaluation.find(f"<{tag_name}>")
        end_index = evaluation.find(f"</{tag_name}>", start_index)
        if start_index != -1 and end_index != -1:
            content = evaluation[start_index:end_index]
            result_start = content.find("<result>")
            result_end = content.find("</result>", result_start)
            if result_start != -1 and result_end != -1:
                result = content[result_start + len("<result>"):result_end].strip()
    return result


def handle_sufficient_answer(state: State, llm, current_target, evaluation) -> State:
    """충분한 답변 처리"""
    # XML에서 결과 추출
    result = extract_result(evaluation, "sufficient")
    if result is None:
        raise ValueError("결과를 추출할 수 없습니다.")
    
    # 답변을 타겟 구조로 변환
    formatted_answer = convert_data(
        llm, 
        current_target["name"], 
        current_target["description"], 
        current_target["example"], 
        result
    )
    logger.info(f"형식화된 답변: {formatted_answer}")
    current_target = state["current_target"]
    target_id = current_target["id"]
    
    # 결과 저장을 위한 상태 업데이트
    if "results" not in state:
        state["results"] = {}
    
    # 타겟 이름과 설명으로 결과 저장
    state["results"][target_id] = {
        "name": current_target["name"],
        "description": current_target["description"],
        "data": formatted_answer
    }
    
    # 확인 메시지 생성
    message = f"'{current_target['name']}' is successfully saved. Let's move on to the next item."
    
    state["messages"].append({"role": "ai", "content": message})
    state["node_result"] = RESULT_ANSWER_SUFFICIENT
    
    return state


def handle_insufficient_answer(state: State, evaluation: str) -> State:
    """불충분한 답변 처리"""
    # XML에서 결과 추출
    result = extract_result(evaluation, "insufficient")
    if result is None:
        result = "More information is needed. Please provide more details."   
   
    state["messages"].append({"role": "ai", "content": result})
    state["node_result"] = RESULT_ANSWER_INSUFFICIENT
    
    return state