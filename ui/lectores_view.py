import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
from models.lector import Lector
from services.lector_service import LectorService
from services.exceptions import BusinessError, ValidationError
from ui.dialogs.lector_dialog import LectorDialog
from ui.theme import ModernTheme


class LectoresView(ttk.Frame):
    """
    Vista de Catálogo B: Gestión de Lectores.
    Treeview con columnas completas, buscador visible (RF-6),
    acciones de Alta, Edición, Desactivación/Baja con confirmación (RF-9, RF-10).
    """

    def __init__(self, parent: tk.Widget, lector_service: LectorService):
        super().__init__(parent, padding=15)
        self.lector_service = lector_service
        self.lectores_actuales: List[Lector] = []

        self._crear_interfaz()
        self.cargar_datos()

    def _crear_interfaz(self) -> None:
        # Encabezado de la vista
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", pady=(0, 10))

        lbl_titulo = ttk.Label(
            header_frame,
            text="Padrón de Lectores",
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

        btn_nuevo = ttk.Button(
            toolbar,
            text="+ Nuevo Lector",
            style="Primary.TButton",
            command=self._abrir_nuevo
        )
        btn_nuevo.pack(side="right")

        # Contenedor del Treeview con scrollbars
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        columnas = ("id", "folio", "nombre", "correo", "telefono", "tipo", "estado")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columnas,
            show="headings",
            selectmode="browse"
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("folio", text="Folio")
        self.tree.heading("nombre", text="Nombre Completo")
        self.tree.heading("correo", text="Correo Electrónico")
        self.tree.heading("telefono", text="Teléfono")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("estado", text="Estado")

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("folio", width=90, anchor="center")
        self.tree.column("nombre", width=220, anchor="w")
        self.tree.column("correo", width=220, anchor="w")
        self.tree.column("telefono", width=120, anchor="w")
        self.tree.column("tipo", width=90, anchor="center")
        self.tree.column("estado", width=90, anchor="center")

        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree.tag_configure("inactivo", background="#fee2e2", foreground="#991b1b")

        # Barra inferior de acciones
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
        solo_act = self.var_solo_activos.get()
        busqueda = self.txt_buscar.get().strip()

        if busqueda:
            self.lectores_actuales = self.lector_service.buscar_lectores(busqueda, solo_activos=solo_act)
        else:
            self.lectores_actuales = self.lector_service.listar_lectores(solo_activos=solo_act)

        self._llenar_treeview(self.lectores_actuales)

    def _llenar_treeview(self, lectores: List[Lector]) -> None:
        self.tree.delete(*self.tree.get_children())
        for l in lectores:
            estado_txt = "Activo" if l.activo else "Inactivo"
            tags = () if l.activo else ("inactivo",)

            self.tree.insert(
                "",
                "end",
                iid=str(l.id),
                values=(
                    l.id,
                    l.folio,
                    l.nombre,
                    l.correo,
                    l.telefono,
                    l.tipo.capitalize(),
                    estado_txt
                ),
                tags=tags
            )

        self.lbl_conteo.config(text=f"Total: {len(lectores)} lectores mostrados")

    def _filtrar(self) -> None:
        self.cargar_datos()

    def _limpiar_busqueda(self) -> None:
        self.txt_buscar.delete(0, tk.END)
        self.cargar_datos()

    def _obtener_seleccionado(self) -> Optional[Lector]:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selección requerida", "Por favor seleccione un lector de la tabla.", parent=self)
            return None
        lector_id = int(selected[0])
        return self.lector_service.obtener_lector(lector_id)

    def _abrir_nuevo(self) -> None:
        LectorDialog(self, self.lector_service, on_success=self.cargar_datos)

    def _abrir_editar(self) -> None:
        lector = self._obtener_seleccionado()
        if lector:
            LectorDialog(self, self.lector_service, lector=lector, on_success=self.cargar_datos)

    def _alternar_estado(self) -> None:
        lector = self._obtener_seleccionado()
        if not lector:
            return

        nuevo_estado = 0 if lector.activo else 1
        accion = "desactivar" if nuevo_estado == 0 else "reactivar"

        if not messagebox.askyesno(
            "Confirmación (RF-9)",
            f"¿Está seguro de que desea {accion} al lector '{lector.nombre}'?",
            parent=self
        ):
            return

        try:
            self.lector_service.cambiar_estado(lector.id, nuevo_estado)
            messagebox.showinfo("Éxito", f"Lector {accion}do con éxito.", parent=self)
            self.cargar_datos()
        except BusinessError as e:
            messagebox.showerror("No Permitido (RF-10)", str(e), parent=self)

    def _eliminar_o_desactivar(self) -> None:
        lector = self._obtener_seleccionado()
        if not lector:
            return

        if not messagebox.askyesno(
            "Confirmación de Eliminación (RF-9)",
            f"¿Desea dar de baja o eliminar al lector '{lector.nombre}' (Folio: {lector.folio})?\n\n"
            "Nota: Si el lector tiene préstamos activos no podrá eliminarse; si tiene historial será desactivado.",
            parent=self
        ):
            return

        try:
            accion, mensaje = self.lector_service.eliminar_o_desactivar(lector.id)
            messagebox.showinfo("Resultado", mensaje, parent=self)
            self.cargar_datos()
        except BusinessError as e:
            messagebox.showerror("Integridad Violada (RF-10)", str(e), parent=self)
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al procesar el lector: {e}", parent=self)
