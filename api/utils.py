from langchain_groq import ChatGroq
from .config import GROQ_API_KEY, GROQ_MODEL

def generate_analysis_and_tips(user_input, context=None):
    try:
        # Initialize Groq LLM (free) with low temperature for factual responses
        llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model=GROQ_MODEL,
            temperature=0.0
        )
        
        # Prepare context string for prompt
        context_str = f"\n<context>\n{context}\n</context>\n" if context else "\n<context>No context available.</context>\n"

        # Generate Legal-focused analysis STRICTLY grounded in context
        analysis_prompt = f"""You are a strict Pakistan Legal Case Assistant. 
Your ONLY source of knowledge is the XML <context> provided below.

{context_str}

USER QUESTION: "{user_input}"

INSTRUCTIONS:
1. Provide a brief analysis of the user's question using ONLY the <context> above.
2. NEVER invent, fabricate, or guess case names, citation numbers (e.g. PLD, CLC, MLD) or legal details from your pre-training data.
3. Only mention case names that appear word-for-word inside the <context> tags.
4. If the <context> does not contain enough information, say so honestly. Do NOT hallucinate an analysis.

ANALYSIS:
"""
        analysis_response = llm.invoke(analysis_prompt)
        analysis = analysis_response.content
        
        # Generate Legal-focused tips grounded in context
        tips_prompt = f"""You are a strict Pakistan Legal Case Assistant. 
Your ONLY source of knowledge is the XML <context> provided below.

{context_str}

USER QUESTION: "{user_input}"

INSTRUCTIONS:
1. Based ONLY on the <context> above, provide 1-2 short, practical legal tips relevant to this question.
2. If the <context> doesn't contain relevant information, provide general procedural tips only (like "consult a qualified lawyer").

TIPS:
"""
        tips_response = llm.invoke(tips_prompt)
        tips = tips_response.content
        
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
