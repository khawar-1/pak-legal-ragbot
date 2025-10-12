from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores.faiss import FAISS
from langchain_ollama import OllamaEmbeddings
from .config import KNOWLEDGE_BASE_PATH, OLLAMA_BASE_URL, EMBEDDING_MODEL

def get_vectorstore():
    loader = TextLoader(KNOWLEDGE_BASE_PATH)
    documents = loader.load()
    
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(documents)
    
    # Use Ollama embeddings
    embeddings = OllamaEmbeddings(
        base_url=OLLAMA_BASE_URL,
        model=EMBEDDING_MODEL
    )
    
    # Create vectorstore from documents and embeddings
    vector_db = FAISS.from_documents(texts, embeddings)
    print(f"Vector database created with {len(texts)} documents")
    return vector_db