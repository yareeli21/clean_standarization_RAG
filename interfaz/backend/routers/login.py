"""
Router: Login
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.core.config import TEMPLATES_DIR
from backend.core.db import ejecutar_query
from backend.core.security import verificar_password

router = APIRouter(tags=["login"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
@router.get("/login", response_class=HTMLResponse)
async def ver_login(request: Request):
    return templates.TemplateResponse(
        request, "pantallas/login/login.html", {"titulo": "Iniciar sesión"}
    )


@router.post("/login", response_class=HTMLResponse)
async def procesar_login(
    request: Request,
    usuario: str = Form(...),
    password: str = Form(...),
):
    filas = ejecutar_query(
        "SELECT id, usuario, password_hash FROM usuarios WHERE usuario = %s",
        (usuario,),
    )

    if not filas or not verificar_password(password, filas[0]["password_hash"]):
        return templates.TemplateResponse(
            request,
            "pantallas/login/login.html",
            {"titulo": "Iniciar sesión", "error": "Usuario o contraseña incorrectos"},
        )

    fila = filas[0]
    response = RedirectResponse(url="/kpis", status_code=303)  # <-- este es el único cambio
    response.set_cookie(
        key="usuario_id",
        value=str(fila["id"]),
        httponly=True,
        max_age=3600,
        samesite="lax",
    )
    return response