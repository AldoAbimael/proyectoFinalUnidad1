import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
from models.libro import Libro
from services.libro_service import LibroService
from services.exceptions import BusinessError, ValidationError
from ui.dialogs.libro_dialog import LibroDialog
from ui.theme import ModernTheme


class LibrosView(ttk.Frame):
    """
    Vista de Catálogo A: Gestión de Libros.
    Treeview con columnas completas, buscador en tiempo real (RF-6),
    acciones de Alta, Edición, Desactivación/Baja con confirmación (RF-9, RF-10).
    """

    def __init__(self, parent: tk.Widget, libro_service: LibroService):
        super().__init__(parent, padding=15)
        self.libro_service = libro_service
        self.libros_actuales: List[Libro] = []

        self._crear_interfaz()
        self.cargar_datos()

    def _crear_interfaz(self) -> None:
        # Encabezado de la vista
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", pady=(0, 10))

        lbl_titulo = ttk.Label(
            header_frame,
            text="Catálogo de Libros (Acervo)",
            font=ModernTheme.FONT_TITLE,
            foreground=ModernTheme.COLOR_PRIMARY
        )
        lbl_titulo.pack(side="left")

        # Barra de búsqueda y controles de filtro (RF-6)
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 10))

        ttk.Label(toolbar, text="Buscar:", font=ModernTheme.FONT_BOLD).pack(side="left", padx=(0, 5))
        self.txt_buscar = ttk.Entry(toolbar, width=28)
        self.txt_buscar.pack(side="left", padx=(0, 8))
        self.txt_buscar.bind("<KeyRelease>", lambda e: self._filtrar())

        self.var_solo_activos = tk.BooleanVar(value=False)
        chk_activos = ttk.Checkbutton(
            toolbar,
            text="Solo activos",
            variable=self.var_solo_activos,
            command=self.cargar_datos
        )
        chk_activos.pack(side="left", padx=(0, 15))

        btn_limpiar = ttk.Button(
            toolbar,
            text="Limpiar Búsqueda",
            style="Secondary.TButton",
            command=self._limpiar_busqueda
        )
        btn_limpiar.pack(side="left")

        # Botones de Acción (derecha)
        btn_nuevo = ttk.Button(
            toolbar,
            text="+ Nuevo Libro",
            style="Primary.TButton",
            command=self._abrir_nuevo
        )
        btn_nuevo.pack(side="right")

        # Contenedor del Treeview con scrollbars
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        columnas = ("id", "isbn", "titulo", "autor", "categoria", "anio", "total", "disponible", "estado")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columnas,
            show="headings",
            selectmode="browse"
        )

        # Definir encabezados
        self.tree.heading("id", text="ID")
        self.tree.heading("isbn", text="ISBN")
        self.tree.heading("titulo", text="Título")
        self.tree.heading("autor", text="Autor")
        self.tree.heading("categoria", text="Categoría")
        self.tree.heading("anio", text="Año")
        self.tree.heading("total", text="Stock Total")
        self.tree.heading("disponible", text="Stock Disp.")
        self.tree.heading("estado", text="Estado")

        # Anchos y alineaciones
        self.tree.column("id", width=45, anchor="center")
        self.tree.column("isbn", width=120, anchor="w")
        self.tree.column("titulo", width=220, anchor="w")
        self.tree.column("autor", width=160, anchor="w")
        self.tree.column("categoria", width=110, anchor="w")
        self.tree.column("anio", width=60, anchor="center")
        self.tree.column("total", width=80, anchor="center")
        self.tree.column("disponible", width=80, anchor="center")
        self.tree.column("estado", width=90, anchor="center")

        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Etiquetas visuales para filas
        self.tree.tag_configure("inactivo", background="#fee2e2", foreground="#991b1b")
        self.tree.tag_configure("sinstock", background="#fef3c7", foreground="#92400e")

        # Barra de acciones inferiores
        bottom_bar = ttk.Frame(self)
        bottom_bar.pack(fill="x", pady=(10, 0))

        btn_editar = ttk.Button(
            bottom_bar,
            text="Editar Seleccionado",
            style="Secondary.TButton",
            command=self._abrir_editar
        )
        btn_editar.pack(side="left", padx=(0, 8))

        btn_baja = ttk.Button(
            bottom_bar,
            text="Eliminar / Desactivar",
            style="Danger.TButton",
            command=self._eliminar_o_desactivar
        )
        btn_baja.pack(side="left", padx=(0, 8))

        btn_toggle = ttk.Button(
            bottom_bar,
            text="Alternar Activo / Inactivo",
            style="Secondary.TButton",
            command=self._alternar_estado
        )
        btn_toggle.pack(side="left", padx=(0, 8))

        self.lbl_conteo = ttk.Label(bottom_bar, text="", font=ModernTheme.FONT_SMALL, foreground=ModernTheme.COLOR_MUTED)
        self.lbl_conteo.pack(side="right")

    def cargar_datos(self) -> None:
        """Carga los libros desde el servicio."""
        solo_act = self.var_solo_activos.get()
        busqueda = self.txt_buscar.get().strip()

        if busqueda:
            self.libros_actuales = self.libro_service.buscar_libros(busqueda, solo_activos=solo_act)
        else:
            self.libros_actuales = self.libro_service.listar_libros(solo_activos=solo_act)

        self._llenar_treeview(self.libros_actuales)

    def _llenar_treeview(self, libros: List[Libro]) -> None:
        self.tree.delete(*self.tree.get_children())
        for l in libros:
            estado_txt = "Activo" if l.activo else "Inactivo"
            tags = ()
            if not l.activo:
                tags = ("inactivo",)
            elif l.stock_disponible <= 0:
                tags = ("sinstock",)

            self.tree.insert(
                "",
                "end",
                iid=str(l.id),
                values=(
                    l.id,
                    l.isbn,
                    l.titulo,
                    l.autor,
                    l.categoria,
                    l.anio,
                    l.stock_total,
                    l.stock_disponible,
                    estado_txt
                ),
                tags=tags
            )

        self.lbl_conteo.config(text=f"Total: {len(libros)} libros mostrados")

    def _filtrar(self) -> None:
        self.cargar_datos()

    def _limpiar_busqueda(self) -> None:
        self.txt_buscar.delete(0, tk.END)
        self.cargar_datos()

    def _obtener_seleccionado(self) -> Optional[Libro]:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selección requerida", "Por favor seleccione un libro de la tabla.", parent=self)
            return None
        libro_id = int(selected[0])
        return self.libro_service.obtener_libro(libro_id)

    def _abrir_nuevo(self) -> None:
        LibroDialog(self, self.libro_service, on_success=self.cargar_datos)

    def _abrir_editar(self) -> None:
        libro = self._obtener_seleccionado()
        if libro:
            LibroDialog(self, self.libro_service, libro=libro, on_success=self.cargar_datos)

    def _alternar_estado(self) -> None:
        libro = self._obtener_seleccionado()
        if not libro:
            return

        nuevo_estado = 0 if libro.activo else 1
        accion = "desactivar" if nuevo_estado == 0 else "reactivar"

        if not messagebox.askyesno(
            "Confirmación (RF-9)",
            f"¿Está seguro de que desea {accion} el libro '{libro.titulo}'?",
            parent=self
        ):
            return

        try:
            self.libro_service.cambiar_estado(libro.id, nuevo_estado)
            messagebox.showinfo("Éxito", f"Libro {accion}do con éxito.", parent=self)
            self.cargar_datos()
        except BusinessError as e:
            messagebox.showerror("No Permitido (RF-10)", str(e), parent=self)

    def _eliminar_o_desactivar(self) -> None:
        """
        RF-9: Confirmación con messagebox antes de borrar.
        RF-10: Integridad: si tiene movimientos activos muestra error; si tiene historial desactiva.
        """
        libro = self._obtener_seleccionado()
        if not libro:
            return

        if not messagebox.askyesno(
            "Confirmación de Eliminación (RF-9)",
            f"¿Desea dar de baja o eliminar el libro '{libro.titulo}' (ISBN: {libro.isbn})?\n\n"
            "Nota: Si el libro tiene préstamos activos no podrá eliminarse; si tiene historial será desactivado.",
            parent=self
        ):
            return

        try:
            accion, mensaje = self.libro_service.eliminar_o_desactivar(libro.id)
            messagebox.showinfo("Resultado", mensaje, parent=self)
            self.cargar_datos()
        except BusinessError as e:
            messagebox.showerror("Integridad Violada (RF-10)", str(e), parent=self)
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al procesar el libro: {e}", parent=self)
