import sqlite3
from typing import List, Optional
from models.usuario import Usuario
from repositories.usuario_repository import UsuarioRepository
from services.auth_service import AuthService
from services.exceptions import BusinessError, ValidationError, IntegrityConflictError


class UsuarioService:
    """
    Servicio para la administración de cuentas del personal (usuarios del sistema).
    Restricción RF-2: El operador no puede gestionar cuentas del personal.
    """

    def __init__(self, usuario_repo: Optional[UsuarioRepository] = None):
        self.usuario_repo = usuario_repo or UsuarioRepository()

    def listar_usuarios(self, usuario_solicitante: Usuario) -> List[Usuario]:
        if not usuario_solicitante.es_admin:
            raise BusinessError("Acceso denegado: solo el administrador puede gestionar usuarios del sistema.")
        return self.usuario_repo.listar_todos()

    def registrar_usuario(
        self,
        usuario_solicitante: Usuario,
        username: str,
        password: str,
        rol: str,
        activo: int = 1
    ) -> Usuario:
        if not usuario_solicitante.es_admin:
            raise BusinessError("Acceso denegado: solo el administrador puede crear nuevos usuarios.")

        username = (username or "").strip()
        password = (password or "").strip()
        rol = (rol or "").strip().lower()

        if not username:
            raise ValidationError("El nombre de usuario no puede estar vacío.")
        if len(username) < 3:
            raise ValidationError("El nombre de usuario debe tener al menos 3 caracteres.")
        if not password:
            raise ValidationError("La contraseña no puede estar vacía.")
        if len(password) < 6:
            raise ValidationError("La contraseña debe tener al menos 6 caracteres.")
        if rol not in ("administrador", "operador"):
            raise ValidationError("El rol asignado debe ser 'administrador' u 'operador'.")

        existente = self.usuario_repo.obtener_por_username(username)
        if existente:
            raise IntegrityConflictError(f"El nombre de usuario '{username}' ya está registrado.")

        pass_hash = AuthService.hash_password(password)
        nuevo_usuario = Usuario(
            id=None,
            username=username,
            password_hash=pass_hash,
            rol=rol,
            activo=1 if activo else 0
        )

        try:
            nuevo_id = self.usuario_repo.crear(nuevo_usuario)
            nuevo_usuario.id = nuevo_id
            return nuevo_usuario
        except sqlite3.IntegrityError as e:
            raise IntegrityConflictError(f"Error al registrar usuario: {e}")

    def cambiar_estado(self, usuario_solicitante: Usuario, user_id: int, nuevo_activo: int) -> None:
        if not usuario_solicitante.es_admin:
            raise BusinessError("Acceso denegado: solo el administrador puede cambiar el estado de un usuario.")

        if usuario_solicitante.id == user_id and nuevo_activo == 0:
            raise BusinessError("No puede desactivar su propia cuenta de administrador mientras está en sesión.")

        target = self.usuario_repo.obtener_por_id(user_id)
        if not target:
            raise ValidationError(f"No se encontró el usuario con ID {user_id}.")

        self.usuario_repo.cambiar_estado(user_id, 1 if nuevo_activo else 0)

    def guardar_preferencias(
        self,
        usuario: Usuario,
        tema: str,
        fuente_familia: str,
        fuente_tamano: int
    ) -> None:
        """Valida y guarda las preferencias de tema y accesibilidad del usuario."""
        temas_validos = ("estandar", "oscuro", "pastel", "corporativo", "bosque")
        tema_limpio = (tema or "estandar").strip().lower()
        if tema_limpio not in temas_validos:
            raise ValidationError(f"Tema visual no reconocido. Opciones válidas: {', '.join(temas_validos)}")

        fuente_familia_limpia = (fuente_familia or "Segoe UI").strip()
        try:
            tamano_int = int(fuente_tamano)
        except (ValueError, TypeError):
            raise ValidationError("El tamaño de fuente debe ser un número entero.")

        if tamano_int < 8 or tamano_int > 20:
            raise ValidationError("El tamaño de fuente debe estar entre 8pt y 20pt.")

        if not usuario.id:
            raise ValidationError("ID de usuario no válido.")

        self.usuario_repo.actualizar_preferencias(
            user_id=usuario.id,
            tema=tema_limpio,
            fuente_familia=fuente_familia_limpia,
            fuente_tamano=tamano_int
        )
        usuario.tema = tema_limpio
        usuario.fuente_familia = fuente_familia_limpia
        usuario.fuente_tamano = tamano_int

    def guardar_avatar(self, usuario: Usuario, ruta_origen: str) -> str:
        """
        Copia y asocia una imagen de perfil (.png, .jpg, etc.) al usuario,
        almacenándola en la carpeta local 'avatars/' y persistiendo la ruta en BD.
        """
        import os
        import shutil

        if not ruta_origen or not os.path.exists(ruta_origen):
            raise ValidationError("El archivo de imagen seleccionado no existe.")

        extension = os.path.splitext(ruta_origen)[1].lower()
        extensiones_validas = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
        if extension not in extensiones_validas:
            raise ValidationError(
                f"Formato de imagen no soportado ({extension}). Por favor use {', '.join(extensiones_validas)}."
            )

        if not usuario.id:
            raise ValidationError("ID de usuario no válido para asignar foto de perfil.")

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        avatars_dir = os.path.join(base_dir, "avatars")
        os.makedirs(avatars_dir, exist_ok=True)

        nombre_archivo = f"avatar_user_{usuario.id}{extension}"
        ruta_destino = os.path.join(avatars_dir, nombre_archivo)

        # Copiar imagen a la carpeta interna del sistema
        shutil.copy2(ruta_origen, ruta_destino)

        # Persistir en la base de datos
        self.usuario_repo.actualizar_avatar(usuario.id, ruta_destino)
        usuario.avatar_path = ruta_destino

        return ruta_destino
