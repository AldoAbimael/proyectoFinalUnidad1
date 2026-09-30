import os
import sqlite3
import hashlib
from datetime import datetime, timedelta

# Ruta por defecto para la base de datos SQLite en la raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "biblioteca.db")


def hash_password(password: str) -> str:
    """Genera el hash SHA-256 de una contraseña."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Retorna una conexión a SQLite con soporte de Foreign Keys activo
    y row_factory configurado para acceso por nombre de columna.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    """Crea las tablas del esquema si no existen (RF-1)."""
    cursor = conn.cursor()

    # 1. Tabla usuarios_sistema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios_sistema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rol TEXT NOT NULL CHECK(rol IN ('administrador', 'operador')),
            activo INTEGER NOT NULL DEFAULT 1 CHECK(activo IN (0, 1)),
            avatar_path TEXT,
            tema TEXT NOT NULL DEFAULT 'estandar',
            fuente_familia TEXT NOT NULL DEFAULT 'Segoe UI',
            fuente_tamano INTEGER NOT NULL DEFAULT 10
        );
    """)

    # 2. Tabla libros (Entidad A)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS libros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn TEXT UNIQUE NOT NULL,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            categoria TEXT NOT NULL,
            anio INTEGER NOT NULL,
            stock_total INTEGER NOT NULL CHECK(stock_total >= 0),
            stock_disponible INTEGER NOT NULL CHECK(stock_disponible >= 0),
            activo INTEGER NOT NULL DEFAULT 1 CHECK(activo IN (0, 1))
        );
    """)

    # 3. Tabla lectores (Entidad B)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lectores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folio TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            correo TEXT UNIQUE NOT NULL,
            telefono TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('alumno', 'docente', 'externo')),
            activo INTEGER NOT NULL DEFAULT 1 CHECK(activo IN (0, 1))
        );
    """)

    # 4. Tabla prestamos (Movimiento de negocio que cruza Entidad A y Entidad B)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prestamos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lector_id INTEGER NOT NULL,
            libro_id INTEGER NOT NULL,
            fecha_prestamo TEXT NOT NULL,
            fecha_vencimiento TEXT NOT NULL,
            fecha_devolucion TEXT,
            estado TEXT NOT NULL CHECK(estado IN ('activo', 'devuelto')),
            FOREIGN KEY (lector_id) REFERENCES lectores(id) ON DELETE RESTRICT,
            FOREIGN KEY (libro_id) REFERENCES libros(id) ON DELETE RESTRICT
        );
    """)

    conn.commit()


def seed_data(conn: sqlite3.Connection) -> None:
    """
    Inserta datos de prueba requeridos por la rúbrica (A.5):
    - admin/admin123 y operador/operador123 con hash SHA-256.
    - Al menos 8 libros.
    - Al menos 5 lectores (incluyendo 1 inactivo).
    - Al menos 3 movimientos: 1 vigente, 1 atrasado (problemático) y 1 cerrado.
    """
    cursor = conn.cursor()

    # Verificar si ya existen usuarios para no duplicar semillas
    cursor.execute("SELECT COUNT(*) FROM usuarios_sistema")
    if cursor.fetchone()[0] > 0:
        return  # Ya existen datos semilla

    # 1. Semilla de usuarios
    usuarios = [
        ("admin", hash_password("admin123"), "administrador", 1),
        ("operador", hash_password("operador123"), "operador", 1),
        ("inactivo_demo", hash_password("pass123"), "operador", 0)
    ]
    cursor.executemany(
        "INSERT INTO usuarios_sistema (username, password_hash, rol, activo) VALUES (?, ?, ?, ?)",
        usuarios
    )

    # 2. Semilla de libros (al menos 8 registros)
    libros = [
        ("978-0132350884", "Clean Code", "Robert C. Martin", "Software", 2008, 5, 4, 1),
        ("978-0201616224", "The Pragmatic Programmer", "Andrew Hunt & David Thomas", "Software", 1999, 4, 3, 1),
        ("978-0134685991", "Effective Java", "Joshua Bloch", "Programación", 2017, 3, 3, 1),
        ("978-0596007126", "Head First Design Patterns", "Eric Freeman", "Arquitectura", 2004, 4, 4, 1),
        ("978-1449355739", "Learning Python", "Mark Lutz", "Programación", 2013, 6, 6, 1),
        ("978-0262033848", "Introduction to Algorithms", "Thomas H. Cormen", "Algoritmos", 2009, 2, 2, 1),
        ("978-0131103627", "The C Programming Language", "Brian Kernighan & Dennis Ritchie", "Programación", 1988, 3, 3, 1),
        ("978-1491950357", "Designing Data-Intensive Applications", "Martin Kleppmann", "Bases de Datos", 2017, 4, 4, 1),
        ("978-0321125217", "Domain-Driven Design", "Eric Evans", "Arquitectura", 2003, 1, 0, 1),  # Stock disponible 0
        ("978-1593279509", "Automate the Boring Stuff with Python", "Al Sweigart", "Programación", 2019, 3, 3, 0)  # Inactivo
    ]
    cursor.executemany(
        """INSERT INTO libros 
           (isbn, titulo, autor, categoria, anio, stock_total, stock_disponible, activo) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        libros
    )

    # 3. Semilla de lectores (al menos 5 registros, incluyendo 1 inactivo)
    lectores = [
        ("L-1001", "Carlos Mendoza", "carlos.mendoza@universidad.edu", "555-123-4567", "alumno", 1),
        ("L-1002", "Dra. Elena Ramos", "elena.ramos@universidad.edu", "555-234-5678", "docente", 1),
        ("L-1003", "Ing. Roberto Solís", "roberto.solis@empresa.com", "555-345-6789", "externo", 1),
        ("L-1004", "Sofía Hernández", "sofia.h@universidad.edu", "555-456-7890", "alumno", 1),
        ("L-1005", "Marcos Villeda (Inactivo)", "marcos.villeda@universidad.edu", "555-567-8901", "alumno", 0),  # Lector inactivo
        ("L-1006", "Patricia Morales", "patricia.m@universidad.edu", "555-678-9012", "docente", 1)
    ]
    cursor.executemany(
        """INSERT INTO lectores 
           (folio, nombre, correo, telefono, tipo, activo) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        lectores
    )

    # Obtenemos IDs de los libros y lectores insertados para referenciar en prestamos
    cursor.execute("SELECT id FROM lectores WHERE folio = 'L-1001'")
    lector_1 = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM lectores WHERE folio = 'L-1002'")
    lector_2 = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM lectores WHERE folio = 'L-1004'")
    lector_4 = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM libros WHERE isbn = '978-0132350884'")  # Clean Code
    libro_1 = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM libros WHERE isbn = '978-0201616224'")  # The Pragmatic Programmer
    libro_2 = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM libros WHERE isbn = '978-0134685991'")  # Effective Java
    libro_3 = cursor.fetchone()[0]

    today = datetime.now().date()
    
    # Préstamo 1: Vigente (prestado hace 2 días, vence en 5 días)
    p1_prestamo = (today - timedelta(days=2)).isoformat()
    p1_vencimiento = (today + timedelta(days=5)).isoformat()
    
    # Préstamo 2: Problemático / Atrasado (prestado hace 15 días, venció hace 8 días, no devuelto)
    p2_prestamo = (today - timedelta(days=15)).isoformat()
    p2_vencimiento = (today - timedelta(days=8)).isoformat()
    
    # Préstamo 3: Cerrado / Ya devuelto (prestado hace 20 días, devuelto hace 16 días)
    p3_prestamo = (today - timedelta(days=20)).isoformat()
    p3_vencimiento = (today - timedelta(days=13)).isoformat()
    p3_devolucion = (today - timedelta(days=16)).isoformat()

    prestamos = [
        (lector_1, libro_1, p1_prestamo, p1_vencimiento, None, "activo"),
        (lector_2, libro_2, p2_prestamo, p2_vencimiento, None, "activo"),
        (lector_4, libro_3, p3_prestamo, p3_vencimiento, p3_devolucion, "devuelto")
    ]

    cursor.executemany(
        """INSERT INTO prestamos 
           (lector_id, libro_id, fecha_prestamo, fecha_vencimiento, fecha_devolucion, estado) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        prestamos
    )

    conn.commit()


def migrate_db(conn: sqlite3.Connection) -> None:
    """Migra el esquema agregando columnas faltantes si la base de datos ya existía."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(usuarios_sistema);")
    columnas = [col["name"] for col in cursor.fetchall()]

    if "avatar_path" not in columnas:
        cursor.execute("ALTER TABLE usuarios_sistema ADD COLUMN avatar_path TEXT;")
    if "tema" not in columnas:
        cursor.execute("ALTER TABLE usuarios_sistema ADD COLUMN tema TEXT NOT NULL DEFAULT 'estandar';")
    if "fuente_familia" not in columnas:
        cursor.execute("ALTER TABLE usuarios_sistema ADD COLUMN fuente_familia TEXT NOT NULL DEFAULT 'Segoe UI';")
    if "fuente_tamano" not in columnas:
        cursor.execute("ALTER TABLE usuarios_sistema ADD COLUMN fuente_tamano INTEGER NOT NULL DEFAULT 10;")
    conn.commit()


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Inicializa la base de datos creando las tablas, migrando columnas y cargando semillas."""
    conn = get_connection(db_path)
    try:
        create_tables(conn)
        migrate_db(conn)
        seed_data(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print("Base de datos inicializada correctamente en:", DEFAULT_DB_PATH)
