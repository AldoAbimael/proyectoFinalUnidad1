import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, List
from datetime import date, timedelta
from models.lector import Lector
from models.libro import Libro
from services.prestamo_service import PrestamoService
from services.lector_service import LectorService
from services.libro_service import LibroService
from services.exceptions import BusinessError, ValidationError
from ui.theme import ModernTheme


class PrestamoDialog(tk.Toplevel):
    """
    Formulario modal en Toplevel para el Alta de un Préstamo (RF-5).
    Selecciona lector y libro, mostrando stock y vigencia de 7 días.
    """

    def __init__(
        self,
        parent: tk.Widget,
        prestamo_service: PrestamoService,
        lector_service: LectorService,
        libro_service: LibroService,
        on_success: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.prestamo_service = prestamo_service
        self.lector_service = lector_service
        self.libro_service = libro_service
        self.on_success = on_success

        self.title("Registrar Nuevo Préstamo")
        self.geometry("520x460")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.lectores_lista: List[Lector] = []
        self.libros_lista: List[Libro] = []

        self._centrar(parent)
        self._cargar_catalogos()
        self._crear_widgets()

    def _centrar(self, parent: tk.Widget) -> None:
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w = 520
        h = 460
        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _cargar_catalogos(self) -> None:
        self.lectores_lista = self.lector_service.listar_lectores()
        self.libros_lista = self.libro_service.listar_libros()

    def _crear_widgets(self) -> None:
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        lbl_titulo = ttk.Label(
            main_frame,
            text="Alta de Préstamo Bibliotecario",
            font=ModernTheme.FONT_SUBTITLE,
            foreground=ModernTheme.COLOR_PRIMARY
        )
        lbl_titulo.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="w")

        # 1. Selección de Lector
        ttk.Label(main_frame, text="Seleccionar Lector: *", font=ModernTheme.FONT_BOLD).grid(
            row=1, column=0, sticky="w", pady=6
        )
        
        # Opciones para el Combobox de lectores
        lector_display_list = [
            f"[{l.folio}] {l.nombre} ({l.tipo}){' [INACTIVO]' if not l.activo else ''}"
            for l in self.lectores_lista
        ]
        self.cbo_lector = ttk.Combobox(
            main_frame,
            values=lector_display_list,
            state="readonly",
            width=42
        )
        self.cbo_lector.grid(row=1, column=1, sticky="ew", pady=6)
        if lector_display_list:
            self.cbo_lector.current(0)

        # 2. Selección de Libro
        ttk.Label(main_frame, text="Seleccionar Libro: *", font=ModernTheme.FONT_BOLD).grid(
            row=2, column=0, sticky="w", pady=6
        )
        libro_display_list = [
            f"{b.titulo} (Disp: {b.stock_disponible}/{b.stock_total}) [ISBN: {b.isbn}]"
            for b in self.libros_lista
        ]
        self.cbo_libro = ttk.Combobox(
            main_frame,
            values=libro_display_list,
            state="readonly",
            width=42
        )
        self.cbo_libro.grid(row=2, column=1, sticky="ew", pady=6)
        if libro_display_list:
            self.cbo_libro.current(0)

        # 3. Datos del préstamo calculados (7 días según la regla de negocio)
        hoy = date.today()
        vencimiento = hoy + timedelta(days=7)

        info_card = ttk.Frame(main_frame, style="Card.TFrame", padding=12)
        info_card.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(15, 10))

        ttk.Label(
            info_card,
            text="Detalles del Movimiento:",
            font=ModernTheme.FONT_BOLD,
            style="Card.TLabel",
            foreground=ModernTheme.COLOR_PRIMARY
        ).pack(anchor="w", pady=(0, 5))

        ttk.Label(
            info_card,
            text=f"• Fecha de Préstamo (Hoy): {hoy.isoformat()}",
            style="Card.TLabel"
        ).pack(anchor="w", pady=2)

        ttk.Label(
            info_card,
            text=f"• Vigencia: 7 días naturales",
            style="Card.TLabel"
        ).pack(anchor="w", pady=2)

        ttk.Label(
            info_card,
            text=f"• Fecha de Vencimiento: {vencimiento.isoformat()}",
            style="Card.TLabel",
            font=ModernTheme.FONT_BOLD,
            foreground=ModernTheme.COLOR_WARNING
        ).pack(anchor="w", pady=2)

        ttk.Label(
            info_card,
            text="• Se descontará 1 unidad del stock disponible del libro seleccionado.",
            style="Card.TLabel",
            font=ModernTheme.FONT_SMALL
        ).pack(anchor="w", pady=(4, 0))

        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0), sticky="e")

        btn_cancelar = ttk.Button(btn_frame, text="Cancelar", style="Secondary.TButton", command=self.destroy)
        btn_cancelar.pack(side="right", padx=(8, 0))

        btn_guardar = ttk.Button(btn_frame, text="Confirmar Préstamo", style="Primary.TButton", command=self._registrar)
        btn_guardar.pack(side="right")

    def _registrar(self) -> None:
        idx_lector = self.cbo_lector.current()
        idx_libro = self.cbo_libro.current()

        if idx_lector < 0 or idx_lector >= len(self.lectores_lista):
            messagebox.showerror("Error", "Debe seleccionar un lector.", parent=self)
            return

        if idx_libro < 0 or idx_libro >= len(self.libros_lista):
            messagebox.showerror("Error", "Debe seleccionar un libro.", parent=self)
            return

        lector_sel = self.lectores_lista[idx_lector]
        libro_sel = self.libros_lista[idx_libro]

        try:
            nuevo_prestamo = self.prestamo_service.registrar_prestamo(
                lector_id=lector_sel.id,
                libro_id=libro_sel.id,
                dias_prestamo=7
            )
            messagebox.showinfo(
                "Préstamo Registrado",
                f"Préstamo #{nuevo_prestamo.id} registrado exitosamente.\n\n"
                f"Lector: {lector_sel.nombre}\n"
                f"Libro: {libro_sel.titulo}\n"
                f"Fecha de vencimiento: {nuevo_prestamo.fecha_vencimiento}",
                parent=self
            )
            if self.on_success:
                self.on_success()
            self.destroy()

        except (ValidationError, BusinessError) as e:
            messagebox.showerror("Restricción de Negocio", str(e), parent=self)
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al registrar el préstamo: {e}", parent=self)
