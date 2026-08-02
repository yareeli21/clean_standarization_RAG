from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
import os


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
persistent_directory = os.path.join(project_root, "datos")


embeding_model = HuggingFaceEmbeddings(model="paraphrase-multilingual-mpnet-base-v2")

db = Chroma(
    persist_directory= persistent_directory,
    embedding_function= embeding_model,
    collection_metadata = {"hnsw:space":"cosine"}
)


query = "Which island does SpaceX lease for its launches in the pacific"

retriver  = db.as_retriever(search_kargs = {"k": 3})#3 chunks con la similaridad mas alta


"""CONTUGURACION ALTERNA

retriver= db.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "k":5,
        "score_threshold": 0.3   # osea una similitud coseno menor a 0.3
    }
)
"""

relevant_docs = retriver.invoke(query)

print(f"User Query: {query}")

print("-----------------Context---------------")
for i, doc in enumerate(relevant_docs):
    print(f"Document{i+1} : \n{doc.page_content}\n")