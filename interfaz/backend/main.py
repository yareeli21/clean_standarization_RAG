"""
Entrypoint de la interfaz web (FastAPI + Jinja2).

Para correr en desarrollo, desde interfaz/:
    uvicorn backend.main:app --reload

Luego abre: http://127.0.0.1:8000
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.core.config import STATIC_DIR, NOMBRE_PROYECTO
from backend.routers import login, kpis, instrumentos, chat, cargar




app = FastAPI(title=NOMBRE_PROYECTO)
app.state.nombre_proyecto = NOMBRE_PROYECTO  # disponible para los templates vía request.app.state


# Sirve CSS/JS/imágenes desde /static/...
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Cada integrante desarrolla el suyo; por ahora todos regresan el mockup base.
app.include_router(login.router)
app.include_router(kpis.router)
app.include_router(instrumentos.router)
app.include_router(chat.router)
app.include_router(cargar.router)
