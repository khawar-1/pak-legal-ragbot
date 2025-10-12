from langchain_text_splitters.character import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores.faiss import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import OllamaLLM
from .config import KNOWLEDGE_BASE_PATH, OLLAMA_BASE_URL, LLAMA_MODEL, EMBEDDING_MODEL
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain

def retrieval(user_input):
    # Load documents
    loader = TextLoader(KNOWLEDGE_BASE_PATH)
    documents = loader.load()
    
    # Split documents into chunks
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(documents)
    
    # Initialize Ollama embeddings
    embeddings = OllamaEmbeddings(
        base_url=OLLAMA_BASE_URL,
        model=EMBEDDING_MODEL
    )
    
    # Create a vector database
    vector_db = FAISS.from_documents(texts, embeddings)
    
    # Create a retriever
    retriever = vector_db.as_retriever(search_kwargs={"k": 5})
    
    # Define the prompt template
    template = """
    You are an expert AWS Cloud Solutions Architect assistant.
    Your role is to help users understand AWS cloud services and recommend solutions for web application architectures.

    Guidelines:
    - Answer only using the provided context. If the answer is not in the context, say "I don’t have that information in my knowledge base."
    - Keep answers clear, structured, and concise.
    - Use technical AWS terms (e.g., EC2, S3, RDS, Lambda).
    - If relevant, explain trade-offs briefly (e.g., EC2 vs Lambda).
    - Do not invent services or features that are not in the context.

    Context:
    {context}

    User Question:
    {input}

    Answer:
    """

    
    # Create a prompt
    prompt = PromptTemplate.from_template(template)
    
    # Create Ollama LLM instance
    llm = OllamaLLM(
        base_url=OLLAMA_BASE_URL,
        model=LLAMA_MODEL,
        temperature=0.7
    )
    
    # Create a chain for combining documents
    combine_docs_chain = create_stuff_documents_chain(llm, prompt)
    
    # Retrieve relevant documents
    relevant_docs = retriever.invoke(user_input)
    
    # Invoke the chain with the user input and relevant documents
    answer = combine_docs_chain.invoke({"input": user_input, "context": relevant_docs})
    
    return answer

# Example usage
# # user_input = "Find the Maximum Element in an Array"
# answer = retrieval(user_input)
# print(answer)