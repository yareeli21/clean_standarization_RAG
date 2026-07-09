"""
Router: Login

Responsable de esta pantalla: [asignar integrante]

TODO para quien desarrolle esta pantalla:
- Agregar endpoint POST /login que valide credenciales
- Conectar con la tabla correspondiente en PostgreSQL (o el mecanismo de auth que definan)
- Manejar sesión (cookies / JWT, lo que decidan)
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from backend.core.config import TEMPLATES_DIR

router = APIRouter(tags=["login"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
@router.get("/login", response_class=HTMLResponse)
async def ver_login(request: Request):
    return templates.TemplateResponse(
        request, "pantallas/login/login.html", {"titulo": "Iniciar sesión"}
    )


# TODO: @router.post("/login") -> procesar credenciales y redirigir
