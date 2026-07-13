"""
Router: Catálogo de instrumentos
Responsable de esta pantalla: Yare
"""
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from backend.core.config import TEMPLATES_DIR
from backend.core.db import ejecutar_query

router = APIRouter(tags=["instrumentos"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Mapeo de estado real (columna `estado` en instrumento_procesado) -> clase CSS
ESTADOS_SLUG = {
    "ingresado": "ingresado",
    "limpio": "limpio",
    "estandarizado": "estandarizado",
    "vectorizado": "vectorizado",
}


def _preparar_instrumentos(filas: list[dict]) -> list[dict]:
    """Agrega campos derivados (slug de tipo, slug de estado, código de catálogo)."""
    prefijos = {"encuesta": "ENC", "entrevista": "ENT", "prueba estandarizada": "PRB"}
    resultado = []
    for i, fila in enumerate(filas, start=1):
        tipo = fila.get("plataforma") or fila.get("tipo", "instrumento")
        tipo_normalizado = tipo.lower()
        prefijo = next((v for k, v in prefijos.items() if k in tipo_normalizado), "INS")
        resultado.append({
            **fila,
            "tipo": tipo,
            "tipo_slug": tipo_normalizado.replace(" ", "-"),
            "estado_slug": ESTADOS_SLUG.get(fila.get("estado", ""), "ingresado"),
            "codigo": f"{prefijo}·{i:03d}",
        })
    return resultado


def _obtener_instrumentos(tipo: str | None = None) -> list[dict]:
    if tipo and tipo != "todos":
        filas = ejecutar_query(
            """
            SELECT nombre, plataforma, estado, fecha_procesamiento
            FROM instrumento_procesado
            WHERE plataforma ILIKE %s
            ORDER BY fecha_procesamiento DESC
            """,
            (f"%{tipo}%",),
        )
    else:
        filas = ejecutar_query(
            """
            SELECT nombre, plataforma, estado, fecha_procesamiento
            FROM instrumento_procesado
            ORDER BY fecha_procesamiento DESC
            """
        )
    return _preparar_instrumentos(filas)


@router.get("/instrumentos", response_class=HTMLResponse)
async def ver_catalogo_instrumentos(request: Request):
    instrumentos = _obtener_instrumentos()
    return templates.TemplateResponse(
        request,
        "pantallas/catalogo_instrumentos/catalogo_instrumentos.html",
        {"titulo": "Catálogo de instrumentos", "instrumentos": instrumentos},
    )


@router.get("/instrumentos/buscar", response_class=HTMLResponse)
async def buscar_instrumentos(request: Request, tipo: str = Query("todos")):
    """Devuelve solo el fragmento de la rejilla, para reemplazar vía fetch."""
    instrumentos = _obtener_instrumentos(tipo)
    return templates.TemplateResponse(
        request,
        "pantallas/catalogo_instrumentos/_rejilla_instrumentos.html",
        {"instrumentos": instrumentos},
    )