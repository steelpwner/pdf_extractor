# Extractor de CUFE

Script en Python para extraer el Código Único de Factura Electrónica (CUFE) de archivos PDF y almacenarlo en SQLite.

## Requisitos

- Python 3.8+
- PyPDF2

## Instalación

```bash
pip install PyPDF2
```

## Uso

```bash
python cufe_extractor.py <directorio_pdfs>
```

Ejemplo:
```bash
python cufe_extractor.py ./pdfs
```

## Información extraída

- Nombre del archivo
- Número de páginas
- CUFE (expresión regular: `(\b([0-9a-fA-F]\n*){95,100}\b)`)
- Peso del archivo

## Base de datos

Se crea `cufe_database.db` con la tabla `pdf_cufe`:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER | ID autoincremental |
| nombre_archivo | TEXT | Nombre del PDF |
| numero_paginas | INTEGER | Páginas del documento |
| cufe | TEXT | Código extraído |
| peso_archivo | TEXT | Tamaño del archivo |
| fecha_extraccion | TIMESTAMP | Fecha de procesamiento |

## Estructura

```
pdf_extractor/
├── cufe_extractor.py   # Script principal
├── cufe_database.db    # Base de datos (se genera)
└── README.md
```
