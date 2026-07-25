"""
Router: Cargar instrumento

Dos secciones en esta pantalla:
- Formulario para registrar un instrumento nuevo.
- Consulta de datasets originales (con filtros por tipo y fecha) y de los
  instrumentos que el usuario en sesión ha cargado.
"""
import hashlib
from pathlib import Path

from fastapi import APIRouter, Request, Form, Query, UploadFile, File, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from backend.core.config import TEMPLATES_DIR
from backend.core.db import ejecutar_query, ejecutar_comando
from backend.core.ollama_client import enviar_mensaje_chat
from datetime import datetime
from backend.core.google_drive import subir_archivo, eliminar_archivo, listar_archivos_por_instrumento, descargar_archivo
from psycopg.types.json import Jsonb

router = APIRouter(tags=["cargar"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

CARPETA_CRUDOS = Path("data/crudos")
CARPETA_CRUDOS.mkdir(parents=True, exist_ok=True)

MAPEO_TIPO_A_CARPETA = {
    "Encuesta": "encuestas",
    "Entrevista": "entrevistas",
    "Prueba estandarizada": "pruebas_estandarizadas",
}


MAPEO_CARPETA_A_TIPO_LEGIBLE = {
    "encuestas": "Encuesta",
    "entrevistas": "Entrevista",
    "pruebas_estandarizadas": "Prueba estandarizada",
}

def _obtener_datasets_originales(tipo: str = "todos", fecha: str = "") -> list[dict]:
    # 1. Lo que ya está registrado en TU propia base de datos local
    condiciones = ["ruta_crudo LIKE 'https://%'"]
    parametros: list = []
    if tipo and tipo != "todos":
        condiciones.append("plataforma ILIKE %s")
        parametros.append(f"%{tipo}%")
    if fecha:
        condiciones.append("fecha_procesamiento::date = %s")
        parametros.append(fecha)
    where = f"WHERE {' AND '.join(condiciones)}"

    filas_bd = ejecutar_query(
        f"""
        SELECT id, nombre, plataforma, estado, fecha_procesamiento, id_archivo_drive
        FROM instrumento_procesado
        {where}
        ORDER BY fecha_procesamiento DESC
        """,
        tuple(parametros),
    )
    ids_ya_en_bd = {fila["id_archivo_drive"] for fila in filas_bd if fila["id_archivo_drive"]}

    # 2. Lo que existe en Drive AHORITA (incluye lo de tus compañeros)
    try:
        archivos_por_tipo = listar_archivos_por_instrumento()
    except Exception as e:
        print(f"[aviso] No se pudo listar Drive: {e}")
        archivos_por_tipo = {}

    filas_solo_drive = []
    for carpeta, archivos in archivos_por_tipo.items():
        tipo_legible = MAPEO_CARPETA_A_TIPO_LEGIBLE.get(carpeta, carpeta)
        if tipo and tipo != "todos" and tipo.lower() not in tipo_legible.lower():
            continue
        for archivo in archivos:
            if archivo["id"] in ids_ya_en_bd:
                continue
            fecha_creacion = datetime.fromisoformat(archivo["createdTime"].replace("Z", "+00:00"))
            if fecha and fecha_creacion.strftime("%Y-%m-%d") != fecha:
                continue
            filas_solo_drive.append({
                "id": None,
                "nombre": archivo["name"],
                "plataforma": tipo_legible,
                "estado": "en Drive (subido por otro integrante)",
                "fecha_procesamiento": fecha_creacion,
                "id_archivo_drive": archivo["id"],
            })

    return filas_bd + filas_solo_drive


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


@router.post("/cargar")
async def procesar_carga(
    request: Request,
    nombre: str = Form(...),
    tipo: str = Form(...),
    archivo: UploadFile = File(...),
):
    usuario_id = request.cookies.get("usuario_id")
    contenido = await archivo.read()
    hash_md5 = hashlib.md5(contenido).hexdigest()

    # Verifica ANTES de subir a Drive, para no crear copias huérfanas
    existente = ejecutar_query(
        "SELECT id FROM instrumento_procesado WHERE hash_md5 = %s", (hash_md5,)
    )
    if existente:
        return JSONResponse(
            {"ok": False, "error": "Este archivo ya fue cargado antes."},
            status_code=409,
        )

    ruta_destino = CARPETA_CRUDOS / f"{hash_md5}_{archivo.filename}"
    with open(ruta_destino, "wb") as f:
        f.write(contenido)

    instrumento_drive = MAPEO_TIPO_A_CARPETA.get(tipo)
    id_drive = None
    try:
        resultado_drive = subir_archivo(str(ruta_destino), archivo.filename, instrumento_drive)
        ruta_guardar = resultado_drive["url"]
        id_drive = resultado_drive["id"]
        try:
            ruta_destino.unlink(missing_ok=True)
        except PermissionError:
            print(f"[aviso] No se pudo borrar la copia local (no es grave): {ruta_destino}")
    except Exception as e:
        print(f"[aviso] No se pudo subir a Drive: {e}")
        ruta_guardar = str(ruta_destino)

    filas = ejecutar_query(
        """
        INSERT INTO instrumento_procesado (nombre, plataforma, ruta_crudo, id_archivo_drive, hash_md5, estado, usuario_id)
        VALUES (%s, %s, %s, %s, %s, 'ingresado', %s)
        ON CONFLICT (hash_md5) DO NOTHING
        RETURNING id
        """,
        (nombre, tipo, ruta_guardar, id_drive, hash_md5, usuario_id),
    )

    if not filas:
        return JSONResponse({"ok": False, "error": "No se pudo cargar (¿ya existe?)."}, status_code=409)

    return JSONResponse({"ok": True, "instrumento_id": filas[0]["id"]})

@router.post("/cargar/{instrumento_id}/metadatos/chat")
async def chat_metadatos(instrumento_id: int, historial: list[dict] = Body(...)):
    """Reenvía el turno de conversación a Ollama y regresa la respuesta."""
    try:
        respuesta = enviar_mensaje_chat(historial)
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"No se pudo contactar al modelo: {e}"}, status_code=502)
    return JSONResponse({"ok": True, "respuesta": respuesta})


