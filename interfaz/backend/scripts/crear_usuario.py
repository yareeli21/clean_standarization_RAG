from backend.core.db import ejecutar_comando
from backend.core.security import hashear_password

def crear_usuario(usuario: str, password: str):
    ok = ejecutar_comando(
        "INSERT INTO usuarios (usuario, password_hash) VALUES (%s, %s)",
        (usuario, hashear_password(password)),
    )
    print("Usuario creado" if ok else "Falló la creación")

if __name__ == "__main__":
    crear_usuario("admin", "admin123")