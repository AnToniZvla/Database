import os
from datetime import datetime
import mysql.connector
from fpdf import FPDF
from conection import obtener_conexion


# ==========================================================================================
# LÓGICA DE NEGOCIO - PRODUCTOS
# ==========================================================================================

def obtener_productos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT id, nombre, precio_costo, cantidad FROM productos ORDER BY id")
        return cursor.fetchall()
    except mysql.connector.Error as err:
        raise Exception(f"Error al obtener los productos: {err}")
    finally:
        cursor.close()
        conexion.close()


def obtener_producto(producto_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "SELECT id, nombre, precio_costo, cantidad FROM productos WHERE id = %s",
            (producto_id,),
        )
        return cursor.fetchone()
    except mysql.connector.Error as err:
        raise Exception(f"Error al obtener el producto: {err}")
    finally:
        cursor.close()
        conexion.close()


def insertar_producto(nombre, precio_costo, cantidad):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        sql = "INSERT INTO productos (nombre, precio_costo, cantidad) VALUES (%s, %s, %s)"
        cursor.execute(sql, (nombre, precio_costo, cantidad))
        conexion.commit()
    except mysql.connector.Error as err:
        raise Exception(f"Error al insertar el producto: {err}")
    finally:
        cursor.close()
        conexion.close()


def actualizar_stock(producto_id, cantidad, nombre, precio_costo):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        sql = "UPDATE productos SET cantidad = %s, nombre = %s, precio_costo = %s WHERE id = %s"
        cursor.execute(sql, (cantidad, nombre, precio_costo, producto_id))
        conexion.commit()
    except mysql.connector.Error as err:
        raise Exception(f"Error al actualizar el producto: {err}")
    finally:
        cursor.close()
        conexion.close()


def actualizar_stock_venta(producto_id, cantidad_vendida):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        sql = "UPDATE productos SET cantidad = cantidad - %s WHERE id = %s"
        cursor.execute(sql, (cantidad_vendida, producto_id))
        conexion.commit()
    except mysql.connector.Error as err:
        raise Exception(f"Error al actualizar el stock: {err}")
    finally:
        cursor.close()
        conexion.close()


# ==========================================================================================
# LÓGICA DE NEGOCIO - VENTAS
# ==========================================================================================

def crear_venta_cabecera():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        sql = "INSERT INTO ventas (total_venta) VALUES (0.00)"
        cursor.execute(sql)
        conexion.commit()
        return cursor.lastrowid
    except mysql.connector.Error as err:
        raise Exception(f"Error al iniciar la venta: {err}")
    finally:
        cursor.close()
        conexion.close()


def actualizar_total_venta(venta_id, total):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        sql = "UPDATE ventas SET total_venta = %s WHERE id = %s"
        cursor.execute(sql, (total, venta_id))
        conexion.commit()
    except mysql.connector.Error as err:
        raise Exception(f"Error al actualizar el total de la venta: {err}")
    finally:
        cursor.close()
        conexion.close()


