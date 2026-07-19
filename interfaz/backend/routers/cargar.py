"""
Router: Cargar instrumento

Dos secciones en esta pantalla:
- Formulario para registrar un instrumento nuevo.
- Consulta de datasets originales (con filtros por tipo y fecha) y de los
  instrumentos que el usuario en sesión ha cargado.
"""
import hashlib
from pathlib import Path

from fastapi import APIRouter, Request, Form, Query, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from backend.core.config import TEMPLATES_DIR
from backend.core.db import ejecutar_query, ejecutar_comando

router = APIRouter(tags=["cargar"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

CARPETA_CRUDOS = Path("data/crudos")
CARPETA_CRUDOS.mkdir(parents=True, exist_ok=True)


def _obtener_datasets_originales(tipo: str = "todos", fecha: str = "") -> list[dict]:
    condiciones = []
    parametros: list = []

    if tipo and tipo != "todos":
        condiciones.append("plataforma ILIKE %s")
        parametros.append(f"%{tipo}%")

    if fecha:
        condiciones.append("fecha_procesamiento::date = %s")
        parametros.append(fecha)

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    return ejecutar_query(
        f"""
        SELECT id, nombre, plataforma, estado, fecha_procesamiento
        FROM instrumento_procesado
        {where}
        ORDER BY fecha_procesamiento DESC
        """,
        tuple(parametros) if parametros else None,
    )


def _obtener_mis_instrumentos(usuario_id: str | None) -> list[dict]:
    if not usuario_id:
        return []
    return ejecutar_query(
        """
        SELECT id, nombre, plataforma, estado, fecha_procesamiento
        FROM instrumento_procesado
        WHERE usuario_id = %s
        ORDER BY fecha_procesamiento DESC
        """,
        (usuario_id,),
    )


@router.get("/cargar", response_class=HTMLResponse)
async def ver_formulario_carga(request: Request):
    usuario_id = request.cookies.get("usuario_id")
    return templates.TemplateResponse(
        request,
        "pantallas/cargar_instrumento/cargar_instrumento.html",
        {
            "titulo": "Cargar instrumento",
            "datasets_originales": _obtener_datasets_originales(),
            "mis_instrumentos": _obtener_mis_instrumentos(usuario_id),
        },
    )


@router.get("/cargar/datasets", response_class=HTMLResponse)
async def filtrar_datasets(
    request: Request,
    tipo: str = Query("todos"),
    fecha: str = Query(""),
):
    """Devuelve solo el fragmento de datasets originales filtrados, para fetch."""
    return templates.TemplateResponse(
        request,
        "pantallas/cargar_instrumento/_datasets_originales.html",
        {"datasets_originales": _obtener_datasets_originales(tipo, fecha)},
    )


@router.post("/cargar", response_class=HTMLResponse)
async def procesar_carga(
    request: Request,
    nombre: str = Form(...),
    tipo: str = Form(...),
    archivo: UploadFile = File(...),
):
    usuario_id = request.cookies.get("usuario_id")
    contenido = await archivo.read()
    hash_md5 = hashlib.md5(contenido).hexdigest()

    ruta_destino = CARPETA_CRUDOS / f"{hash_md5}_{archivo.filename}"
    with open(ruta_destino, "wb") as f:
        f.write(contenido)

    ok = ejecutar_comando(
        """
        INSERT INTO instrumento_procesado (nombre, plataforma, ruta_crudo, hash_md5, estado, usuario_id)
        VALUES (%s, %s, %s, %s, 'ingresado', %s)
        ON CONFLICT (hash_md5) DO NOTHING
        """,
        (nombre, tipo, str(ruta_destino), hash_md5, usuario_id),
    )

    mensaje = "Instrumento cargado correctamente." if ok else "No se pudo cargar el instrumento (¿ya existe?)."
    return templates.TemplateResponse(
        request,
        "pantallas/cargar_instrumento/cargar_instrumento.html",
        {
            "titulo": "Cargar instrumento",
            "mensaje": mensaje,
            "ok": ok,
            "datasets_originales": _obtener_datasets_originales(),
            "mis_instrumentos": _obtener_mis_instrumentos(usuario_id),
        },
    )