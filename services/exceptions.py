class BusinessError(Exception):
    """Excepción base para violaciones de reglas de negocio del dominio."""
    pass


class ValidationError(BusinessError):
    """Excepción lanzada cuando los datos de entrada no cumplen con las validaciones de tipo o formato."""
    pass


class AuthenticationError(BusinessError):
    """Excepción lanzada por fallos de credenciales o usuario inactivo en el login."""
    pass


class IntegrityConflictError(BusinessError):
    """Excepción lanzada al violar restricciones de unicidad o integridad referencial."""
    pass
