import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime
from typing import List
from models.prestamo import PrestamoDetalle
from services.prestamo_service import PrestamoService
from ui.theme import ModernTheme


class ReportesView(ttk.Frame):
    """
    Vista de Reporte del Caso Problemático del Dominio (RF-8):
    Lista préstamos activos con fecha de vencimiento menor al día actual (atrasados).
    Incluye la opción de exportar a archivo CSV (Extra opcional A.6).
    """

    def __init__(self, parent: tk.Widget, prestamo_service: PrestamoService):
        super().__init__(parent, padding=15)
        self.prestamo_service = prestamo_service
        self.atrasados: List[PrestamoDetalle] = []

        self._crear_interfaz()
        self.cargar_datos()

    def _crear_interfaz(self) -> None:
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", pady=(0, 10))

        lbl_titulo = ttk.Label(
            header_frame,
            text="Reporte de Préstamos Atrasados (Caso Problemático RF-8)",
            font=ModernTheme.FONT_TITLE,
            foreground=ModernTheme.COLOR_DANGER
        )
        lbl_titulo.pack(side="left")

        # Barra de herramientas y botones
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 10))

        btn_actualizar = ttk.Button(
            toolbar,
            text="Actualizar Reporte",
            style="Secondary.TButton",
            command=self.cargar_datos
        )
        btn_actualizar.pack(side="left", padx=(0, 10))

        btn_exportar = ttk.Button(
            toolbar,
            text="📥 Exportar a CSV (Extra)",
            style="Primary.TButton",
            command=self._exportar_csv
        )
        btn_exportar.pack(side="left")

        # Tarjeta informativa de advertencia
        info_card = ttk.Frame(self, style="Card.TFrame", padding=12)
        info_card.pack(fill="x", pady=(0, 10))

        self.lbl_resumen = ttk.Label(
            info_card,
            text="",
            font=ModernTheme.FONT_BOLD,
            style="Card.TLabel",
            foreground=ModernTheme.COLOR_DANGER
        )
        self.lbl_resumen.pack(anchor="w")

        lbl_desc = ttk.Label(
            info_card,
            text="Este reporte filtra automáticamente aquellos préstamos que continúan en estado 'activo' "
                 "pero cuya fecha límite de entrega (vencimiento) expiró respecto a la fecha actual del sistema.",
            style="Card.TLabel",
            font=ModernTheme.FONT_SMALL
        )
        lbl_desc.pack(anchor="w", pady=(3, 0))

        # Treeview de préstamos atrasados
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
            "dias_retraso"
        )

        self.tree = ttk.Treeview(
            tree_frame,
            columns=columnas,
            show="headings",
            selectmode="browse"
        )

        self.tree.heading("id", text="Folio")
        self.tree.heading("folio_lector", text="Folio Lector")
        self.tree.heading("nombre_lector", text="Lector Deudor")
        self.tree.heading("tipo_lector", text="Tipo")
        self.tree.heading("isbn_libro", text="ISBN")
        self.tree.heading("titulo_libro", text="Título del Libro")
        self.tree.heading("fecha_prestamo", text="F. Préstamo")
        self.tree.heading("fecha_vencimiento", text="F. Límite Vencida")
        self.tree.heading("dias_retraso", text="Días de Retraso")

        self.tree.column("id", width=65, anchor="center")
        self.tree.column("folio_lector", width=85, anchor="center")
        self.tree.column("nombre_lector", width=180, anchor="w")
        self.tree.column("tipo_lector", width=80, anchor="center")
        self.tree.column("isbn_libro", width=110, anchor="w")
        self.tree.column("titulo_libro", width=220, anchor="w")
        self.tree.column("fecha_prestamo", width=90, anchor="center")
        self.tree.column("fecha_vencimiento", width=110, anchor="center")
        self.tree.column("dias_retraso", width=110, anchor="center")

        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree.tag_configure("atraso", background="#fee2e2", foreground="#991b1b")

    def cargar_datos(self) -> None:
        """Consulta el reporte de casos atrasados desde el servicio."""
        self.atrasados = self.prestamo_service.obtener_prestamos_atrasados()
        self.tree.delete(*self.tree.get_children())
        hoy = date.today()

        for p in self.atrasados:
            try:
                f_venc = datetime.strptime(p.fecha_vencimiento, "%Y-%m-%d").date()
                dias = (hoy - f_venc).days
            except Exception:
                dias = "N/D"

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
                    f"{dias} día(s)"
                ),
                tags=("atraso",)
            )

        total = len(self.atrasados)
        if total == 0:
            self.lbl_resumen.config(
                text="✔ No hay préstamos atrasados. Todos los préstamos activos están dentro de su periodo de vigencia.",
                foreground=ModernTheme.COLOR_SUCCESS
            )
        else:
            self.lbl_resumen.config(
                text=f"⚠ ATENCIÓN: Se encontraron {total} préstamo(s) con fecha de entrega expirada que requieren seguimiento.",
                foreground=ModernTheme.COLOR_DANGER
            )

    def _exportar_csv(self) -> None:
        if not self.atrasados:
            messagebox.showinfo("Exportar", "No hay préstamos atrasados para exportar.", parent=self)
            return

        nombre_defecto = f"prestamos_atrasados_{date.today().isoformat()}.csv"
        archivo = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar Reporte CSV",
            defaultextension=".csv",
            initialfile=nombre_defecto,
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )

        if not archivo:
            return

        try:
            total_exportados = self.prestamo_service.exportar_reporte_csv(archivo)
            messagebox.showinfo(
                "Exportación Exitosa",
                f"Se exportaron correctamente {total_exportados} registros a:\n{archivo}",
                parent=self
            )
        except Exception as e:
            messagebox.showerror("Error al Exportar", f"No se pudo guardar el archivo CSV: {e}", parent=self)
