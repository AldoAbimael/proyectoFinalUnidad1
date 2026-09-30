import hashlib
from typing import Optional
from models.usuario import Usuario
from repositories.usuario_repository import UsuarioRepository
from services.exceptions import AuthenticationError, ValidationError


class AuthService:
    """
    Servicio de autenticación y control de acceso.
    Maneja hash de contraseñas con SHA-256 (RF-2, RF-3) y validación de usuarios inactivos.
    """

    def __init__(self, usuario_repo: Optional[UsuarioRepository] = None):
        self.usuario_repo = usuario_repo or UsuarioRepository()

    @staticmethod
    def hash_password(password: str) -> str:
        """Genera hash SHA-256 de una contraseña."""
        if not password:
            return ""
        return hashlib.sha256(password.strip().encode("utf-8")).hexdigest()

    def login(self, username: str, password: str) -> Usuario:
        """
        Valida credenciales de acceso.
        Lanza AuthenticationError si las credenciales fallan o el usuario está inactivo (RF-2, A.4).
        """
        username = (username or "").strip()
        password = (password or "").strip()

        if not username or not password:
            raise ValidationError("Debe ingresar tanto el usuario como la contraseña.")

        usuario = self.usuario_repo.obtener_por_username(username)
        if not usuario:
            raise AuthenticationError("Usuario o contraseña incorrectos.")

        pass_hash = self.hash_password(password)
        if usuario.password_hash != pass_hash:
            raise AuthenticationError("Usuario o contraseña incorrectos.")

        if not usuario.esta_activo:
            raise AuthenticationError(
                f"La cuenta del usuario '{username}' está desactivada. Contacte al administrador."
            )

        return usuario
