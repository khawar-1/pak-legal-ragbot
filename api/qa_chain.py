from langchain_groq import ChatGroq
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.chains.question_answering import load_qa_chain
from .knowledge_base import get_vectorstore
from .config import GROQ_API_KEY, GROQ_MODEL

def get_qa_chain():
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0.7
    )
    vectorstore = get_vectorstore()
    
    # Create a chain to combine documents using the LLM
    combine_documents_chain = load_qa_chain(llm, chain_type="stuff")
    
    # Pass the combine_documents_chain and retriever to RetrievalQA
    qa_chain = RetrievalQA(
        combine_documents_chain=combine_documents_chain,
        retriever=vectorstore.as_retriever()
    )
    print("QA Chain created with Gemini")
    
    return qa_chain

def run_qa_chain(qa_chain: RetrievalQA, user_input):
    try:
        print(f"Processing input: {user_input}")
        result = qa_chain.invoke({"query": user_input})
        print(f"QA Chain result: {result}")
        return result
    except Exception as e:
        raise ValueError(f"Error running QA chain: {str(e)}")