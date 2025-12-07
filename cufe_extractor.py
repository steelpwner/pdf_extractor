"""
Script para extraer información CUFE de archivos PDF
y almacenarla en una base de datos SQLite.
"""

import os
import re
import sqlite3
from pathlib import Path

try:
    import PyPDF2
except ImportError:
    print("Error: PyPDF2 no está instalado. Ejecute: pip install PyPDF2")
    exit(1)


def create_database(db_path: str = "cufe_database.db") -> sqlite3.Connection:
    """Crea la base de datos SQLite y la tabla para almacenar la información."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pdf_cufe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_archivo TEXT NOT NULL,
            numero_paginas INTEGER NOT NULL,
            cufe TEXT,
            peso_archivo TEXT NOT NULL,
            fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    return conn


def get_file_size(file_path: str) -> str:
    """Obtiene el tamaño del archivo en formato legible."""
    size_bytes = os.path.getsize(file_path)

    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def extract_cufe(text: str) -> str | None:
    """
    Extrae el CUFE del texto usando la expresión regular especificada.
    CUFE: Código Único de Factura Electrónica (95-100 caracteres hexadecimales)
    """
    pattern = r'\b([0-9a-fA-F]\n*){95,100}\b'

    match = re.search(pattern, text)
    if match:
        cufe = match.group(0).replace('\n', '')
        return cufe

    hex_pattern = r'[0-9a-fA-F]{95,100}'
    match = re.search(hex_pattern, text)
    if match:
        return match.group(0)

    return None


def process_pdf(file_path: str) -> dict:
    """Procesa un archivo PDF y extrae la información requerida."""
    result = {
        'nombre_archivo': os.path.basename(file_path),
        'numero_paginas': 0,
        'cufe': None,
        'peso_archivo': get_file_size(file_path)
    }

    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            result['numero_paginas'] = len(pdf_reader.pages)

            full_text = ""
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

            result['cufe'] = extract_cufe(full_text)

    except Exception as e:
        print(f"Error procesando {file_path}: {str(e)}")

    return result


def save_to_database(conn: sqlite3.Connection, data: dict) -> None:
    """Guarda la información extraída en la base de datos."""
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO pdf_cufe (nombre_archivo, numero_paginas, cufe, peso_archivo)
        VALUES (?, ?, ?, ?)
    ''', (
        data['nombre_archivo'],
        data['numero_paginas'],
        data['cufe'],
        data['peso_archivo']
    ))

    conn.commit()


def process_directory(pdf_directory: str, db_path: str = "cufe_database.db") -> None:
    """Procesa todos los archivos PDF en un directorio."""
    pdf_dir = Path(pdf_directory)

    if not pdf_dir.exists():
        print(f"Error: El directorio '{pdf_directory}' no existe.")
        return

    # Usar case_sensitive=False para evitar duplicados en Windows
    pdf_files = list(pdf_dir.glob("*.[pP][dD][fF]"))

    if not pdf_files:
        print(f"No se encontraron archivos PDF en '{pdf_directory}'")
        return

    print(f"Encontrados {len(pdf_files)} archivos PDF")
    print("-" * 60)

    conn = create_database(db_path)

    for pdf_file in pdf_files:
        print(f"Procesando: {pdf_file.name}")
        data = process_pdf(str(pdf_file))
        save_to_database(conn, data)

        print(f"  - Páginas: {data['numero_paginas']}")
        print(f"  - Peso: {data['peso_archivo']}")
        if data['cufe']:
            print(f"  - CUFE: {data['cufe'][:50]}...")
        else:
            print("  - CUFE: No encontrado")
        print()

    conn.close()
    print("-" * 60)
    print(f"Proceso completado. Datos guardados en '{db_path}'")


def show_database_contents(db_path: str = "cufe_database.db") -> None:
    """Muestra el contenido de la base de datos."""
    if not os.path.exists(db_path):
        print(f"La base de datos '{db_path}' no existe.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM pdf_cufe")
    rows = cursor.fetchall()

    print("\n" + "=" * 80)
    print("CONTENIDO DE LA BASE DE DATOS")
    print("=" * 80)

    for row in rows:
        print(f"\nID: {row[0]}")
        print(f"Nombre del archivo: {row[1]}")
        print(f"Número de páginas: {row[2]}")
        print(f"CUFE: {row[3] if row[3] else 'No encontrado'}")
        print(f"Peso del archivo: {row[4]}")
        print(f"Fecha de extracción: {row[5]}")
        print("-" * 40)

    conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python cufe_extractor.py <directorio_pdfs>")
        print("Ejemplo: python cufe_extractor.py ./facturas")
        sys.exit(1)

    pdf_directory = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else "cufe_database.db"

    process_directory(pdf_directory, db_path)
    show_database_contents(db_path)