def eliminar_venta_vacia(venta_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        sql = "DELETE FROM ventas WHERE id = %s"
        cursor.execute(sql, (venta_id,))
        conexion.commit()
    except mysql.connector.Error:
        pass
    finally:
        cursor.close()
        conexion.close()


def insertar_detalle_venta(venta_id, producto_id, cantidad, precio_costo, precio_venta, precio_venta_total):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        sql = """INSERT INTO detalles_ventas
                 (venta_id, producto_id, cantidad, precio_costo, precio_venta, precio_venta_total)
                 VALUES (%s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (venta_id, producto_id, cantidad, precio_costo, precio_venta, precio_venta_total))
        conexion.commit()
    except mysql.connector.Error as err:
        raise Exception(f"Error al insertar el detalle de venta: {err}")
    finally:
        cursor.close()
        conexion.close()


def procesar_venta(carrito):
    if not carrito:
        raise Exception("El carrito está vacío.")

    venta_id = crear_venta_cabecera()
    if not venta_id:
        raise Exception("No se pudo iniciar la transacción de venta.")

    total = 0.0
    try:
        for item in carrito:
            insertar_detalle_venta(
                venta_id,
                item["producto_id"],
                item["cantidad"],
                item["precio_costo"],
                item["precio_venta"],
                item["subtotal"],
            )
            actualizar_stock_venta(item["producto_id"], item["cantidad"])
            total += item["subtotal"]

        actualizar_total_venta(venta_id, total)
        return venta_id, total
    except Exception as e:
        eliminar_venta_vacia(venta_id)
        raise e


def obtener_historial_ventas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        sql = """
        SELECT v.id, p.nombre, dv.cantidad, dv.precio_venta, dv.precio_venta_total, v.fecha
        FROM ventas v
        JOIN detalles_ventas dv ON v.id = dv.venta_id
        JOIN productos p ON dv.producto_id = p.id
        ORDER BY v.fecha DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except mysql.connector.Error as err:
        raise Exception(f"Error al obtener el historial de ventas: {err}")
    finally:
        cursor.close()
        conexion.close()


def obtener_metricas_dashboard():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        metricas = {}

        cursor.execute("SELECT COUNT(*), COALESCE(SUM(cantidad), 0) FROM productos")
        total_productos, total_stock = cursor.fetchone()
        metricas["total_productos"] = total_productos or 0
        metricas["total_stock"] = total_stock or 0

        cursor.execute("SELECT COUNT(*), COALESCE(SUM(cantidad), 0) FROM productos WHERE cantidad <= 5")
        bajo_stock_count, _ = cursor.fetchone()
        metricas["bajo_stock"] = bajo_stock_count or 0

        cursor.execute(
            """SELECT COUNT(DISTINCT v.id), COALESCE(SUM(v.total_venta), 0)
               FROM ventas v
               WHERE MONTH(v.fecha) = MONTH(CURRENT_DATE()) AND YEAR(v.fecha) = YEAR(CURRENT_DATE())"""
        )
        ventas_mes, total_ventas_mes = cursor.fetchone()
        metricas["ventas_mes"] = ventas_mes or 0
        metricas["total_ventas_mes"] = float(total_ventas_mes or 0)

        cursor.execute(
            """SELECT COALESCE(SUM(dv.cantidad * p.precio_costo), 0)
               FROM detalles_ventas dv
               JOIN ventas v ON dv.venta_id = v.id
               JOIN productos p ON dv.producto_id = p.id
               WHERE MONTH(v.fecha) = MONTH(CURRENT_DATE()) AND YEAR(v.fecha) = YEAR(CURRENT_DATE())"""
        )
        (costo_mes,) = cursor.fetchone()
        costo_mes = float(costo_mes or 0)
        metricas["ganancia_mes"] = metricas["total_ventas_mes"] - costo_mes

        return metricas
    except mysql.connector.Error as err:
        raise Exception(f"Error al calcular las métricas: {err}")
    finally:
        cursor.close()
        conexion.close()


# ==========================================================================================
# LÓGICA DE NEGOCIO - REPORTE PDF
# ==========================================================================================

def generar_reporte_pdf(ruta_destino=None):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        sql = """
        SELECT v.id, p.nombre, dv.cantidad, p.precio_costo, dv.precio_venta, dv.precio_venta_total, v.fecha
        FROM ventas v
        JOIN detalles_ventas dv ON v.id = dv.venta_id
        JOIN productos p ON dv.producto_id = p.id
        WHERE MONTH(v.fecha) = MONTH(CURRENT_DATE()) AND YEAR(v.fecha) = YEAR(CURRENT_DATE())
        ORDER BY v.fecha ASC
        """
        cursor.execute(sql)
        registros = cursor.fetchall()

        if not registros:
            raise Exception("No hay ventas registradas en el mes actual para generar el reporte.")

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()

        pdf.set_font("Arial", "B", 14)
        pdf.cell(190, 8, txt="Reporte Mensual de Ventas y Ganancias", ln=True, align="C")
        pdf.ln(3)

        pdf.set_font("Arial", "B", 8)
        pdf.cell(15, 6, "ID Vta", border=1, align="C")
        pdf.cell(40, 6, "Producto", border=1, align="C")
        pdf.cell(10, 6, "Cant.", border=1, align="C")
        pdf.cell(20, 6, "P. Entrada", border=1, align="C")
        pdf.cell(20, 6, "P. Salida", border=1, align="C")
        pdf.cell(25, 6, "Subt. Entrada", border=1, align="C")
        pdf.cell(25, 6, "Subt. Salida", border=1, align="C")
        pdf.cell(35, 6, "Fecha", border=1, align="C")
        pdf.ln()

        pdf.set_font("Arial", size=8)
        total_entrada_mes = 0.0
        total_salida_mes = 0.0

        for row in registros:
            id_venta = str(row[0])
            nombre = str(row[1])[:20]
            cantidad = int(row[2])
            precio_costo = float(row[3])
            precio_venta = float(row[4])
            subtotal_salida = float(row[5])
            fecha = str(row[6].strftime("%Y-%m-%d %H:%M"))

            subtotal_entrada = cantidad * precio_costo

            pdf.cell(15, 6, id_venta, border=1, align="C")
            pdf.cell(40, 6, nombre, border=1)
            pdf.cell(10, 6, str(cantidad), border=1, align="C")
            pdf.cell(20, 6, f"${precio_costo:.2f}", border=1, align="R")
            pdf.cell(20, 6, f"${precio_venta:.2f}", border=1, align="R")
            pdf.cell(25, 6, f"${subtotal_entrada:.2f}", border=1, align="R")
            pdf.cell(25, 6, f"${subtotal_salida:.2f}", border=1, align="R")
            pdf.cell(35, 6, fecha, border=1, align="C")
            pdf.ln()

            total_entrada_mes += subtotal_entrada
            total_salida_mes += subtotal_salida

        ganancia_total = total_salida_mes - total_entrada_mes

        pdf.ln(5)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(130, 6, "TOTAL PRECIO DE ENTRADA (Costo):", border=1, align="R")
        pdf.cell(60, 6, f"${total_entrada_mes:.2f}", border=1, align="C")
        pdf.ln()
        pdf.cell(130, 6, "TOTAL PRECIO DE SALIDA (Venta):", border=1, align="R")
        pdf.cell(60, 6, f"${total_salida_mes:.2f}", border=1, align="C")
        pdf.ln()

        pdf.set_fill_color(220, 235, 255)
        pdf.cell(130, 6, "GANANCIA TOTAL DEL MES:", border=1, align="R", fill=True)
        pdf.cell(60, 6, f"${ganancia_total:.2f}", border=1, align="C", fill=True)

        if ruta_destino:
            nombre_archivo = ruta_destino
        else:
            mes_actual = datetime.now().strftime("%m_%Y")
            nombre_archivo = os.path.join(os.getcwd(), f"reporte_ventas_{mes_actual}.pdf")

        pdf.output(nombre_archivo)
        return nombre_archivo

    except mysql.connector.Error as err:
        raise Exception(f"Error de base de datos al generar el reporte: {err}")
    finally:
        cursor.close()
        conexion.close()