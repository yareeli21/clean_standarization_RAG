import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "aprende_rag"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


def obtener_conexion():
    """Regresa una conexion nueva a PostgreSQL."""
    return psycopg.connect(**DB_CONFIG, row_factory=dict_row)


def ejecutar_query(query: str, parametros: tuple = None) -> list[dict]:
    """
    Ejecuta un SELECT y regresa una lista de dicts.
    Si la base de datos aun no existe, no esta corriendo, o la tabla esta
    vacia, regresa una lista vacia [] en vez de tronar.
    """
    try:
        with psycopg.connect(**DB_CONFIG, row_factory=dict_row) as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(query, parametros)
                filas = cursor.fetchall()
                return [dict(fila) for fila in filas]
    except psycopg.Error as error:
        print(f"[aviso] No se pudo consultar la BD todavia: {error}")
        return []


def ejecutar_comando(query: str, parametros: tuple = None) -> bool:
    """Ejecuta un INSERT/UPDATE/DELETE. Regresa True si se ejecuto bien."""
    try:
        with psycopg.connect(**DB_CONFIG) as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(query, parametros)
        return True
    except psycopg.Error as error:
        print(f"[aviso] No se pudo ejecutar el comando: {error}")
        return False