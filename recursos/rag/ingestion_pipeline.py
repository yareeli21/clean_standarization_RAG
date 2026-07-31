import os 
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_chroma import Chroma
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM, OllamaEmbeddings

load_dotenv()


llm = OllamaLLM(model="llama3.2:1b")


def load_documents(docs_path):#direccion donde deberian de estar todos los archivos del usuario 
    
    """_summary_
    """
    print(f"Loading documents from {docs_path}")
    
    #primero ver si existe el path
    if not os.path.exists(docs_path):
        raise FileNotFoundError(f"El directorio {docs_path} no existe. Porfavor crealo y añade tus documentos")   
    
    
    #carga todos los archivos .txt del directiorio
    loader = DirectoryLoader(
        path=docs_path,
        glob="*.txt", #osea todos los archivos txt
        loader_cls=lambda path: TextLoader(path, encoding="utf-8", autodetect_encoding=True)
    )
    documents = loader.load()
    
    if len(documents)== 0:
        raise FileNotFoundError(f"No .txt files found in {docs_path}. Please add your company documents.")
    
    for i, doc in enumerate(documents[:2]):
        print(f"\nDocument {i+1}")
        print(f"  Source: {doc.metadata['source']}")
        print(f"  Content length: {len(doc.page_content)} characters")
        print(f"  Content preview: {doc.page_content[:100]}...")
        print(f"  Metadata: {doc.metadata}")
    
    return documents
    
    
def split_documents(documents, chunk_size=800, chunk_overlap =0):
    
    """split the documents into smaller chunks with overlap
    """
    print("splitting documents into chuncks")
    
    text_splitter =CharacterTextSplitter(
        chunk_size= chunk_size,
        chunk_overlap= chunk_overlap
    )
    
    chunks = text_splitter.split_documents(documents)
    
    if chunks:
        
        for i, chunk in enumerate(chunks[:5]):
            print(f"\n --- Chunk {i+1} --- ")
            print(f"Source: {chunk.metadata['source' ]}")
            print(f"Length: {len(chunk.page_content)} characters")
            print(f"Content:")
            print(chunk.page_content)
            print("-" * 50)  
        
        if len(chunks)< 5: 
            print(f"\n... and {len(chunks) - 5} more chunks")
            
    return chunks 
    

def create_vector_store(chunks, perisist_directory="db/chroma_Db"):
    
    """create and persist chroma db vector store
    """
    print("Creating embeddings and storing in ChromaDB...")

    embedding_model = OllamaEmbeddings(model="nomic-embed-text:latest")
    
    print("--Creating vector store---")
    vector_store = Chroma.from_documents(
        documents= chunks,
        embedding= embedding_model,
        persist_directory= perisist_directory,
        collection_metadata={"hhsw:space":"cosine"}#el algoritmo para la similitud
    )
    
    print("---Finished creating vector store---")
    print(f"Vector store created and saved to {perisist_directory}")
    return vector_store

    
def main():
    
    print("Main function")
    
    #1.- cargar los documentos
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    docs_path = os.path.join(project_root, "instrumentos")
    chroma_persist_directory = os.path.join(project_root, "datos")

    if docs_path is None:
        raise FileNotFoundError(f"No se encontró ninguna carpeta de documentos en {project_root}")

    documents = load_documents(docs_path)
    
    #Chunking the documents
    chunks = split_documents(documents)
    
    # EMBEDDINGS
    
    vector_store = create_vector_store(chunks, perisist_directory= chroma_persist_directory)
    
    
    


if __name__ == "__main__":
    main()
