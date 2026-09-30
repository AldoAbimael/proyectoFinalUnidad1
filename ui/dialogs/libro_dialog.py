import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from models.libro import Libro
from services.libro_service import LibroService
from services.exceptions import BusinessError, ValidationError, IntegrityConflictError
from ui.theme import ModernTheme


class LibroDialog(tk.Toplevel):
    """
    Formulario modal en Toplevel para Crear o Editar un Libro (RNF-3).
    Captura todas las excepciones de integridad y validación (RNF-4).
    """

    def __init__(
        self,
        parent: tk.Widget,
        libro_service: LibroService,
        libro: Optional[Libro] = None,
        on_success: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)
        self.libro_service = libro_service
        self.libro = libro
        self.on_success = on_success

        self.title("Editar Libro" if libro else "Nuevo Libro")
        self.geometry("480x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Centrar sobre la ventana padre
        self._centrar(parent)

        self._crear_widgets()
        if self.libro:
            self._cargar_datos()

    def _centrar(self, parent: tk.Widget) -> None:
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w = 480
        h = 480
        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _crear_widgets(self) -> None:
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        titulo_texto = "Editar Registro de Libro" if self.libro else "Registrar Nuevo Libro"
        lbl_titulo = ttk.Label(main_frame, text=titulo_texto, font=ModernTheme.FONT_SUBTITLE, foreground=ModernTheme.COLOR_PRIMARY)
        lbl_titulo.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="w")

        # Campos
        ttk.Label(main_frame, text="ISBN: *", font=ModernTheme.FONT_BOLD).grid(row=1, column=0, sticky="w", pady=4)
        self.txt_isbn = ttk.Entry(main_frame, width=32)
        self.txt_isbn.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(main_frame, text="Título: *", font=ModernTheme.FONT_BOLD).grid(row=2, column=0, sticky="w", pady=4)
        self.txt_titulo = ttk.Entry(main_frame, width=32)
        self.txt_titulo.grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(main_frame, text="Autor: *", font=ModernTheme.FONT_BOLD).grid(row=3, column=0, sticky="w", pady=4)
        self.txt_autor = ttk.Entry(main_frame, width=32)
        self.txt_autor.grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(main_frame, text="Categoría: *", font=ModernTheme.FONT_BOLD).grid(row=4, column=0, sticky="w", pady=4)
        self.cbo_categoria = ttk.Combobox(
            main_frame,
            values=["Software", "Programación", "Arquitectura", "Algoritmos", "Bases de Datos", "Redes", "Otro"],
            width=30
        )
        self.cbo_categoria.grid(row=4, column=1, sticky="ew", pady=4)
        self.cbo_categoria.set("Programación")

        ttk.Label(main_frame, text="Año de Publicación: *", font=ModernTheme.FONT_BOLD).grid(row=5, column=0, sticky="w", pady=4)
        self.txt_anio = ttk.Entry(main_frame, width=32)
        self.txt_anio.grid(row=5, column=1, sticky="ew", pady=4)
        self.txt_anio.insert(0, "2023")

        ttk.Label(main_frame, text="Stock Total: *", font=ModernTheme.FONT_BOLD).grid(row=6, column=0, sticky="w", pady=4)
        self.txt_stock_total = ttk.Entry(main_frame, width=32)
        self.txt_stock_total.grid(row=6, column=1, sticky="ew", pady=4)
        self.txt_stock_total.insert(0, "1")

        ttk.Label(main_frame, text="Stock Disponible: *", font=ModernTheme.FONT_BOLD).grid(row=7, column=0, sticky="w", pady=4)
        self.txt_stock_disponible = ttk.Entry(main_frame, width=32)
        self.txt_stock_disponible.grid(row=7, column=1, sticky="ew", pady=4)
        self.txt_stock_disponible.insert(0, "1")

        # Estado Activo (Check)
        self.var_activo = tk.IntVar(value=1)
        self.chk_activo = ttk.Checkbutton(
            main_frame,
            text="Libro activo para préstamos",
            variable=self.var_activo
        )
        self.chk_activo.grid(row=8, column=1, sticky="w", pady=8)

        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=9, column=0, columnspan=2, pady=(15, 0), sticky="e")

        btn_cancelar = ttk.Button(btn_frame, text="Cancelar", style="Secondary.TButton", command=self.destroy)
        btn_cancelar.pack(side="right", padx=(8, 0))

        btn_guardar = ttk.Button(btn_frame, text="Guardar", style="Primary.TButton", command=self._guardar)
        btn_guardar.pack(side="right")

    def _cargar_datos(self) -> None:
        if not self.libro:
            return
        self.txt_isbn.insert(0, self.libro.isbn)
        self.txt_titulo.insert(0, self.libro.titulo)
        self.txt_autor.insert(0, self.libro.autor)
        self.cbo_categoria.set(self.libro.categoria)
        self.txt_anio.delete(0, tk.END)
        self.txt_anio.insert(0, str(self.libro.anio))
        self.txt_stock_total.delete(0, tk.END)
        self.txt_stock_total.insert(0, str(self.libro.stock_total))
        self.txt_stock_disponible.delete(0, tk.END)
        self.txt_stock_disponible.insert(0, str(self.libro.stock_disponible))
        self.var_activo.set(self.libro.activo)

    def _guardar(self) -> None:
        isbn = self.txt_isbn.get()
        titulo = self.txt_titulo.get()
        autor = self.txt_autor.get()
        categoria = self.cbo_categoria.get()
        anio = self.txt_anio.get()
        stock_total = self.txt_stock_total.get()
        stock_disp = self.txt_stock_disponible.get()
        activo = self.var_activo.get()

        try:
            if self.libro:
                # Edición
                self.libro_service.actualizar_libro(
                    libro_id=self.libro.id,
                    isbn=isbn,
                    titulo=titulo,
                    autor=autor,
                    categoria=categoria,
                    anio=anio,
                    stock_total=stock_total,
                    stock_disponible=stock_disp,
                    activo=activo
                )
                messagebox.showinfo("Éxito", "Libro actualizado correctamente.", parent=self)
            else:
                # Nuevo
                self.libro_service.crear_libro(
                    isbn=isbn,
                    titulo=titulo,
                    autor=autor,
                    categoria=categoria,
                    anio=anio,
                    stock_total=stock_total,
                    stock_disponible=stock_disp,
                    activo=activo
                )
                messagebox.showinfo("Éxito", "Libro registrado exitosamente.", parent=self)

            if self.on_success:
                self.on_success()
            self.destroy()

        except (ValidationError, IntegrityConflictError, BusinessError) as e:
            messagebox.showerror("Error de Validación", str(e), parent=self)
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al procesar el libro: {e}", parent=self)
