"""
Módulo de modelos y entidades de dominio del Sistema de Biblioteca.
Clases puras sin widgets ni dependencias de Tkinter (RNF-1, A.3).
"""
from .usuario import Usuario
from .libro import Libro
from .lector import Lector
from .prestamo import Prestamo, PrestamoDetalle

__all__ = ["Usuario", "Libro", "Lector", "Prestamo", "PrestamoDetalle"]
