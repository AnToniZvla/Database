import sys
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk

# Importar lógica de otros módulos
from tablas import crear_tablas
from functions import (
    obtener_productos, 
    insertar_producto, 
    actualizar_stock, 
    procesar_venta, 
    obtener_historial_ventas, 
    obtener_metricas_dashboard, 
    generar_reporte_pdf
)

# ==========================================================================================
# INTERFAZ GRÁFICA
# ==========================================================================================

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

COLOR_SIDEBAR = "#1f2937"
COLOR_SIDEBAR_BTN_HOVER = "#374151"
COLOR_ACCENT = "#2563eb"


def configurar_estilo_treeview():
    """Ajusta el estilo ttk.Treeview para que combine con customtkinter."""
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Custom.Treeview",
        background="#f9fafb",
        foreground="#111827",
        fieldbackground="#f9fafb",
        rowheight=28,
        borderwidth=0,
        font=("Segoe UI", 10),
    )
    style.configure(
        "Custom.Treeview.Heading",
        background="#e5e7eb",
        foreground="#111827",
        font=("Segoe UI", 10, "bold"),
        relief="flat",
    )
    style.map("Custom.Treeview", background=[("selected", COLOR_ACCENT)], foreground=[("selected", "white")])


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sistema de Gestión de Productos y Ventas")
        self.geometry("1180x700")
        self.minsize(1000, 600)

        configurar_estilo_treeview()

        # Carrito de venta en memoria: lista de dicts
        self.carrito = []

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._crear_sidebar()
        self._crear_contenedor_vistas()

        self._inicializar_base_datos()

        self.mostrar_vista("dashboard")

    def _inicializar_base_datos(self):
        try:
            crear_tablas()
        except Exception as e:
            messagebox.showerror("Error de Base de Datos", str(e))

    def _crear_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        titulo = ctk.CTkLabel(
            self.sidebar,
            text="📋 Gestión\nde Ventas",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white",
            justify="left",
        )
        titulo.grid(row=0, column=0, padx=20, pady=(25, 30), sticky="w")

        botones = [
            ("📊  Dashboard", "dashboard"),
            ("📦  Productos", "productos"),
            ("🛒  Ventas (POS)", "ventas"),
            ("📜  Historial", "historial"),
            ("📄  Reporte PDF", "reporte"),
        ]

        self.botones_nav = {}
        for i, (texto, clave) in enumerate(botones, start=1):
            btn = ctk.CTkButton(
                self.sidebar,
                text=texto,
                anchor="w",
                fg_color="transparent",
                hover_color=COLOR_SIDEBAR_BTN_HOVER,
                text_color="white",
                font=ctk.CTkFont(size=14),
                height=40,
                command=lambda k=clave: self.mostrar_vista(k),
            )
            btn.grid(row=i, column=0, padx=15, pady=4, sticky="ew")
            self.botones_nav[clave] = btn

        btn_salir = ctk.CTkButton(
            self.sidebar,
            text="🚪  Salir",
            anchor="w",
            fg_color="#7f1d1d",
            hover_color="#991b1b",
            text_color="white",
            font=ctk.CTkFont(size=14),
            height=40,
            command=self.destroy,
        )
        btn_salir.grid(row=9, column=0, padx=15, pady=(4, 20), sticky="sew")

    def _crear_contenedor_vistas(self):
        self.contenedor = ctk.CTkFrame(self, corner_radius=0, fg_color=("#ffffff", "#1a1a1a"))
        self.contenedor.grid(row=0, column=1, sticky="nsew")
        self.contenedor.grid_rowconfigure(0, weight=1)
        self.contenedor.grid_columnconfigure(0, weight=1)

        self.vistas = {}
        self.vistas["dashboard"] = DashboardFrame(self.contenedor, self)
        self.vistas["productos"] = ProductosFrame(self.contenedor, self)
        self.vistas["ventas"] = VentasFrame(self.contenedor, self)
        self.vistas["historial"] = HistorialFrame(self.contenedor, self)
        self.vistas["reporte"] = ReporteFrame(self.contenedor, self)

        for vista in self.vistas.values():
            vista.grid(row=0, column=0, sticky="nsew")

    def mostrar_vista(self, clave):
        for k, btn in self.botones_nav.items():
            btn.configure(fg_color=COLOR_ACCENT if k == clave else "transparent")

        vista = self.vistas[clave]
        vista.tkraise()
        if hasattr(vista, "on_show"):
            vista.on_show()

    def ejecutar_seguro(self, funcion, *args, mensaje_exito=None, **kwargs):
        try:
            resultado = funcion(*args, **kwargs)
            if mensaje_exito:
                messagebox.showinfo("Éxito", mensaje_exito)
            return resultado
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return None


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, app: App):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        titulo = ctk.CTkLabel(self, text="Dashboard / Resumen", font=ctk.CTkFont(size=24, weight="bold"))
        titulo.grid(row=0, column=0, columnspan=4, padx=30, pady=(25, 15), sticky="w")

        self.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.tarjetas = {}
        info_tarjetas = [
            ("total_productos", "📦 Productos registrados", "#2563eb"),
            ("total_stock", "📈 Unidades en stock", "#059669"),
            ("bajo_stock", "⚠️ Productos con stock bajo (≤5)", "#d97706"),
            ("ventas_mes", "🛒 Ventas este mes", "#7c3aed"),
            ("total_ventas_mes", "💰 Ingresos del mes", "#16a34a"),
            ("ganancia_mes", "📊 Ganancia del mes", "#dc2626"),
        ]

        for i, (clave, etiqueta, color) in enumerate(info_tarjetas):
            fila = 1 + (i // 3)
            columna = i % 3
            tarjeta = ctk.CTkFrame(self, corner_radius=12, fg_color=("#f3f4f6", "#262626"))
            tarjeta.grid(row=fila, column=columna, padx=15, pady=15, sticky="nsew")

            barra = ctk.CTkFrame(tarjeta, width=6, fg_color=color, corner_radius=0)
            barra.pack(side="left", fill="y")

            contenido = ctk.CTkFrame(tarjeta, fg_color="transparent")
            contenido.pack(side="left", fill="both", expand=True, padx=15, pady=15)

            lbl_valor = ctk.CTkLabel(contenido, text="--", font=ctk.CTkFont(size=26, weight="bold"))
            lbl_valor.pack(anchor="w")
            lbl_desc = ctk.CTkLabel(contenido, text=etiqueta, font=ctk.CTkFont(size=13), text_color="gray")
            lbl_desc.pack(anchor="w")

            self.tarjetas[clave] = lbl_valor

        btn_actualizar = ctk.CTkButton(self, text="🔄 Actualizar métricas", command=self.cargar_metricas)
        btn_actualizar.grid(row=3, column=0, padx=30, pady=15, sticky="w")

    def on_show(self):
        self.cargar_metricas()

    def cargar_metricas(self):
        metricas = self.app.ejecutar_seguro(obtener_metricas_dashboard)
        if metricas is None:
            return
        self.tarjetas["total_productos"].configure(text=str(metricas["total_productos"]))
        self.tarjetas["total_stock"].configure(text=str(metricas["total_stock"]))
        self.tarjetas["bajo_stock"].configure(text=str(metricas["bajo_stock"]))
        self.tarjetas["ventas_mes"].configure(text=str(metricas["ventas_mes"]))
        self.tarjetas["total_ventas_mes"].configure(text=f"${metricas['total_ventas_mes']:.2f}")
        self.tarjetas["ganancia_mes"].configure(text=f"${metricas['ganancia_mes']:.2f}")


class ProductosFrame(ctk.CTkFrame):
    def __init__(self, parent, app: App):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.producto_seleccionado = None

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        titulo = ctk.CTkLabel(self, text="Productos", font=ctk.CTkFont(size=24, weight="bold"))
        titulo.grid(row=0, column=0, columnspan=2, padx=30, pady=(25, 10), sticky="w")

        frame_tabla = ctk.CTkFrame(self, fg_color=("#f3f4f6", "#262626"), corner_radius=10)
        frame_tabla.grid(row=1, column=0, padx=(30, 15), pady=(0, 20), sticky="nsew")
        frame_tabla.grid_rowconfigure(0, weight=1)
        frame_tabla.grid_columnconfigure(0, weight=1)

        columnas = ("id", "nombre", "precio_costo", "cantidad")
        self.tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings", style="Custom.Treeview")
        self.tabla.heading("id", text="ID")
        self.tabla.heading("nombre", text="Nombre")
        self.tabla.heading("precio_costo", text="Precio Costo")
        self.tabla.heading("cantidad", text="Stock")
        self.tabla.column("id", width=50, anchor="center")
        self.tabla.column("nombre", width=220)
        self.tabla.column("precio_costo", width=100, anchor="e")
        self.tabla.column("cantidad", width=80, anchor="center")
        self.tabla.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.tabla.bind("<<TreeviewSelect>>", self._on_seleccionar)

        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=10)

        btn_refrescar = ctk.CTkButton(frame_tabla, text="🔄 Refrescar", width=120, command=self.cargar_productos)
        btn_refrescar.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")

        frame_form = ctk.CTkFrame(self, fg_color=("#f3f4f6", "#262626"), corner_radius=10)
        frame_form.grid(row=1, column=1, padx=(0, 30), pady=(0, 20), sticky="nsew")

        lbl_form = ctk.CTkLabel(frame_form, text="Nuevo / Actualizar producto", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_form.pack(padx=15, pady=(15, 10), anchor="w")

        ctk.CTkLabel(frame_form, text="Nombre:").pack(padx=15, anchor="w")
        self.entry_nombre = ctk.CTkEntry(frame_form, placeholder_text="Nombre del producto")
        self.entry_nombre.pack(padx=15, pady=(0, 10), fill="x")

        ctk.CTkLabel(frame_form, text="Precio de costo:").pack(padx=15, anchor="w")
        self.entry_precio = ctk.CTkEntry(frame_form, placeholder_text="0.00")
        self.entry_precio.pack(padx=15, pady=(0, 10), fill="x")

        ctk.CTkLabel(frame_form, text="Cantidad / Stock:").pack(padx=15, anchor="w")
        self.entry_cantidad = ctk.CTkEntry(frame_form, placeholder_text="0")
        self.entry_cantidad.pack(padx=15, pady=(0, 15), fill="x")

        self.lbl_id_seleccionado = ctk.CTkLabel(frame_form, text="Ningún producto seleccionado", text_color="gray")
        self.lbl_id_seleccionado.pack(padx=15, anchor="w")

        btn_guardar = ctk.CTkButton(frame_form, text="➕ Registrar nuevo producto", command=self.registrar_producto)
        btn_guardar.pack(padx=15, pady=(10, 5), fill="x")

        btn_actualizar = ctk.CTkButton(
            frame_form, text="✏️ Actualizar producto seleccionado",
            fg_color="#d97706", hover_color="#b45309", command=self.actualizar_producto
        )
        btn_actualizar.pack(padx=15, pady=5, fill="x")

        btn_limpiar = ctk.CTkButton(
            frame_form, text="🧹 Limpiar formulario",
            fg_color="gray30", hover_color="gray20", command=self.limpiar_formulario
        )
        btn_limpiar.pack(padx=15, pady=(5, 15), fill="x")

        self.cargar_productos()

    def on_show(self):
        self.cargar_productos()

    def cargar_productos(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        productos = self.app.ejecutar_seguro(obtener_productos)
        if productos is None:
            return
        for p in productos:
            id_, nombre, precio_costo, cantidad = p
            self.tabla.insert("", "end", values=(id_, nombre, f"{float(precio_costo):.2f}", cantidad))

    def _on_seleccionar(self, event):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        valores = self.tabla.item(seleccion[0], "values")
        self.producto_seleccionado = valores[0]
        self.entry_nombre.delete(0, "end")
        self.entry_nombre.insert(0, valores[1])
        self.entry_precio.delete(0, "end")
        self.entry_precio.insert(0, valores[2])
        self.entry_cantidad.delete(0, "end")
        self.entry_cantidad.insert(0, valores[3])
        self.lbl_id_seleccionado.configure(text=f"Editando producto ID: {valores[0]}")

    def limpiar_formulario(self):
        self.entry_nombre.delete(0, "end")
        self.entry_precio.delete(0, "end")
        self.entry_cantidad.delete(0, "end")
        self.producto_seleccionado = None
        self.lbl_id_seleccionado.configure(text="Ningún producto seleccionado")
        self.tabla.selection_remove(self.tabla.selection())

    def _validar_formulario(self):
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Datos incompletos", "El nombre del producto es obligatorio.")
            return None
        try:
            precio_costo = float(self.entry_precio.get())
            if precio_costo <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Datos inválidos", "El precio de costo debe ser un número mayor a 0.")
            return None
        try:
            cantidad = int(self.entry_cantidad.get())
            if cantidad < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Datos inválidos", "La cantidad debe ser un número entero válido.")
            return None
        return nombre, precio_costo, cantidad

    def registrar_producto(self):
        datos = self._validar_formulario()
        if not datos:
            return
        nombre, precio_costo, cantidad = datos
        resultado = self.app.ejecutar_seguro(
            insertar_producto, nombre, precio_costo, cantidad,
            mensaje_exito="Producto insertado exitosamente."
        )
        if resultado is not None or True: 
            self.limpiar_formulario()
            self.cargar_productos()

    def actualizar_producto(self):
        if not self.producto_seleccionado:
            messagebox.showwarning("Sin selección", "Seleccione un producto de la tabla para actualizar.")
            return
        datos = self._validar_formulario()
        if not datos:
            return
        nombre, precio_costo, cantidad = datos
        self.app.ejecutar_seguro(
            actualizar_stock, self.producto_seleccionado, cantidad, nombre, precio_costo,
            mensaje_exito="Producto actualizado exitosamente."
        )
        self.limpiar_formulario()
        self.cargar_productos()


class VentasFrame(ctk.CTkFrame):
    def __init__(self, parent, app: App):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.productos_cache = {}

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        titulo = ctk.CTkLabel(self, text="Ventas (Punto de Venta)", font=ctk.CTkFont(size=24, weight="bold"))
        titulo.grid(row=0, column=0, columnspan=2, padx=30, pady=(25, 10), sticky="w")

        frame_productos = ctk.CTkFrame(self, fg_color=("#f3f4f6", "#262626"), corner_radius=10)
        frame_productos.grid(row=1, column=0, padx=(30, 15), pady=(0, 10), sticky="nsew")
        frame_productos.grid_rowconfigure(1, weight=1)
        frame_productos.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame_productos, text="Productos disponibles", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w"
        )

        columnas = ("id", "nombre", "precio_costo", "stock")
        self.tabla_productos = ttk.Treeview(frame_productos, columns=columnas, show="headings", style="Custom.Treeview")
        self.tabla_productos.heading("id", text="ID")
        self.tabla_productos.heading("nombre", text="Nombre")
        self.tabla_productos.heading("precio_costo", text="Costo")
        self.tabla_productos.heading("stock", text="Stock")
        self.tabla_productos.column("id", width=50, anchor="center")
        self.tabla_productos.column("nombre", width=200)
        self.tabla_productos.column("precio_costo", width=90, anchor="e")
        self.tabla_productos.column("stock", width=70, anchor="center")
        self.tabla_productos.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        scrollbar1 = ttk.Scrollbar(frame_productos, orient="vertical", command=self.tabla_productos.yview)
        self.tabla_productos.configure(yscrollcommand=scrollbar1.set)
        scrollbar1.grid(row=1, column=1, sticky="ns", pady=5)

        frame_agregar = ctk.CTkFrame(frame_productos, fg_color="transparent")
        frame_agregar.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        frame_agregar.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(frame_agregar, text="Cantidad:").grid(row=0, column=0, sticky="w")
        self.entry_cant_venta = ctk.CTkEntry(frame_agregar, placeholder_text="Ej. 1")
        self.entry_cant_venta.grid(row=1, column=0, padx=(0, 5), sticky="ew")

        ctk.CTkLabel(frame_agregar, text="Precio de venta:").grid(row=0, column=1, sticky="w")
        self.entry_precio_venta = ctk.CTkEntry(frame_agregar, placeholder_text="Ej. 10.00")
        self.entry_precio_venta.grid(row=1, column=1, padx=5, sticky="ew")

        btn_agregar = ctk.CTkButton(frame_agregar, text="➕ Agregar al carrito", command=self.agregar_al_carrito)
        btn_agregar.grid(row=1, column=2, padx=(5, 0), sticky="ew")

        btn_refrescar_prod = ctk.CTkButton(
            frame_productos, text="🔄 Refrescar productos", command=self.cargar_productos
        )
        btn_refrescar_prod.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="w")

        frame_carrito = ctk.CTkFrame(self, fg_color=("#f3f4f6", "#262626"), corner_radius=10)
        frame_carrito.grid(row=1, column=1, padx=(0, 30), pady=(0, 10), sticky="nsew")
        frame_carrito.grid_rowconfigure(1, weight=1)
        frame_carrito.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame_carrito, text="🛒 Carrito de venta", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w"
        )

        columnas_carrito = ("producto", "cantidad", "precio_venta", "subtotal")
        self.tabla_carrito = ttk.Treeview(
            frame_carrito, columns=columnas_carrito, show="headings", style="Custom.Treeview"
        )
        self.tabla_carrito.heading("producto", text="Producto")
        self.tabla_carrito.heading("cantidad", text="Cant.")
        self.tabla_carrito.heading("precio_venta", text="P. Unit.")
        self.tabla_carrito.heading("subtotal", text="Subtotal")
        self.tabla_carrito.column("producto", width=140)
        self.tabla_carrito.column("cantidad", width=50, anchor="center")
        self.tabla_carrito.column("precio_venta", width=70, anchor="e")
        self.tabla_carrito.column("subtotal", width=80, anchor="e")
        self.tabla_carrito.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        btn_quitar = ctk.CTkButton(
            frame_carrito, text="🗑️ Quitar seleccionado", fg_color="gray30", hover_color="gray20",
            command=self.quitar_del_carrito
        )
        btn_quitar.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="ew")

        self.lbl_total = ctk.CTkLabel(frame_carrito, text="Total: $0.00", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_total.grid(row=3, column=0, padx=10, pady=10, sticky="e")

        btn_procesar = ctk.CTkButton(
            frame_carrito, text="✅ Procesar Venta", fg_color="#16a34a", hover_color="#15803d",
            font=ctk.CTkFont(size=14, weight="bold"), height=40, command=self.procesar_venta
        )
        btn_procesar.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")

        self.cargar_productos()

    def on_show(self):
        self.cargar_productos()

    def cargar_productos(self):
        for item in self.tabla_productos.get_children():
            self.tabla_productos.delete(item)
        productos = self.app.ejecutar_seguro(obtener_productos)
        if productos is None:
            return
        self.productos_cache = {}
        for p in productos:
            id_, nombre, precio_costo, cantidad = p
            self.productos_cache[str(id_)] = {
                "nombre": nombre, "precio_costo": float(precio_costo), "stock": cantidad
            }
            self.tabla_productos.insert("", "end", values=(id_, nombre, f"{float(precio_costo):.2f}", cantidad))

    def agregar_al_carrito(self):
        seleccion = self.tabla_productos.selection()
        if not seleccion:
            messagebox.showwarning("Sin selección", "Seleccione un producto de la tabla.")
            return

        valores = self.tabla_productos.item(seleccion[0], "values")
        producto_id, nombre, precio_costo_str, stock_str = valores
        precio_costo = float(precio_costo_str)
        stock_disponible = int(stock_str)

        try:
            cantidad = int(self.entry_cant_venta.get())
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Datos inválidos", "Ingrese una cantidad válida mayor a 0.")
            return

        ya_en_carrito = sum(item["cantidad"] for item in self.carrito_items() if item["producto_id"] == producto_id)
        if cantidad + ya_en_carrito > stock_disponible:
            messagebox.showwarning(
                "Stock insuficiente",
                f"Solo hay {stock_disponible} unidades disponibles de '{nombre}' "
                f"({ya_en_carrito} ya están en el carrito)."
            )
            return

        try:
            precio_venta = float(self.entry_precio_venta.get())
            if precio_venta <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Datos inválidos", "Ingrese un precio de venta válido mayor a 0.")
            return

        subtotal = cantidad * precio_venta
        item = {
            "producto_id": producto_id,
            "nombre": nombre,
            "cantidad": cantidad,
            "precio_costo": precio_costo,
            "precio_venta": precio_venta,
            "subtotal": subtotal,
        }
        self.app.carrito.append(item)
        self.tabla_carrito.insert("", "end", values=(nombre, cantidad, f"{precio_venta:.2f}", f"{subtotal:.2f}"))

        self.entry_cant_venta.delete(0, "end")
        self.entry_precio_venta.delete(0, "end")
        self._actualizar_total()

    def carrito_items(self):
        return self.app.carrito

    def quitar_del_carrito(self):
        seleccion = self.tabla_carrito.selection()
        if not seleccion:
            return
        idx = self.tabla_carrito.index(seleccion[0])
        self.tabla_carrito.delete(seleccion[0])
        if 0 <= idx < len(self.app.carrito):
            del self.app.carrito[idx]
        self._actualizar_total()

    def _actualizar_total(self):
        total = sum(item["subtotal"] for item in self.app.carrito)
        self.lbl_total.configure(text=f"Total: ${total:.2f}")

    def procesar_venta(self):
        if not self.app.carrito:
            messagebox.showwarning("Carrito vacío", "Agregue al menos un producto al carrito antes de procesar la venta.")
            return

        confirmar = messagebox.askyesno(
            "Confirmar venta",
            f"¿Desea procesar la venta con {len(self.app.carrito)} artículo(s) "
            f"por un total de ${sum(i['subtotal'] for i in self.app.carrito):.2f}?"
        )
        if not confirmar:
            return

        resultado = self.app.ejecutar_seguro(procesar_venta, self.app.carrito)
        if resultado is None:
            return

        venta_id, total = resultado
        messagebox.showinfo("Venta procesada", f"Venta #{venta_id} procesada con éxito.\nTotal cobrado: ${total:.2f}")

        self.app.carrito = []
        for item in self.tabla_carrito.get_children():
            self.tabla_carrito.delete(item)
        self._actualizar_total()
        self.cargar_productos()


class HistorialFrame(ctk.CTkFrame):
    def __init__(self, parent, app: App):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        titulo = ctk.CTkLabel(self, text="Historial de Ventas", font=ctk.CTkFont(size=24, weight="bold"))
        titulo.grid(row=0, column=0, padx=30, pady=(25, 10), sticky="w")

        frame_filtro = ctk.CTkFrame(self, fg_color="transparent")
        frame_filtro.grid(row=1, column=0, padx=30, pady=(0, 10), sticky="ew")

        self.entry_filtro = ctk.CTkEntry(frame_filtro, placeholder_text="Filtrar por nombre de producto...")
        self.entry_filtro.pack(side="left", padx=(0, 10), fill="x", expand=True)
        self.entry_filtro.bind("<KeyRelease>", lambda e: self._aplicar_filtro())

        btn_refrescar = ctk.CTkButton(frame_filtro, text="🔄 Refrescar", width=120, command=self.cargar_historial)
        btn_refrescar.pack(side="left")

        frame_tabla = ctk.CTkFrame(self, fg_color=("#f3f4f6", "#262626"), corner_radius=10)
        frame_tabla.grid(row=2, column=0, padx=30, pady=(0, 20), sticky="nsew")
        frame_tabla.grid_rowconfigure(0, weight=1)
        frame_tabla.grid_columnconfigure(0, weight=1)

        columnas = ("id_venta", "producto", "cantidad", "precio_unit", "subtotal", "fecha")
        self.tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings", style="Custom.Treeview")
        titulos = {
            "id_venta": "ID Venta", "producto": "Producto", "cantidad": "Cant.",
            "precio_unit": "Precio Unit.", "subtotal": "Subtotal", "fecha": "Fecha",
        }
        anchos = {"id_venta": 70, "producto": 220, "cantidad": 60, "precio_unit": 90, "subtotal": 90, "fecha": 150}
        for col in columnas:
            self.tabla.heading(col, text=titulos[col])
            self.tabla.column(col, width=anchos[col], anchor="center" if col != "producto" else "w")
        self.tabla.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=10)

        self.registros_completos = []

    def on_show(self):
        self.cargar_historial()

    def cargar_historial(self):
        registros = self.app.ejecutar_seguro(obtener_historial_ventas)
        if registros is None:
            return
        self.registros_completos = registros
        self._aplicar_filtro()

    def _aplicar_filtro(self):
        filtro = self.entry_filtro.get().strip().lower()
        for item in self.tabla.get_children():
            self.tabla.delete(item)
        for r in self.registros_completos:
            id_venta, producto, cantidad, precio_unit, subtotal, fecha = r
            if filtro and filtro not in producto.lower():
                continue
            fecha_str = fecha.strftime("%Y-%m-%d %H:%M") if hasattr(fecha, "strftime") else str(fecha)
            self.tabla.insert(
                "", "end",
                values=(id_venta, producto, cantidad, f"${float(precio_unit):.2f}", f"${float(subtotal):.2f}", fecha_str)
            )


