"""
Cliente mínimo para el chat de captura de metadatos.

El modelo (Mistral 7B o Llama, aún sin decidir cuál) se coordina por
variable de entorno para no acoplar el código a una ubicación fija de
Ollama — útil mientras no se decide si corre en el host o en el mismo
docker-compose.
"""
import os
import requests

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

SYSTEM_PROMPT = """Eres un asistente que ayuda a un investigador a describir
un instrumento educativo (encuesta, entrevista o prueba estandarizada) que
acaba de subir al sistema. Tu tarea es hacer preguntas breves, una a la vez,
para entender el contexto del instrumento: qué mide, a quién se aplicó,
cuándo, y cualquier detalle relevante para su documentación. No inventes
categorías fijas de metadatos — simplemente conversa de forma natural y
breve. Si el investigador indica que quiere terminar o no sabe una
respuesta, respétalo y no insistas."""


def enviar_mensaje_chat(historial: list[dict]) -> str:
    """
    historial: lista de mensajes [{"role": "user"|"assistant", "content": "..."}]
    (sin incluir el system prompt, se antepone aquí).
    Regresa el texto de la respuesta del modelo.
    """
    mensajes = [{"role": "system", "content": SYSTEM_PROMPT}] + historial

    respuesta = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={"model": OLLAMA_MODEL, "messages": mensajes, "stream": False},
        timeout=60,
    )
    respuesta.raise_for_status()
    return respuesta.json()["message"]["content"]