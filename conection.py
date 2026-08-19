import mysql.connector
from mysql.connector import errorcode

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "database",
}

def obtener_conexion():
    """Devuelve una conexión activa a MySQL o lanza una excepción con un mensaje claro."""
    try:
        conexion = mysql.connector.connect(use_pure=True, **DB_CONFIG)
        return conexion
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            raise Exception("Algo está mal con tu usuario o contraseña de MySQL.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            raise Exception("La base de datos no existe.")
        else:
            raise Exception(f"Error al conectar a la base de datos: {err}")