class ReporteFrame(ctk.CTkFrame):
    def __init__(self, parent, app: App):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        titulo = ctk.CTkLabel(self, text="Reporte Mensual (PDF)", font=ctk.CTkFont(size=24, weight="bold"))
        titulo.pack(padx=30, pady=(25, 10), anchor="w")

        descripcion = ctk.CTkLabel(
            self,
            text=(
                "Genera un reporte en PDF con todas las ventas del mes actual,\n"
                "incluyendo el desglose de precios de entrada, salida y la ganancia total."
            ),
            justify="left",
            text_color="gray",
        )
        descripcion.pack(padx=30, pady=(0, 20), anchor="w")

        frame_card = ctk.CTkFrame(self, fg_color=("#f3f4f6", "#262626"), corner_radius=12)
        frame_card.pack(padx=30, pady=10, fill="x")

        ctk.CTkLabel(frame_card, text="📄", font=ctk.CTkFont(size=48)).pack(pady=(20, 5))
        ctk.CTkLabel(
            frame_card,
            text=f"Mes actual: {datetime.now().strftime('%B %Y')}",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(0, 15))

        btn_generar = ctk.CTkButton(
            frame_card, text="📄 Generar Reporte PDF", height=45,
            font=ctk.CTkFont(size=14, weight="bold"), command=self.generar_reporte
        )
        btn_generar.pack(padx=20, pady=(0, 20))

        self.lbl_estado = ctk.CTkLabel(self, text="", text_color="gray")
        self.lbl_estado.pack(padx=30, pady=10, anchor="w")

    def generar_reporte(self):
        confirmar = messagebox.askyesno(
            "Confirmar generación",
            "¿Desea generar el reporte PDF de ventas del mes actual?"
        )
        if not confirmar:
            return

        mes_actual = datetime.now().strftime("%m_%Y")
        ruta = filedialog.asksaveasfilename(
            title="Guardar reporte como...",
            defaultextension=".pdf",
            initialfile=f"reporte_ventas_{mes_actual}.pdf",
            filetypes=[("Archivo PDF", "*.pdf")],
        )
        if not ruta:
            return 

        resultado = self.app.ejecutar_seguro(generar_reporte_pdf, ruta)
        if resultado:
            self.lbl_estado.configure(text=f"✅ Reporte generado: {resultado}", text_color="#16a34a")
            messagebox.showinfo("Reporte generado", f"El reporte se generó exitosamente en:\n{resultado}")


# ==========================================================================================
# PUNTO DE ENTRADA
# ==========================================================================================

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()