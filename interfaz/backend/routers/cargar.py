"""
Router: Cargar instrumento
Responsable de esta pantalla: [asignar integrante]

Permite registrar un instrumento nuevo en `instrumento_procesado`.
Por ahora solo guarda los metadatos básicos (nombre, plataforma, ruta del
archivo crudo) — el pipeline real de limpieza/estandarización se conecta
después, actualizando el campo `estado` conforme avance.
"""
import hashlib
import shutil
from pathlib import Path

from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.core.config import TEMPLATES_DIR
from backend.core.db import ejecutar_comando

router = APIRouter(tags=["cargar"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

CARPETA_CRUDOS = Path("data/crudos")
CARPETA_CRUDOS.mkdir(parents=True, exist_ok=True)


@router.get("/cargar", response_class=HTMLResponse)
async def ver_formulario_carga(request: Request):
    return templates.TemplateResponse(
        request,
        "pantallas/cargar_instrumento/cargar_instrumento.html",
        {"titulo": "Cargar instrumento"},
    )


@router.post("/cargar", response_class=HTMLResponse)
async def procesar_carga(
    request: Request,
    nombre: str = Form(...),
    tipo: str = Form(...),
    archivo: UploadFile = File(...),
):
    contenido = await archivo.read()
    hash_md5 = hashlib.md5(contenido).hexdigest()

    ruta_destino = CARPETA_CRUDOS / f"{hash_md5}_{archivo.filename}"
    with open(ruta_destino, "wb") as f:
        f.write(contenido)

    ok = ejecutar_comando(
        """
        INSERT INTO instrumento_procesado (nombre, plataforma, ruta_crudo, hash_md5, estado)
        VALUES (%s, %s, %s, %s, 'ingresado')
        ON CONFLICT (hash_md5) DO NOTHING
        """,
        (nombre, tipo, str(ruta_destino), hash_md5),
    )

    mensaje = "Instrumento cargado correctamente." if ok else "No se pudo cargar el instrumento (¿ya existe?)."
    return templates.TemplateResponse(
        request,
        "pantallas/cargar_instrumento/cargar_instrumento.html",
        {"titulo": "Cargar instrumento", "mensaje": mensaje, "ok": ok},
    )