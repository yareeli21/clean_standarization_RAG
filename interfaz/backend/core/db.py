"""
Conexión a PostgreSQL.

Ajusta los valores de conexión aquí (o mejor, en un archivo .env — ver abajo).
Este módulo se reutiliza desde cualquier router que necesite consultar la BD.
"""
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "postgres_lay"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "Lucassini11"),
}


def obtener_conexion():
    """Regresa una conexión nueva a PostgreSQL."""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=psycopg2.extras.RealDictCursor)


def ejecutar_query(query: str, parametros: tuple = None) -> list[dict]:
    """
    Ejecuta un SELECT y regresa una lista de dicts.
    Si algo falla, regresa [] en vez de tronar.
    """
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion:
            with conexion.cursor() as cursor:
                cursor.execute(query, parametros)
                filas = cursor.fetchall()
                return [dict(fila) for fila in filas]
    except psycopg2.Error as error:
        print(f"[aviso] No se pudo consultar la BD todavía: {error}")
        return []
    finally:
        if conexion:
            conexion.close()


def ejecutar_comando(query: str, parametros: tuple = None) -> bool:
    """
    Ejecuta un INSERT/UPDATE/DELETE. Regresa True si se ejecutó bien.
    """
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion:
            with conexion.cursor() as cursor:
                cursor.execute(query, parametros)
        return True
    except psycopg2.Error as error:
        print(f"[aviso] No se pudo ejecutar el comando: {error}")
        return False
    finally:
        if conexion:
            conexion.close()