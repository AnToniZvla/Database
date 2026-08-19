from functions import (
    mostrar_historial_ventas, actualizar_stock_venta, insertar_producto,
    crear_venta_cabecera, actualizar_total_venta, eliminar_venta_vacia, insertar_detalle_venta,
    limpiar_pantalla, esperar_tecla, mostrar_productos, actualizar_stock, obtener_producto, generar_reporte_pdf
)
from tablas import crear_tablas

#==========================================================================================================================================================================
crear_tablas()
#==========================================================================================================================================================================
limpiar_pantalla()
#==========================================================================================================================================================================

def mostrar_menu_principal():
    print("                               ======================================================")
    print("                               Bienvenido al sistema de gestión de productos y ventas")
    print("                               ======================================================")
    print("1. Productos")
    print("2. Ventas")
    print("3. Historial de ventas")
    print("4. Generar reporte mensual (PDF)")
    print("5. Salir")

mostrar_menu_principal()
input_usuario = input("Esperando opción: ")

while input_usuario != "5":
    if input_usuario == "1":
        limpiar_pantalla()
        print("1. Insertar producto")
        print("2. Mostrar productos")
        print("3. Actualizar producto")
        print("4. Salir al menu principal")
        input_producto = input("Esperando opción: ")
        
        if input_producto == "1":
            limpiar_pantalla()
            while True:
                nombre = input("Ingrese el nombre del producto (enter para salir): ")
                if nombre.strip() == "":
                    break
                precio_costo = float(input("Ingrese el precio de ENTRADA (costo) del producto: "))
                if precio_costo <= 0:
                    break
                # Ya no pide precio de VENTA aquí
                cantidad = int(input("Ingrese la cantidad del producto: "))
                if cantidad < 0:
                    break
                insertar_producto(nombre, precio_costo, cantidad)
                esperar_tecla()

            limpiar_pantalla()

        elif input_producto == "2":
            limpiar_pantalla()
            mostrar_productos()
            esperar_tecla()
            limpiar_pantalla()
            
        elif input_producto == "3":
            limpiar_pantalla()
            mostrar_productos()
            producto_id = int(input("\nIngrese el ID del producto a actualizar: "))
            nombre = input("Ingrese el nuevo nombre del producto: ")
            precio_costo = float(input("Ingrese el nuevo precio de ENTRADA (costo) del producto: "))
            # Ya no pide precio de VENTA aquí
            cantidad = int(input("Ingrese la nueva cantidad del producto: "))
            actualizar_stock(producto_id, cantidad, nombre, precio_costo)
            esperar_tecla()
            limpiar_pantalla()
        else:
            limpiar_pantalla()
            print("Opción inválida. Por favor, seleccione una opción válida.")
            esperar_tecla()
            limpiar_pantalla()

#=========================================================================================================
    elif input_usuario == "2":
        limpiar_pantalla()
        
        venta_id = crear_venta_cabecera()
        if not venta_id:
            print("No se pudo iniciar la transacción.")
            esperar_tecla()
            continue
            
        gran_total = 0.0
        items_vendidos = 0
        
        print(f"--- Iniciando Venta #{venta_id} ---")
        
        while True:
            mostrar_productos()
            entrada = input("\nIngrese el ID del producto a vender (o escriba '0' para procesar el pago): ")
            
            if entrada == "0":
                break
                
            if not entrada.isdigit():
                print("Por favor, ingrese un ID numérico válido.")
                continue
                
            producto_id = int(entrada)
            producto = obtener_producto(producto_id)
            
            if producto is None:
                print("Producto no encontrado.")
            else:
                # Ahora solo se extraen 3 valores (ya no hay 'precio' base)
                nombre, precio_costo, stock = producto 
                cantidad = int(input(f"Stock disponible: {stock}. Ingrese la cantidad a llevar: "))
                
                if cantidad <= 0:
                    print("La cantidad debe ser mayor a 0.")
                elif cantidad > stock:
                    print(f"No hay suficiente stock. Solo quedan {stock} unidades.")
                else:
                    # Aquí es donde le asignas el precio en el que lo vas a vender
                    precio_venta = float(input(f"Ingrese el precio de VENTA para el cliente: "))
                    
                    if precio_venta <= 0:
                        print("El precio debe ser mayor a 0.")
                        continue

                    precio_venta_total = precio_venta * cantidad
                    
                    insertar_detalle_venta(venta_id, producto_id, cantidad, precio_costo, precio_venta, precio_venta_total)
                    actualizar_stock_venta(producto_id, cantidad)
                    
                    gran_total += precio_venta_total
                    items_vendidos += 1
                    print(f"✅ Agregado: {cantidad} x {nombre} a ${precio_venta} c/u. (Subtotal: ${precio_venta_total})")

        if items_vendidos > 0:
            actualizar_total_venta(venta_id, gran_total)
            print(f"\n✅ Venta #{venta_id} procesada con éxito. Total a pagar: ${gran_total:.2f}")
        else:
            eliminar_venta_vacia(venta_id)
            print("\nVenta cancelada (no se agregaron artículos).")
            
        esperar_tecla()
        limpiar_pantalla()

#==========================================================================================================================================================================
    elif input_usuario == "3":
        limpiar_pantalla()
        mostrar_historial_ventas()
        esperar_tecla()
        limpiar_pantalla()

#==========================================================================================================================================================================
    elif input_usuario == "4":
        limpiar_pantalla()
        generar_reporte_pdf()
        esperar_tecla()
        limpiar_pantalla()

#==========================================================================================================================================================================
    else:
        print("Opción inválida. Por favor, seleccione una opción válida.")
        esperar_tecla()
        limpiar_pantalla()

    mostrar_menu_principal()
    input_usuario = input("Esperando opción: ")
