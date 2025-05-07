import json
import logging
from src.state import State
from src.target import TargetItem
from src.utils.model import invoke
from src.utils.convert import dedent_prompt
from src.utils.decorator import node
from src.entities import RESULT_QUESTION_GENERATED, RESULT_ERROR

logger = logging.getLogger(__name__)

@node
def generate_question(state: State) -> State:
    try:       
        # 프롬프트 템플릿
        prompt_template = """\
        <goal>
            You are an assistant collecting information from users. You need to collect information about the following item:           
            <name>{name}</name>
            <description>{description}</description>
            <example>{example}</example>
        </goal>

        <task>
            Please generate a question to collect information for "<goal>".
            Reference the description and examples, and if necessary, mention the examples to help the user understand how to respond.
            Generate only the question. Do not include other explanations or meta information.
        </task>

        <thinking>
            Please use Chain of Thought (CoT) method to break down your thinking process:
            1. First, understand what kind of information is needed based on the name and description
            2. Analyze the example data structure to understand what format is expected
            3. Consider what is the best way to ask this question to get a clear and comprehensive answer
            4. Formulate a question that will guide the user to provide information in the expected format
            5. Ensure the question is clear, specific, and easy to understand
        </thinking>

        <output>
            IMPORTANT: You MUST NOT include your thinking process in the final output. DO NOT include any text like "</thinking>" in your response.
            
            Your response must contain ONLY the direct question for the user. 
            Do not include explanations, XML tags, or any other meta-information.
            
            Example of correct output format:
            "What is the purpose of this project?"

            Example of INCORRECT output format:
            "Here's my thinking process: ..."
            "Here's my formulated question: ..."
            
            REMEMBER: Your output should be ONLY a simple question. No explanations before or after.
        </output>
        """
        
        # 프롬프트에 변수 채우기
        prompt = dedent_prompt(prompt_template).format(
            name=state["current_target"]["name"],
            description=state["current_target"]["description"],
            example=json.dumps(state["current_target"]["example"], ensure_ascii=False, indent=2)
        )
    
        # 중앙 invoke 함수 호출
        question = invoke(prompt)
        
        # 프롬프트 실행 결과를 메시지에 추가
        if "messages" not in state:
            state["messages"] = []
        
        state["messages"].append({"role": "ai", "content": question})
        state["node_result"] = RESULT_QUESTION_GENERATED
        return state

    except Exception as e:
        logger.error(f"질문 생성 중 오류 발생: {str(e)}")
        state["node_result"] = RESULT_ERROR
        state["error"] = str(e)
        return state 