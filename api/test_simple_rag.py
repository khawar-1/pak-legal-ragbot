#!/usr/bin/env python3
"""
Test script for the simplified RAG system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import KNOWLEDGE_BASE_PATH, OLLAMA_BASE_URL, LLAMA_MODEL, EMBEDDING_MODEL
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import json

def retrieval(user_input):
    # Load documents
    loader = TextLoader(KNOWLEDGE_BASE_PATH)
    documents = loader.load()
    
    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    
    # Create embeddings
    embeddings = OllamaEmbeddings(
        base_url=OLLAMA_BASE_URL,
        model=EMBEDDING_MODEL
    )
    
    # Create vector store
    vectorstore = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    
    # Create LLM
    llm = OllamaLLM(
        base_url=OLLAMA_BASE_URL,
        model=LLAMA_MODEL,
        temperature=0.1
    )
    
    # Create prompt template
    prompt_template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

    {context}

    Question: {question}
    Answer:"""
    
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )
    
    # Create retrieval chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        chain_type_kwargs={"prompt": PROMPT}
    )
    
    # Get answer
    answer = qa_chain.run(user_input)
    return answer

def generate_analysis_and_tips(user_input):
    # Create LLM for analysis and tips
    llm = OllamaLLM(
        base_url=OLLAMA_BASE_URL,
        model=LLAMA_MODEL,
        temperature=0.3
    )
    
    # Generate analysis
    analysis_prompt = f"""
    Analyze this AWS-related question: "{user_input}"
    
    Provide a brief analysis of what the user is asking and what key concepts they should understand.
    Keep it concise and focused on AWS/cloud concepts.
    """
    
    analysis = llm.generate([analysis_prompt])
    
    # Generate tips
    tips_prompt = f"""
    Based on this AWS question: "{user_input}"
    
    Provide 2-3 practical tips or best practices related to the topic.
    Focus on actionable advice for AWS/cloud implementation.
    """
    
    tips = llm.generate([tips_prompt])
    
    return analysis, tips

def test_rag_system():
    """Test the simplified RAG system"""
    print("=" * 60)
    print("TESTING SIMPLIFIED RAG SYSTEM")
    print("=" * 60)
    
    test_questions = [
        "What is AWS Lambda?",
        "How does Amazon S3 work?",
        "What is the difference between RDS and DynamoDB?",
        "How to set up a VPC in AWS?",
        "What is Amazon EC2?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\nTest {i}: {question}")
        print("-" * 40)
        try:
            # Test retrieval
            answer = retrieval(question)
            print(f"Answer: {answer[:200]}..." if len(answer) > 200 else f"Answer: {answer}")
            
            # Test analysis and tips
            analysis, tips = generate_analysis_and_tips(question)
            analysis_text = analysis.generations[0][0].text if hasattr(analysis, 'generations') else str(analysis)
            tips_text = tips.generations[0][0].text if hasattr(tips, 'generations') else str(tips)
            
            print(f"Analysis: {analysis_text[:100]}..." if len(analysis_text) > 100 else f"Analysis: {analysis_text}")
            print(f"Tips: {tips_text[:100]}..." if len(tips_text) > 100 else f"Tips: {tips_text}")
            
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 60)

def main():
    """Run the test"""
    print("AWS Cloud Assistant - Simplified RAG System Test")
    print("Make sure Ollama is running with the required models!")
    
    try:
        test_rag_system()
        print("\n" + "=" * 60)
        print("RAG SYSTEM TEST COMPLETED!")
        print("=" * 60)
    except Exception as e:
        print(f"Test failed: {e}")
        print("Make sure Ollama is running and the required models are available.")

if __name__ == "__main__":
    main()
