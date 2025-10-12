from langchain_ollama import OllamaLLM as Ollama
from .config import OLLAMA_BASE_URL, LLAMA_MODEL

def generate_analysis_and_tips(user_input):
    try:
        # Initialize Ollama LLM
        llm = Ollama(
            base_url=OLLAMA_BASE_URL,
            model=LLAMA_MODEL,
            temperature=0.7
        )
        
        # Generate AWS-focused analysis
        analysis_prompt = f"""
        You are an AWS Cloud Solutions Architect assistant.
        The user has asked: "{user_input}"
        
        Analyze the question and provide a short, clear answer 
        based strictly on AWS cloud services knowledge (compute, storage, databases, networking, security).
        Keep the answer concise and avoid generic explanations.
        """
        analysis = llm.invoke(analysis_prompt)
        
        # Generate AWS-focused tips
        tips_prompt = f"""
        You are an AWS Cloud Solutions Architect assistant.
        The user has asked: "{user_input}"
        
        Provide very short, practical tips or best practices for AWS architecture or service selection 
        that are relevant to this question. 
        Keep the tips extremely concise (1–2 sentences).
        """
        tips = llm.invoke(tips_prompt)
        
        # Format responses to match expected structure
        class MockGeneration:
            def __init__(self, text):
                self.text = text
        
        class MockGenerations:
            def __init__(self, text):
                self.generations = [[MockGeneration(text)]]
        
        return MockGenerations(analysis), MockGenerations(tips)
        
    except Exception as e:
        raise ValueError(f"Error generating analysis and tips: {str(e)}")
