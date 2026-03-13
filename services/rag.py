from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

_vector_store = None
_embeddings = None

def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = GoogleGenerativeAIEmbeddings(model='model/embedding-001')
    return _embeddings

def add_pdf(file_path) -> int:
    global _vector_store
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, overlap=100)
    chunks = splitter.split_documents(docs)
    if not chunks:
        return 0
    emb = _get_embeddings()
    if _vector_store is None:
        _vector_store = FAISS.from_documents(chunks, emb)
    else:
        _vector_store.add_documents(chunks)
    
    return len(chunks)

def search_docs(query: str, k: int=3) -> str:
    if _vector_store is None:
        return "No vector database found. Ask the user to upload the pdf first"
    results = _vector_store.similarity_search(query, k=k)
    if not results:
        return "No result found from the vector database for the given query"
    content = [doc.page_content for doc in results]
    return "\n\n".join(content)