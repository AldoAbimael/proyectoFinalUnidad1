import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
from models.prestamo import PrestamoDetalle
from services.prestamo_service import PrestamoService
from services.lector_service import LectorService
from services.libro_service import LibroService
from services.exceptions import BusinessError, ValidationError
from ui.dialogs.prestamo_dialog import PrestamoDialog
from ui.theme import ModernTheme


class PrestamosView(ttk.Frame):
    """
    Vista de Movimiento de Negocio: Préstamos y Devoluciones.
    Cumple con:
    - RF-5: Cruce de entidades (Lector + Libro).
    - RF-6: Búsqueda y filtrado en Treeview por estado.
    - RF-7: Consulta SQL con JOIN obligatorio visible en pantalla.
    - RF-9: Confirmación con messagebox antes de registrar la devolución.
    """

    def __init__(
        self,
        parent: tk.Widget,
        prestamo_service: PrestamoService,
        lector_service: LectorService,
        libro_service: LibroService
    ):
        super().__init__(parent, padding=15)
        self.prestamo_service = prestamo_service
        self.lector_service = lector_service
        self.libro_service = libro_service
        self.prestamos_actuales: List[PrestamoDetalle] = []

        self._crear_interfaz()
        self.cargar_datos()

    def _crear_interfaz(self) -> None:
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", pady=(0, 10))

        lbl_titulo = ttk.Label(
            header_frame,
            text="Movimiento de Préstamos y Devoluciones (JOIN SQL)",
            font=ModernTheme.FONT_TITLE,
            foreground=ModernTheme.COLOR_PRIMARY
        )
        lbl_titulo.pack(side="left")

        # Barra de filtros y búsqueda (RF-6)
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 10))

        ttk.Label(toolbar, text="Buscar:", font=ModernTheme.FONT_BOLD).pack(side="left", padx=(0, 5))
        self.txt_buscar = ttk.Entry(toolbar, width=24)
        self.txt_buscar.pack(side="left", padx=(0, 10))
        self.txt_buscar.bind("<KeyRelease>", lambda e: self.cargar_datos())

        ttk.Label(toolbar, text="Filtrar por Estado:", font=ModernTheme.FONT_BOLD).pack(side="left", padx=(0, 5))
        self.cbo_estado = ttk.Combobox(
            toolbar,
            values=["Todos", "Activos", "Devueltos"],
            state="readonly",
            width=12
        )
        self.cbo_estado.set("Todos")
        self.cbo_estado.pack(side="left", padx=(0, 10))
        self.cbo_estado.bind("<<ComboboxSelected>>", lambda e: self.cargar_datos())

        btn_limpiar = ttk.Button(
            toolbar,
            text="Limpiar Filtros",
            style="Secondary.TButton",
            command=self._limpiar_filtros
        )
        btn_limpiar.pack(side="left")

        # Botón para Registrar Préstamo (Alta del Proceso de Negocio)
        btn_nuevo = ttk.Button(
            toolbar,
            text="+ Registrar Préstamo",
            style="Primary.TButton",
            command=self._abrir_nuevo_prestamo
        )
        btn_nuevo.pack(side="right")

        # Treeview con JOIN (RF-7)
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        columnas = (
            "id",
            "folio_lector",
            "nombre_lector",
            "tipo_lector",
            "isbn_libro",
            "titulo_libro",
            "fecha_prestamo",
            "fecha_vencimiento",
            "fecha_devolucion",
            "estado",
            "condicion"
        )

        self.tree = ttk.Treeview(
            tree_frame,
            columns=columnas,
            show="headings",
            selectmode="browse"
        )

        # Encabezados
        self.tree.heading("id", text="Folio Préstamo")
        self.tree.heading("folio_lector", text="Folio Lector")
        self.tree.heading("nombre_lector", text="Lector (JOIN)")
        self.tree.heading("tipo_lector", text="Tipo")
        self.tree.heading("isbn_libro", text="ISBN")
        self.tree.heading("titulo_libro", text="Título Libro (JOIN)")
        self.tree.heading("fecha_prestamo", text="F. Préstamo")
        self.tree.heading("fecha_vencimiento", text="F. Vencimiento")
        self.tree.heading("fecha_devolucion", text="F. Devolución")
        self.tree.heading("estado", text="Estado")
        self.tree.heading("condicion", text="Condición")

        # Anchos
        self.tree.column("id", width=85, anchor="center")
        self.tree.column("folio_lector", width=80, anchor="center")
        self.tree.column("nombre_lector", width=160, anchor="w")
        self.tree.column("tipo_lector", width=75, anchor="center")
        self.tree.column("isbn_libro", width=105, anchor="w")
        self.tree.column("titulo_libro", width=190, anchor="w")
        self.tree.column("fecha_prestamo", width=85, anchor="center")
        self.tree.column("fecha_vencimiento", width=95, anchor="center")
        self.tree.column("fecha_devolucion", width=95, anchor="center")
        self.tree.column("estado", width=75, anchor="center")
        self.tree.column("condicion", width=95, anchor="center")

        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Tags de estilo para estados
        self.tree.tag_configure("atrasado", background="#fee2e2", foreground="#991b1b")
        self.tree.tag_configure("devuelto", background="#f0fdf4", foreground="#166534")
        self.tree.tag_configure("activo", background="#eff6ff", foreground="#1e40af")

        # Barra inferior de acciones
        bottom_bar = ttk.Frame(self)
        bottom_bar.pack(fill="x", pady=(10, 0))

        # Acción de Cierre: Devolución
        btn_devolucion = ttk.Button(
            bottom_bar,
            text="✔ Registrar Devolución (Cierre)",
            style="Success.TButton",
            command=self._registrar_devolucion
        )
        btn_devolucion.pack(side="left", padx=(0, 10))

        self.lbl_conteo = ttk.Label(bottom_bar, text="", font=ModernTheme.FONT_SMALL, foreground=ModernTheme.COLOR_MUTED)
        self.lbl_conteo.pack(side="right")

    def cargar_datos(self) -> None:
        """Carga los préstamos ejecutando la consulta con JOIN SQL (RF-7)."""
        estado_sel = self.cbo_estado.get()
        filtro_estado = None
        if estado_sel == "Activos":
            filtro_estado = "activo"
        elif estado_sel == "Devueltos":
            filtro_estado = "devuelto"

        busqueda = self.txt_buscar.get().strip()

        self.prestamos_actuales = self.prestamo_service.listar_prestamos(
            filtro_estado=filtro_estado,
            busqueda=busqueda if busqueda else None
        )
        self._llenar_treeview(self.prestamos_actuales)

    def _llenar_treeview(self, prestamos: List[PrestamoDetalle]) -> None:
        self.tree.delete(*self.tree.get_children())
        for p in prestamos:
            f_dev = p.fecha_devolucion if p.fecha_devolucion else "Pendiente"
            estado_cap = p.estado.capitalize()

            if p.estado == "activo":
                if p.esta_atrasado:
                    condicion = "ATRASADO"
                    tag = "atrasado"
                else:
                    condicion = "Vigente"
                    tag = "activo"
            else:
                condicion = "Concluido"
                tag = "devuelto"

            self.tree.insert(
                "",
                "end",
                iid=str(p.id),
                values=(
                    f"#{p.id}",
                    p.lector_folio,
                    p.lector_nombre,
                    p.lector_tipo.capitalize(),
                    p.libro_isbn,
                    p.libro_titulo,
                    p.fecha_prestamo,
                    p.fecha_vencimiento,
                    f_dev,
                    estado_cap,
                    condicion
                ),
                tags=(tag,)
            )

        self.lbl_conteo.config(text=f"Total: {len(prestamos)} movimientos registrados")

    def _limpiar_filtros(self) -> None:
        self.txt_buscar.delete(0, tk.END)
        self.cbo_estado.set("Todos")
        self.cargar_datos()

    def _abrir_nuevo_prestamo(self) -> None:
        PrestamoDialog(
            self,
            prestamo_service=self.prestamo_service,
            lector_service=self.lector_service,
            libro_service=self.libro_service,
            on_success=self.cargar_datos
        )

    def _registrar_devolucion(self) -> None:
        """
        Acción de Cierre del proceso de negocio:
        RF-9: Confirmación con messagebox antes de una acción irreversible.
        Suma 1 al stock disponible y marca fecha_devolucion.
        """
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selección requerida", "Por favor seleccione un préstamo de la lista.", parent=self)
            return

        prestamo_id = int(selected[0])
        # Buscar el objeto en los actuales
        detalle = next((p for p in self.prestamos_actuales if p.id == prestamo_id), None)
        if not detalle:
            return

        if detalle.estado == "devuelto":
            messagebox.showinfo(
                "Préstamo ya devuelto",
                f"El préstamo #{prestamo_id} ya fue devuelto previamente el {detalle.fecha_devolucion}.",
                parent=self
            )
            return

        # Confirmación RF-9
        if not messagebox.askyesno(
            "Confirmación de Devolución (RF-9)",
            f"¿Confirma la devolución del libro '{detalle.libro_titulo}' prestado a '{detalle.lector_nombre}'?\n\n"
            "Se sumará 1 unidad al stock disponible del libro y se cerrará el préstamo.",
            parent=self
        ):
            return

        try:
            self.prestamo_service.registrar_devolucion(prestamo_id)
            messagebox.showinfo(
                "Devolución Exitosa",
                f"La devolución del préstamo #{prestamo_id} se registró correctamente. "
                "El stock disponible fue actualizado.",
                parent=self
            )
            self.cargar_datos()
        except BusinessError as e:
            messagebox.showerror("Error al Devolver", str(e), parent=self)
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error: {e}", parent=self)
