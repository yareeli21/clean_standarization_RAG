"""
Punto de entrada único de la interfaz.

Uso: desde interfaz/, en PowerShell:
    python index.py

Esto levanta el servidor Y abre el navegador automáticamente en
http://127.0.0.1:8000 — no necesitas escribir el comando de uvicorn
ni la URL a mano.
"""
import threading
import webbrowser

import uvicorn

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def abrir_navegador():
    """Espera un momento a que el servidor arranque y abre el navegador."""
    threading.Timer(1.5, lambda: webbrowser.open(URL)).start()


if __name__ == "__main__":
    print(f"Iniciando Aprende RAG en {URL} ...")
    abrir_navegador()
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=False)
