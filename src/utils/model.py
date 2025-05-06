from langchain_community.llms import Ollama

def get_llm(model_name: str = "llama3", temperature: float = 0.7):
    """
    Ollama LLM 모델을 초기화하고 반환합니다.
    """
    return Ollama(model=model_name, temperature=temperature) 