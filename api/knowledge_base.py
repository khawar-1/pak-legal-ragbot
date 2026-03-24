from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores.faiss import FAISS
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from .config import KNOWLEDGE_BASE_PATH, HUGGINGFACE_API_TOKEN

def get_vectorstore():
    loader = TextLoader(KNOWLEDGE_BASE_PATH)
    documents = loader.load()
    
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(documents)
    
    # Use free HuggingFace embeddings (no daily quota limits)
    embeddings = HuggingFaceEndpointEmbeddings(
        model="sentence-transformers/all-MiniLM-L6-v2",
        task="feature-extraction",
        huggingfacehub_api_token=HUGGINGFACE_API_TOKEN
    )
    
    # Create vectorstore from documents and embeddings
    vector_db = FAISS.from_documents(texts, embeddings)
    print(f"Vector database created with {len(texts)} documents")
    return vector_db