"""
Router: Chat de IA (consulta RAG)

Responsable de esta pantalla: [asignar integrante — probablemente Yare, dado su trabajo en RAG]

TODO para quien desarrolle esta pantalla:
- Implementar POST /chat/consultar que reciba {pregunta, instrumento}
- Llamar a backend.rag_backend.rag_service para obtener la respuesta
- Registrar la interacción en la tabla `rag_log` (PostgreSQL)
- Decidir si la respuesta se renderiza server-side o vía fetch + JS (recomendado: fetch)
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from backend.core.config import TEMPLATES_DIR

router = APIRouter(tags=["chat"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


class ConsultaRequest(BaseModel):
    pregunta: str
    instrumento: str  # "encuestas" | "entrevistas" | "pruebas_estandarizadas"


@router.get("/chat", response_class=HTMLResponse)
async def ver_chat_ia(request: Request):
    return templates.TemplateResponse(
        request, "pantallas/chat_ia/chat_ia.html", {"titulo": "Chat de IA"}
    )


@router.post("/chat/consultar")
async def consultar_rag(datos: ConsultaRequest):
    # TODO: reemplazar por llamada real a rag_backend.rag_service.consultar(...)
    return {
        "respuesta": f"[MOCKUP] Aquí iría la respuesta del RAG para: '{datos.pregunta}' "
                      f"sobre el instrumento '{datos.instrumento}'.",
        "chunks_recuperados": [],
    }
