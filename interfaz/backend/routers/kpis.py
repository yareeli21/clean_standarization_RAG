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
        SELECT  id, nombre, descripcion, objetivo, razon 
        FROM kpi
        ORDER BY nombre;
        """
    )
    return templates.TemplateResponse(
        request,
        "pantallas/catalogo_kpis/catalogo_kpis.html",
        {"titulo": "Catálogo de KPIs", "kpis": kpis},
    )
    

initial_statistics = [0 for i in range(7)]

numero_de_estudiantes = ejecutar_query(
    
    """ 
    SELECT 
    """

)