@router.post("/cargar/{instrumento_id}/metadatos")
async def guardar_metadatos(instrumento_id: int, cuerpo: dict = Body(...)):
    """
    Guarda la transcripción del chat (o null si se omitió) asociada
    al instrumento. No modifica el crudo en Drive.
    """
    historial = cuerpo.get("historial")  # None si el usuario omitió
    ejecutar_comando(
        "UPDATE instrumento_procesado SET metadatos = %s WHERE id = %s",
        (Jsonb(historial) if historial else None, instrumento_id),
    )
    return JSONResponse({"ok": True})


@router.delete("/cargar/{instrumento_id}")
async def eliminar_instrumento(request: Request, instrumento_id: int):
    """Elimina un instrumento propio: de Drive y de la base de datos."""
    usuario_id = request.cookies.get("usuario_id")

    filas = ejecutar_query(
        "SELECT id_archivo_drive FROM instrumento_procesado WHERE id = %s AND usuario_id = %s",
        (instrumento_id, usuario_id),
    )
    if not filas:
        return JSONResponse({"ok": False, "error": "No encontrado."}, status_code=404)

    id_drive = filas[0]["id_archivo_drive"]
    if id_drive:
        try:
            eliminar_archivo(id_drive)
        except Exception as e:
            print(f"[aviso] No se pudo eliminar de Drive: {e}")

    ejecutar_comando(
        "DELETE FROM instrumento_procesado WHERE id = %s AND usuario_id = %s",
        (instrumento_id, usuario_id),
    )
    return JSONResponse({"ok": True})

@router.get("/cargar/preview/{drive_id}")
async def previsualizar_archivo(drive_id: str):
    """
    Descarga el archivo de Drive en memoria y lo regresa como tabla HTML
    si es CSV, o como texto plano para otros formatos simples.
    """
    try:
        contenido = descargar_archivo(drive_id)
    except Exception as e:
        return HTMLResponse(f"<p style='padding:2rem;'>No se pudo obtener el archivo: {e}</p>")

    try:
        texto = contenido.decode("utf-8")
    except UnicodeDecodeError:
        return HTMLResponse("<p style='padding:2rem;'>Este archivo no se puede previsualizar como texto (¿es binario?).</p>")

    import csv
    import io as io_module

    filas = list(csv.reader(io_module.StringIO(texto)))
    if not filas:
        return HTMLResponse("<p style='padding:2rem;'>El archivo está vacío.</p>")

    encabezado, *datos = filas
    html = "<table style='width:100%; border-collapse:collapse; font-size:0.85rem;'>"
    html += "<tr>" + "".join(f"<th style='border:1px solid #ccc; padding:6px; background:#f0f0f0; text-align:left;'>{c}</th>" for c in encabezado) + "</tr>"
    for fila in datos[:500]:  # límite de 500 filas para no tronar el navegador
        html += "<tr>" + "".join(f"<td style='border:1px solid #ccc; padding:6px;'>{c}</td>" for c in fila) + "</tr>"
    html += "</table>"
    if len(datos) > 500:
        html += f"<p style='padding:1rem; opacity:0.7;'>Mostrando las primeras 500 de {len(datos)} filas.</p>"

    return HTMLResponse(html)