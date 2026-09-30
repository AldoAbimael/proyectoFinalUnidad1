import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from models.lector import Lector
from services.lector_service import LectorService
from services.exceptions import BusinessError, ValidationError, IntegrityConflictError
from ui.theme import ModernTheme


class LectorDialog(tk.Toplevel):
    """
    Formulario modal en Toplevel para Crear o Editar un Lector (RNF-3).
    Captura todas las excepciones de integridad y formato (RNF-4).
    """

    def __init__(
        self,
        parent: tk.Widget,
        lector_service: LectorService,
        lector: Optional[Lector] = None,
        on_success: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.lector_service = lector_service
        self.lector = lector
        self.on_success = on_success

        self.title("Editar Lector" if lector else "Nuevo Lector")
        self.geometry("460x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._centrar(parent)
        self._crear_widgets()
        if self.lector:
            self._cargar_datos()

    def _centrar(self, parent: tk.Widget) -> None:
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w = 460
        h = 420
        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _crear_widgets(self) -> None:
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        titulo_texto = "Editar Registro de Lector" if self.lector else "Registrar Nuevo Lector"
        lbl_titulo = ttk.Label(main_frame, text=titulo_texto, font=ModernTheme.FONT_SUBTITLE, foreground=ModernTheme.COLOR_PRIMARY)
        lbl_titulo.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="w")

        # Campos
        ttk.Label(main_frame, text="Folio: *", font=ModernTheme.FONT_BOLD).grid(row=1, column=0, sticky="w", pady=4)
        self.txt_folio = ttk.Entry(main_frame, width=30)
        self.txt_folio.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(main_frame, text="Nombre Completo: *", font=ModernTheme.FONT_BOLD).grid(row=2, column=0, sticky="w", pady=4)
        self.txt_nombre = ttk.Entry(main_frame, width=30)
        self.txt_nombre.grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(main_frame, text="Correo Electrónico: *", font=ModernTheme.FONT_BOLD).grid(row=3, column=0, sticky="w", pady=4)
        self.txt_correo = ttk.Entry(main_frame, width=30)
        self.txt_correo.grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(main_frame, text="Teléfono: *", font=ModernTheme.FONT_BOLD).grid(row=4, column=0, sticky="w", pady=4)
        self.txt_telefono = ttk.Entry(main_frame, width=30)
        self.txt_telefono.grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(main_frame, text="Tipo de Lector: *", font=ModernTheme.FONT_BOLD).grid(row=5, column=0, sticky="w", pady=4)
        self.cbo_tipo = ttk.Combobox(
            main_frame,
            values=["alumno", "docente", "externo"],
            state="readonly",
            width=28
        )
        self.cbo_tipo.grid(row=5, column=1, sticky="ew", pady=4)
        self.cbo_tipo.set("alumno")

        # Activo
        self.var_activo = tk.IntVar(value=1)
        self.chk_activo = ttk.Checkbutton(
            main_frame,
            text="Lector activo (habilitado para solicitar préstamos)",
            variable=self.var_activo
        )
        self.chk_activo.grid(row=6, column=1, sticky="w", pady=8)

        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=(15, 0), sticky="e")

        btn_cancelar = ttk.Button(btn_frame, text="Cancelar", style="Secondary.TButton", command=self.destroy)
        btn_cancelar.pack(side="right", padx=(8, 0))

        btn_guardar = ttk.Button(btn_frame, text="Guardar", style="Primary.TButton", command=self._guardar)
        btn_guardar.pack(side="right")

    def _cargar_datos(self) -> None:
        if not self.lector:
            return
        self.txt_folio.insert(0, self.lector.folio)
        self.txt_nombre.insert(0, self.lector.nombre)
        self.txt_correo.insert(0, self.lector.correo)
        self.txt_telefono.insert(0, self.lector.telefono)
        self.cbo_tipo.set(self.lector.tipo)
        self.var_activo.set(self.lector.activo)

    def _guardar(self) -> None:
        folio = self.txt_folio.get()
        nombre = self.txt_nombre.get()
        correo = self.txt_correo.get()
        telefono = self.txt_telefono.get()
        tipo = self.cbo_tipo.get()
        activo = self.var_activo.get()

        try:
            if self.lector:
                self.lector_service.actualizar_lector(
                    lector_id=self.lector.id,
                    folio=folio,
                    nombre=nombre,
                    correo=correo,
                    telefono=telefono,
                    tipo=tipo,
                    activo=activo
                )
                messagebox.showinfo("Éxito", "Lector actualizado correctamente.", parent=self)
            else:
                self.lector_service.crear_lector(
                    folio=folio,
                    nombre=nombre,
                    correo=correo,
                    telefono=telefono,
                    tipo=tipo,
                    activo=activo
                )
                messagebox.showinfo("Éxito", "Lector registrado exitosamente.", parent=self)

            if self.on_success:
                self.on_success()
            self.destroy()

        except (ValidationError, IntegrityConflictError, BusinessError) as e:
            messagebox.showerror("Error de Validación", str(e), parent=self)
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al procesar el lector: {e}", parent=self)
