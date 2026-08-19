import os
import mysql.connector
from datetime import datetime
from conection import obtener_conexion
from tabulate import tabulate
from fpdf import FPDF

def limpiar_pantalla():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

def esperar_tecla():
    input("\nPresione Enter para continuar...")

def insertar_producto(nombre, precio_costo, cantidad):
    conexion = obtener_conexion()
    if conexion is None: return
    cursor = conexion.cursor()
    try:
        sql = "INSERT INTO productos (nombre, precio_costo, cantidad) VALUES (%s, %s, %s)"
        cursor.execute(sql, (nombre, precio_costo, cantidad))
        conexion.commit()
        print("Producto insertado exitosamente")
    except mysql.connector.Error as err:
        print(f"Error al insertar el producto: {err}")
    finally:
        cursor.close()
        conexion.close()

def crear_venta_cabecera():
    conexion = obtener_conexion()
    if conexion is None: return None
    cursor = conexion.cursor()
    try:
        sql = "INSERT INTO ventas (total_venta) VALUES (0.00)"
        cursor.execute(sql)
        conexion.commit()
        return cursor.lastrowid
    except mysql.connector.Error as err:
        print(f"Error al iniciar la venta: {err}")
        return None
    finally:
        cursor.close()
        conexion.close()

def actualizar_total_venta(venta_id, total):
    conexion = obtener_conexion()
    if conexion is None: return
    cursor = conexion.cursor()
    try:
        sql = "UPDATE ventas SET total_venta = %s WHERE id = %s"
        cursor.execute(sql, (total, venta_id))
        conexion.commit()
    except mysql.connector.Error as err:
        print(f"Error al actualizar el total: {err}")
    finally:
        cursor.close()
        conexion.close()

def eliminar_venta_vacia(venta_id):
    conexion = obtener_conexion()
    if conexion is None: return
    cursor = conexion.cursor()
    try:
        sql = "DELETE FROM ventas WHERE id = %s"
        cursor.execute(sql, (venta_id,))
        conexion.commit()
    except mysql.connector.Error as err:
        pass
    finally:
        cursor.close()
        conexion.close()

def insertar_detalle_venta(venta_id, producto_id, cantidad, precio_costo, precio_venta, precio_venta_total):
    conexion = obtener_conexion()
    if conexion is None: return
    cursor = conexion.cursor()
    try:
        sql = "INSERT INTO detalles_ventas (venta_id, producto_id, cantidad, precio_costo, precio_venta, precio_venta_total) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (venta_id, producto_id, cantidad, precio_costo, precio_venta, precio_venta_total))
        conexion.commit()
    except mysql.connector.Error as err:
        print(f"Error al insertar el detalle de venta: {err}")
    finally:
        cursor.close()
        conexion.close()

def mostrar_productos():
    conexion = obtener_conexion()
    if conexion is None: return
    cursor = conexion.cursor()
    try:
        sql = "SELECT id, nombre, precio_costo, cantidad FROM productos"
        cursor.execute(sql)
        productos = cursor.fetchall()
        headers = ["ID", "Nombre", "Precio Costo", "Stock"]
        print(tabulate(productos, headers=headers, tablefmt="grid"))
    except mysql.connector.Error as err:
        print(f"Error al mostrar los productos: {err}")
    finally:
        cursor.close()
        conexion.close()

def obtener_producto(producto_id):
    conexion = obtener_conexion()
    if conexion is None: return None
    cursor = conexion.cursor()
    try:
        sql = "SELECT nombre, precio_costo, cantidad FROM productos WHERE id = %s"
        cursor.execute(sql, (producto_id,))
        return cursor.fetchone()
    except mysql.connector.Error as err:
        return None
    finally:
        cursor.close()
        conexion.close()

def actualizar_stock_venta(producto_id, cantidad_vendida):
    conexion = obtener_conexion()
    if conexion is None: return False
    cursor = conexion.cursor()
    try:
        sql = "UPDATE productos SET cantidad = cantidad - %s WHERE id = %s"
        cursor.execute(sql, (cantidad_vendida, producto_id))
        conexion.commit()
        return True
    except mysql.connector.Error as err:
        return False
    finally:
        cursor.close()
        conexion.close()

def actualizar_stock(producto_id, cantidad, nombre, precio_costo):
    conexion = obtener_conexion()
    if conexion is None: return False
    cursor = conexion.cursor()
    try:
        sql = "UPDATE productos SET cantidad = %s, nombre = %s, precio_costo = %s WHERE id = %s"
        cursor.execute(sql, (cantidad, nombre, precio_costo, producto_id))
        conexion.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Error al actualizar el producto: {err}")
        return False
    finally:
        cursor.close()
        conexion.close()

