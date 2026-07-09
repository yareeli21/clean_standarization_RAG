"""
Router: Catálogo de KPIs

Responsable de esta pantalla: [asignar integrante]

Ya conectado a PostgreSQL de verdad: consulta la tabla `kpi`.
Si la tabla todavía no tiene registros (o la BD ni siquiera está corriendo
todavía), la pantalla muestra un estado vacío en vez de tronar. En cuanto
existan filas en `kpi`, solo hay que volver a correr el proyecto
(python index.py) y aparecerán solas — no se necesita tocar este código.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from backend.core.config import TEMPLATES_DIR
from backend.core.db import ejecutar_query

router = APIRouter(tags=["kpis"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/kpis", response_class=HTMLResponse)
async def ver_catalogo_kpis(request: Request):
    kpis = ejecutar_query(
        """
        SELECT nombre, instrumento, descripcion
        FROM kpi
        ORDER BY nombre;
        """
    )
    return templates.TemplateResponse(
        request,
        "pantallas/catalogo_kpis/catalogo_kpis.html",
        {"titulo": "Catálogo de KPIs", "kpis": kpis},
    )
