"""
Lógica central del RAG: conexión a ChromaDB + embeddings + LLM (Ollama).

TODO:
- Cargar modelo de embeddings: paraphrase-multilingual-mpnet-base-v2
- Conectar a ChromaDB embebido (persist_directory apuntando a datos/chroma)
- Función consultar(pregunta: str, instrumento: str, top_k: int = 5) -> dict
    1. Genera embedding de la pregunta
    2. Busca en la colección correspondiente (col_encuestas / col_entrevistas / col_pruebas_estandarizadas)
    3. Arma el prompt con los chunks recuperados
    4. Llama a Ollama (mistral:latest recomendado, según pruebas previas)
    5. Regresa {respuesta, chunks_recuperados, metadata}
"""

# Import de ejemplo para cuando se implemente:
# import chromadb
# from sentence_transformers import SentenceTransformer

def consultar(pregunta: str, instrumento: str, top_k: int = 5) -> dict:
    raise NotImplementedError("Implementar conexión real a ChromaDB + Ollama")
