import mysql.connector
from connection import obtener_conexion

def crear_tablas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        sql_productos = """
        CREATE TABLE IF NOT EXISTS PRODUCTOS (
            id int auto_increment primary key,
            nombre varchar(100) not null,
            precio_costo decimal(10,2) not null,
            cantidad int not null
        )"""

        sql_ventas = """
        CREATE TABLE IF NOT EXISTS VENTAS (
            id int auto_increment primary key,
            fecha datetime default current_timestamp,
            total_venta decimal(10,2) default 0.00
        )"""

        sql_detalles_ventas = """
        CREATE TABLE IF NOT EXISTS DETALLES_VENTAS (
            id int auto_increment primary key,
            venta_id int not null,
            producto_id int not null,
            cantidad int not null,
            precio_costo decimal(10,2) not null,
            precio_venta decimal(10,2) not null,
            precio_venta_total decimal(10,2) not null,
            foreign key (venta_id) references VENTAS(id) ON DELETE CASCADE,
            foreign key (producto_id) references PRODUCTOS(id)
        )"""

        cursor.execute(sql_productos)
        conexion.commit()
        cursor.execute(sql_ventas)
        conexion.commit()
        cursor.execute(sql_detalles_ventas)
        conexion.commit()
    except mysql.connector.Error as err:
        raise Exception(f"Error al crear las tablas: {err}")
    finally:
        cursor.close()
        conexion.close()