def mostrar_historial_ventas():
    conexion = obtener_conexion()
    if conexion is None: return
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
        ventas = cursor.fetchall()
        headers = ["ID Venta", "Producto", "Cant.", "Precio Unit.", "Subtotal", "Fecha"]
        print(tabulate(ventas, headers=headers, tablefmt="grid"))
    except mysql.connector.Error as err:
        print(f"Error al mostrar el historial: {err}")
    finally:
        cursor.close()
        conexion.close()

def generar_reporte_pdf():
    conexion = obtener_conexion()
    if conexion is None: return
    cursor = conexion.cursor()
    try:
        # AQUÍ SE CAMBIA dv.precio_costo POR p.precio_costo PARA QUE LO TOME DE LA TABLA PRODUCTOS
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
            print("No hay ventas registradas en el mes actual para generar el reporte.")
            return

        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        
        # Título
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 8, txt="Reporte Mensual de Ventas y Ganancias", ln=True, align='C')
        pdf.ln(3)

        # Encabezados de tabla
        pdf.set_font("Arial", 'B', 8)
        # Ancho total: 15+40+10+20+20+25+25+35 = 190 mm
        pdf.cell(15, 6, "ID Vta", border=1, align='C')
        pdf.cell(40, 6, "Producto", border=1, align='C')
        pdf.cell(10, 6, "Cant.", border=1, align='C')
        pdf.cell(20, 6, "P. Entrada", border=1, align='C')
        pdf.cell(20, 6, "P. Salida", border=1, align='C')
        pdf.cell(25, 6, "Subt. Entrada", border=1, align='C')
        pdf.cell(25, 6, "Subt. Salida", border=1, align='C')
        pdf.cell(35, 6, "Fecha", border=1, align='C')
        pdf.ln()

        # Filas
        pdf.set_font("Arial", size=8)
        total_entrada_mes = 0.0
        total_salida_mes = 0.0

        for row in registros:
            id_venta = str(row[0])
            nombre = str(row[1])[:20] # Se recorta para que no desborde la celda
            cantidad = int(row[2])
            precio_costo = float(row[3])
            precio_venta = float(row[4])
            subtotal_salida = float(row[5])
            fecha = str(row[6].strftime("%Y-%m-%d %H:%M"))
            
            subtotal_entrada = cantidad * precio_costo

            pdf.cell(15, 6, id_venta, border=1, align='C')
            pdf.cell(40, 6, nombre, border=1)
            pdf.cell(10, 6, str(cantidad), border=1, align='C')
            pdf.cell(20, 6, f"${precio_costo:.2f}", border=1, align='R')
            pdf.cell(20, 6, f"${precio_venta:.2f}", border=1, align='R')
            pdf.cell(25, 6, f"${subtotal_entrada:.2f}", border=1, align='R')
            pdf.cell(25, 6, f"${subtotal_salida:.2f}", border=1, align='R')
            pdf.cell(35, 6, fecha, border=1, align='C')
            pdf.ln()
            
            total_entrada_mes += subtotal_entrada
            total_salida_mes += subtotal_salida

        # Sección de Resumen y Totales
        ganancia_total = total_salida_mes - total_entrada_mes
        
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(130, 6, "TOTAL PRECIO DE ENTRADA (Costo):", border=1, align='R')
        pdf.cell(60, 6, f"${total_entrada_mes:.2f}", border=1, align='C')
        pdf.ln()
        pdf.cell(130, 6, "TOTAL PRECIO DE SALIDA (Venta):", border=1, align='R')
        pdf.cell(60, 6, f"${total_salida_mes:.2f}", border=1, align='C')
        pdf.ln()
        
        # Resaltamos la ganancia
        pdf.set_fill_color(220, 235, 255)
        pdf.cell(130, 6, "GANANCIA TOTAL DEL MES:", border=1, align='R', fill=True)
        pdf.cell(60, 6, f"${ganancia_total:.2f}", border=1, align='C', fill=True)

        mes_actual = datetime.now().strftime("%m_%Y")
        nombre_archivo = f"reporte_ventas_{mes_actual}.pdf"
        pdf.output(nombre_archivo)
        print(f"\n✅ Reporte generado exitosamente: {nombre_archivo}")
        
    except Exception as e:
        print(f"Error al generar el reporte PDF: {e}")
    finally:
        cursor.close()
        conexion.close()
