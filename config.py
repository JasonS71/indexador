import os

# Configuración de carpetas
UPLOAD_FOLDER = 'uploads'
DEFAULT_DOCS_FOLDER = 'documentos_por_defecto'
DATA_FOLDER = 'indexados_datos'
ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.docx', '.xlsx', '.sql'}

# Parámetros del indexador
DEFAULT_FRAGMENT_SIZE = 2500
DEFAULT_OVERLAP = 300

# Configuración de PostgreSQL
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'nombre_base_datos',
    'user': 'usuario',
    'password': 'contraseña'
}

# Lista de tablas a indexar con su configuración
PG_TABLES = [
    # Ejemplo:
    # {
    #     'tabla': 'usuarios',
    #     'campos': ['id', 'nombre', 'email', 'fecha_registro'],
    #     'condicion': 'activo = true',
    #     'limite': 500
    # },
]

# Crear directorios necesarios
def crear_directorios():
    """Crea los directorios necesarios para la aplicación"""
    for folder in [UPLOAD_FOLDER, DEFAULT_DOCS_FOLDER, DATA_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder) 