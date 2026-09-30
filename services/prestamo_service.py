import csv
from datetime import date, timedelta
from typing import List, Optional
from db.database import get_connection, DEFAULT_DB_PATH
from models.prestamo import Prestamo, PrestamoDetalle
from repositories.libro_repository import LibroRepository
from repositories.lector_repository import LectorRepository
from repositories.prestamo_repository import PrestamoRepository
from services.exceptions import BusinessError, ValidationError


class PrestamoService:
    """
    Servicio para el proceso de negocio de Préstamos y Devoluciones (RF-5, RF-7, RF-8).
    Aplica las reglas de negocio estrictas de la Opción 1:
    - Vence en 7 días y descuenta 1 de stock disponible.
    - No prestar sin stock disponible ni a lector inactivo.
    - Un lector no puede tener dos préstamos activos del mismo libro.
    - La devolución suma 1 al stock disponible (sin exceder el total).
    - Reporte de atrasados y exportación CSV.
    """

    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        prestamo_repo: Optional[PrestamoRepository] = None,
        libro_repo: Optional[LibroRepository] = None,
        lector_repo: Optional[LectorRepository] = None
    ):
        self.db_path = db_path
        self.prestamo_repo = prestamo_repo or PrestamoRepository(db_path)
        self.libro_repo = libro_repo or LibroRepository(db_path)
        self.lector_repo = lector_repo or LectorRepository(db_path)

    def registrar_prestamo(
        self,
        lector_id: int,
        libro_id: int,
        dias_prestamo: int = 7
    ) -> Prestamo:
        """
        Registra un nuevo préstamo bibliotecario garantizando todas las reglas del enunciado.
        Maneja la transacción de forma atómica: descuenta stock e inserta el préstamo.
        """
        # 1. Validar lector
        lector = self.lector_repo.obtener_por_id(lector_id)
        if not lector:
            raise ValidationError(f"No se encontró el lector con ID {lector_id}.")
        if not lector.esta_activo:
            raise BusinessError(
                f"No se puede realizar el préstamo: El lector '{lector.nombre}' (Folio: {lector.folio}) "
                "se encuentra INACTIVO en el sistema."
            )

        # 2. Validar libro
        libro = self.libro_repo.obtener_por_id(libro_id)
        if not libro:
            raise ValidationError(f"No se encontró el libro con ID {libro_id}.")
        if not libro.esta_activo:
            raise BusinessError(
                f"No se puede realizar el préstamo: El libro '{libro.titulo}' está dado de baja o inactivo."
            )
        if libro.stock_disponible <= 0:
            raise BusinessError(
                f"No se puede realizar el préstamo: No hay stock disponible del libro '{libro.titulo}' "
                f"(Total: {libro.stock_total}, Disponibles: 0)."
            )

        # 3. Validar duplicidad activa del mismo libro para el mismo lector
        if self.prestamo_repo.tiene_prestamo_activo_del_libro(lector_id, libro_id):
            raise BusinessError(
                f"Regla de negocio violada: El lector '{lector.nombre}' ya tiene un préstamo ACTIVO "
                f"del libro '{libro.titulo}'. No puede solicitar otro ejemplar hasta devolver el actual."
            )

        # 4. Fechas (vence en 7 días por especificación)
        hoy = date.today()
        fecha_prestamo = hoy.isoformat()
        fecha_vencimiento = (hoy + timedelta(days=dias_prestamo)).isoformat()

        # 5. Transacción atómica en SQLite: Descontar stock + Registrar préstamo
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            # Descontar 1 ejemplar disponible
            nuevo_stock = libro.stock_disponible - 1
            cursor.execute(
                "UPDATE libros SET stock_disponible = ? WHERE id = ?",
                (nuevo_stock, libro_id)
            )

            # Insertar préstamo
            cursor.execute(
                """INSERT INTO prestamos 
                   (lector_id, libro_id, fecha_prestamo, fecha_vencimiento, fecha_devolucion, estado)
                   VALUES (?, ?, ?, ?, NULL, 'activo')""",
                (lector_id, libro_id, fecha_prestamo, fecha_vencimiento)
            )
            prestamo_id = cursor.lastrowid
            conn.commit()

        return Prestamo(
            id=prestamo_id,
            lector_id=lector_id,
            libro_id=libro_id,
            fecha_prestamo=fecha_prestamo,
            fecha_vencimiento=fecha_vencimiento,
            fecha_devolucion=None,
            estado="activo"
        )

    def registrar_devolucion(self, prestamo_id: int) -> None:
        """
        Cierre del movimiento:
        - Marca el préstamo como 'devuelto' con fecha_devolucion = hoy.
        - Suma 1 al stock disponible del libro (sin sobrepasar stock_total).
        """
        prestamo = self.prestamo_repo.obtener_por_id(prestamo_id)
        if not prestamo:
            raise ValidationError(f"No se encontró el préstamo con ID {prestamo_id}.")

        if prestamo.esta_devuelto:
            raise BusinessError(
                f"El préstamo #{prestamo_id} ya fue devuelto previamente el {prestamo.fecha_devolucion}."
            )

        libro = self.libro_repo.obtener_por_id(prestamo.libro_id)
        if not libro:
            raise ValidationError(f"Libro asociado al préstamo #{prestamo_id} no encontrado.")

        # Calcular nuevo stock disponible cuidando no exceder el total
        nuevo_stock = min(libro.stock_total, libro.stock_disponible + 1)
        fecha_hoy = date.today().isoformat()

        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE prestamos 
                   SET estado = 'devuelto', fecha_devolucion = ? 
                   WHERE id = ?""",
                (fecha_hoy, prestamo_id)
            )
            cursor.execute(
                "UPDATE libros SET stock_disponible = ? WHERE id = ?",
                (nuevo_stock, libro.id)
            )
            conn.commit()

    def listar_prestamos(
        self,
        filtro_estado: Optional[str] = None,
        busqueda: Optional[str] = None
    ) -> List[PrestamoDetalle]:
        """Retorna listado con JOIN entre préstamos, lectores y libros (RF-7)."""
        return self.prestamo_repo.listar_con_detalle(
            filtro_estado=filtro_estado,
            busqueda=busqueda
        )

    def obtener_prestamos_atrasados(self) -> List[PrestamoDetalle]:
        """RF-8: Reporte del caso problemático: préstamos activos con vencimiento < hoy."""
        return self.prestamo_repo.obtener_prestamos_atrasados()

    def exportar_reporte_csv(self, ruta_archivo: str) -> int:
        """
        Extra opcional A.6: Exportar reporte de préstamos atrasados a archivo CSV.
        Retorna la cantidad de registros exportados.
        """
        atrasados = self.obtener_prestamos_atrasados()
        with open(ruta_archivo, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            # Cabeceras
            writer.writerow([
                "ID Préstamo",
                "Folio Lector",
                "Nombre Lector",
                "Tipo Lector",
                "ISBN Libro",
                "Título Libro",
                "Fecha Préstamo",
                "Fecha Vencimiento",
                "Estado"
            ])
            for p in atrasados:
                writer.writerow([
                    p.id,
                    p.lector_folio,
                    p.lector_nombre,
                    p.lector_tipo,
                    p.libro_isbn,
                    p.libro_titulo,
                    p.fecha_prestamo,
                    p.fecha_vencimiento,
                    p.estado
                ])
        return len(atrasados)
