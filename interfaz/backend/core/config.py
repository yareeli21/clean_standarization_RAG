"""
Configuración central de la interfaz.
Aquí se definen rutas base y settings que consumen main.py y los routers.
"""
from pathlib import Path

# Raíz de interfaz/ (sube 2 niveles desde este archivo: core/ -> backend/ -> interfaz/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
STATIC_DIR = BASE_DIR / "frontend" / "static"

# Nombre que aparece en el nav / título de pestaña
NOMBRE_PROYECTO = "INDAGATA"

# Nombres de las 3 colecciones de ChromaDB (referencia para rag_backend)
COLECCIONES_CHROMA = {
    "encuestas": "col_encuestas",
    "entrevistas": "col_entrevistas",
    "pruebas_estandarizadas": "col_pruebas_estandarizadas",
}
