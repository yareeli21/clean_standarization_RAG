"""
Router: Catálogo de instrumentos

Responsable de esta pantalla: [asignar integrante]

TODO para quien desarrolle esta pantalla:
- Consultar la tabla `instrumento_procesado` en PostgreSQL
- Mostrar metadata Dublin Core (título, tipo, fecha de procesamiento, etc.)
- Enlazar cada instrumento con sus KPIs asociados (join con `pregunta_kpi`)
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from backend.core.config import TEMPLATES_DIR

router = APIRouter(tags=["instrumentos"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Datos de ejemplo (mockup) — reemplazar por consulta real a PostgreSQL
INSTRUMENTOS_EJEMPLO = [
    {"nombre": "Encuesta de clima escolar 2025", "tipo": "Encuesta", "estado": "Procesado"},
    {"nombre": "Entrevista docentes - ciclo 2", "tipo": "Entrevista", "estado": "Procesado"},
    {"nombre": "Prueba diagnóstica matemáticas", "tipo": "Prueba estandarizada", "estado": "Pendiente"},
]


@router.get("/instrumentos", response_class=HTMLResponse)
async def ver_catalogo_instrumentos(request: Request):
    return templates.TemplateResponse(
        request,
        "pantallas/catalogo_instrumentos/catalogo_instrumentos.html",
        {"titulo": "Catálogo de instrumentos", "instrumentos": INSTRUMENTOS_EJEMPLO},
    )
