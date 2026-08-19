import mysql.connector
from conection import obtener_conexion

def crear_tablas():
    conexion = obtener_conexion()
    if conexion is None:
        return False

    cursor = conexion.cursor()
    try:
        # SE ELIMINÓ EL CAMPO "precio" DE ESTA TABLA
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
        print("Tabla PRODUCTOS validada.")
        conexion.commit()

        cursor.execute(sql_ventas)
        print("Tabla VENTAS validada.")
        conexion.commit()

        cursor.execute(sql_detalles_ventas)
        print("Tabla DETALLES_VENTAS validada.")
        conexion.commit()
        return True

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False
    finally:
        cursor.close()
        conexion.close()
