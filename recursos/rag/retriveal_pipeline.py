from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM, OllamaEmbeddings, ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
import os
from langchain_huggingface import ChatHuggingFace
from langchain_core.messages import HumanMessage, SystemMessage


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
    
    
#para mandar el mensaje a el llm y decirle que solo conteste con base en los documentos y no con su conocimiento
combined_input= f"""Based on the following documents, please answer this question: {query}

Documents:
{chr(10).join([f"-{doc.page_content}" for doc in relevant_docs])}

Please provide a clear, helpful anwer using only the information from these documents. If you can't find the answer in the documents, say "I don't have enough information to answer the question based on the provided documents"
"""
model = ChatOllama(model="llama3.2:3b")

mesages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content= combined_input),
]



result = model.invoke(mesages)


print("\n-----GENERATED RESPONSE-----")
#print("Full result:")
#print(result)
print("COntent only:")
print(result.content)