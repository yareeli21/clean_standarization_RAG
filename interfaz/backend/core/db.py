"""
Conexión a PostgreSQL.

Ajusta los valores de conexión aquí (o mejor, en un archivo .env — ver abajo).
Este módulo se reutiliza desde cualquier router que necesite consultar la BD.
"""
import os
import psycopg2
import psycopg2.extras

# TODO: mover estos valores a un archivo .env y leerlos con python-dotenv,
# en vez de dejarlos escritos aquí (por seguridad, sobre todo la contraseña).
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "aprende_rag"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


def obtener_conexion():
    """Regresa una conexión nueva a PostgreSQL."""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=psycopg2.extras.RealDictCursor)


def ejecutar_query(query: str, parametros: tuple = None) -> list[dict]:
    """
    Ejecuta un SELECT y regresa una lista de dicts.

    Si la base de datos aún no existe, no está corriendo, o la tabla está
    vacía, regresa una lista vacía [] en vez de tronar — así la pantalla
    simplemente muestra "sin datos" hasta que la información exista de verdad.
    """
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
        try:
            conexion.close()
        except Exception:
            pass
