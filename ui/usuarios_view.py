import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
from models.usuario import Usuario
from services.usuario_service import UsuarioService
from services.exceptions import BusinessError, ValidationError, IntegrityConflictError
from ui.theme import ModernTheme


class UsuariosView(ttk.Frame):
    """
    Vista de Gestión de Cuentas de Personal (Usuarios del Sistema).
    RF-2: Exclusivo para el rol 'administrador'. El operador no gestiona cuentas del personal.
    """

    def __init__(
        self,
        parent: tk.Widget,
        usuario_service: UsuarioService,
        usuario_actual: Usuario
    ):
        super().__init__(parent, padding=15)
        self.usuario_service = usuario_service
        self.usuario_actual = usuario_actual
        self.usuarios: List[Usuario] = []

        self._crear_interfaz()
        self.cargar_datos()

    def _crear_interfaz(self) -> None:
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", pady=(0, 10))

        lbl_titulo = ttk.Label(
            header_frame,
            text="Administración de Usuarios del Sistema (Cuentas de Personal)",
            font=ModernTheme.FONT_TITLE,
            foreground=ModernTheme.COLOR_PRIMARY
        )
        lbl_titulo.pack(side="left")

        # Formulario para registrar nuevo usuario
        form_frame = ttk.LabelFrame(self, text="Registrar Nuevo Usuario", padding=10)
        form_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(form_frame, text="Username: *", font=ModernTheme.FONT_BOLD).grid(row=0, column=0, padx=5, pady=4, sticky="w")
        self.txt_username = ttk.Entry(form_frame, width=18)
        self.txt_username.grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(form_frame, text="Contraseña: *", font=ModernTheme.FONT_BOLD).grid(row=0, column=2, padx=5, pady=4, sticky="w")
        self.txt_password = ttk.Entry(form_frame, width=18, show="•")
        self.txt_password.grid(row=0, column=3, padx=5, pady=4)

        ttk.Label(form_frame, text="Rol: *", font=ModernTheme.FONT_BOLD).grid(row=0, column=4, padx=5, pady=4, sticky="w")
        self.cbo_rol = ttk.Combobox(
            form_frame,
            values=["operador", "administrador"],
            state="readonly",
            width=15
        )
        self.cbo_rol.set("operador")
        self.cbo_rol.grid(row=0, column=5, padx=5, pady=4)

        btn_crear = ttk.Button(
            form_frame,
            text="+ Crear Usuario",
            style="Primary.TButton",
            command=self._crear_usuario
        )
        btn_crear.grid(row=0, column=6, padx=(15, 5), pady=4)

        # Treeview de usuarios
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        columnas = ("id", "username", "rol", "activo")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columnas,
            show="headings",
            selectmode="browse"
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("username", text="Nombre de Usuario")
        self.tree.heading("rol", text="Rol Asignado")
        self.tree.heading("activo", text="Estado de Cuenta")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("username", width=200, anchor="w")
        self.tree.column("rol", width=150, anchor="center")
        self.tree.column("activo", width=120, anchor="center")

        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar_y.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree.tag_configure("inactivo", background="#fee2e2", foreground="#991b1b")

        # Botones inferiores
        bottom_bar = ttk.Frame(self)
        bottom_bar.pack(fill="x", pady=(10, 0))

        btn_toggle = ttk.Button(
            bottom_bar,
            text="Alternar Activo / Desactivado",
            style="Secondary.TButton",
            command=self._alternar_estado
        )
        btn_toggle.pack(side="left")

    def cargar_datos(self) -> None:
        try:
            self.usuarios = self.usuario_service.listar_usuarios(self.usuario_actual)
            self.tree.delete(*self.tree.get_children())
            for u in self.usuarios:
                estado_txt = "Activo" if u.activo else "Desactivado"
                tags = () if u.activo else ("inactivo",)
                self.tree.insert(
                    "",
                    "end",
                    iid=str(u.id),
                    values=(u.id, u.username, u.rol.capitalize(), estado_txt),
                    tags=tags
                )
        except BusinessError as e:
            messagebox.showerror("Acceso Denegado", str(e), parent=self)

    def _crear_usuario(self) -> None:
        username = self.txt_username.get()
        password = self.txt_password.get()
        rol = self.cbo_rol.get()

        try:
            nuevo = self.usuario_service.registrar_usuario(
                usuario_solicitante=self.usuario_actual,
                username=username,
                password=password,
                rol=rol,
                activo=1
            )
            messagebox.showinfo("Usuario Creado", f"El usuario '{nuevo.username}' fue creado con rol '{nuevo.rol}'.", parent=self)
            self.txt_username.delete(0, tk.END)
            self.txt_password.delete(0, tk.END)
            self.cargar_datos()
        except (ValidationError, IntegrityConflictError, BusinessError) as e:
            messagebox.showerror("Error al Crear Usuario", str(e), parent=self)

    def _alternar_estado(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Seleccionar", "Seleccione un usuario de la lista.", parent=self)
            return

        user_id = int(selected[0])
        usuario = next((u for u in self.usuarios if u.id == user_id), None)
        if not usuario:
            return

        nuevo_estado = 0 if usuario.activo else 1
        accion = "desactivar" if nuevo_estado == 0 else "activar"

        if not messagebox.askyesno("Confirmación (RF-9)", f"¿Desea {accion} la cuenta de '{usuario.username}'?", parent=self):
            return

        try:
            self.usuario_service.cambiar_estado(self.usuario_actual, user_id, nuevo_estado)
            self.cargar_datos()
        except BusinessError as e:
            messagebox.showerror("Restricción", str(e), parent=self)
