"""
Conexión a Google Drive vía OAuth de usuario (NO cuenta de servicio).

Por qué el cambio: las cuentas de servicio no tienen cuota de
almacenamiento propia en una cuenta de Gmail personal/gratuita — solo
funcionan para crear archivos en "Unidades compartidas" (Shared Drives),
que es una función exclusiva de Google Workspace de pago. Como la cuenta
del equipo es una cuenta de Gmail normal, usamos OAuth: la PRIMERA vez que
alguien sube un archivo, se abre el navegador pidiendo iniciar sesión con
la cuenta compartida del equipo. Después de esa vez, queda guardado un
"token" (token.json) que reutiliza esa sesión automáticamente — nadie
vuelve a tener que iniciar sesión de nuevo, a menos que se borre ese archivo.

Requiere:
1. `oauth_credentials.json` (descargado de Google Cloud Console, tipo
   "Aplicación de escritorio") en backend/core/ — NUNCA subir a git.
2. La primera vez que se use, correr esto de forma interactiva (con
   ventana de navegador disponible) para generar token.json.
"""
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CARPETA_CORE = Path(__file__).parent
OAUTH_CREDENCIALES_PATH = CARPETA_CORE / "oauth_credentials.json"
TOKEN_PATH = CARPETA_CORE / "token.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

CARPETAS_POR_INSTRUMENTO = {
    "encuestas": os.getenv("GOOGLE_DRIVE_FOLDER_ENCUESTAS", ""),
    "entrevistas": os.getenv("GOOGLE_DRIVE_FOLDER_ENTREVISTAS", ""),
    "pruebas_estandarizadas": os.getenv("GOOGLE_DRIVE_FOLDER_PRUEBAS", ""),
}


def _obtener_credenciales():
    """
    Regresa credenciales válidas, reutilizando token.json si ya existe,
    o abriendo el navegador para iniciar sesión si es la primera vez
    (o si el token expiró y no se pudo refrescar solo).
    """
    credenciales = None

    if TOKEN_PATH.exists():
        credenciales = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not credenciales or not credenciales.valid:
        if credenciales and credenciales.expired and credenciales.refresh_token:
            credenciales.refresh(Request())
        else:
            if not OAUTH_CREDENCIALES_PATH.exists():
                raise FileNotFoundError(
                    "No se encontró oauth_credentials.json en backend/core/. "
                    "Descárgalo desde Google Cloud Console (ver README)."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(OAUTH_CREDENCIALES_PATH), SCOPES
            )
            # Abre el navegador para que inicies sesión — solo pasa la primera vez
            credenciales = flow.run_local_server(port=0)

        TOKEN_PATH.write_text(credenciales.to_json())

    return credenciales


def _obtener_servicio():
    credenciales = _obtener_credenciales()
    return build("drive", "v3", credentials=credenciales)


def subir_archivo(ruta_local: str, nombre_archivo: str, instrumento: str) -> dict:
    """
    Sube un archivo a la subcarpeta de Drive correspondiente al tipo de
    instrumento ("encuestas" | "entrevistas" | "pruebas_estandarizadas").
    """
    if instrumento not in CARPETAS_POR_INSTRUMENTO:
        raise ValueError(
            f"Instrumento '{instrumento}' no reconocido. "
            f"Debe ser uno de: {list(CARPETAS_POR_INSTRUMENTO.keys())}"
        )

    carpeta_id = CARPETAS_POR_INSTRUMENTO[instrumento]
    if not carpeta_id:
        raise ValueError(
            f"Falta configurar el ID de carpeta para '{instrumento}' en tu .env"
        )

    servicio = _obtener_servicio()

    metadata_archivo = {
        "name": nombre_archivo,
        "parents": [carpeta_id],
    }
    media = MediaFileUpload(ruta_local, resumable=True)

    archivo_subido = servicio.files().create(
        body=metadata_archivo,
        media_body=media,
        fields="id, name, webViewLink",
    ).execute()

    return {
        "id": archivo_subido["id"],
        "nombre": archivo_subido["name"],
        "url": archivo_subido["webViewLink"],
    }


def listar_archivos_por_instrumento() -> dict:
    """
    Lista los archivos que existen AHORITA en cada subcarpeta de Drive,
    sin depender de PostgreSQL. Útil para que todo el equipo vea lo que
    hay en Drive aunque no lo hayan subido ellos mismos (cada quien tiene
    su propia base de datos local, pero Drive sí es compartido de verdad).
    """
    servicio = _obtener_servicio()
    resultado = {}
    for instrumento, carpeta_id in CARPETAS_POR_INSTRUMENTO.items():
        if not carpeta_id:
            resultado[instrumento] = []
            continue
        respuesta = servicio.files().list(
            q=f"'{carpeta_id}' in parents and trashed = false",
            fields="files(id, name, webViewLink, createdTime)",
            orderBy="createdTime desc",
        ).execute()
        resultado[instrumento] = respuesta.get("files", [])
    return resultado


def eliminar_archivo(archivo_id: str) -> None:
    """Elimina permanentemente un archivo de Drive por su ID."""
    servicio = _obtener_servicio()
    servicio.files().delete(fileId=archivo_id).execute()

def descargar_archivo(archivo_id: str) -> bytes:
    """
    Descarga el contenido de un archivo de Drive en memoria (no lo guarda
    en disco). Útil para generar una vista previa sin depender del widget
    nativo de Drive, que a veces falla con CSVs subidos por API.
    """
    import io
    from googleapiclient.http import MediaIoBaseDownload

    servicio = _obtener_servicio()
    solicitud = servicio.files().get_media(fileId=archivo_id)
    buffer = io.BytesIO()
    descargador = MediaIoBaseDownload(buffer, solicitud)
    listo = False
    while not listo:
        _, listo = descargador.next_chunk()
    return buffer.getvalue()