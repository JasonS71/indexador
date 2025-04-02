from .txt_procesador import ProcesadorTXT
from .pdf_procesador import ProcesadorPDF
from .docx_procesador import ProcesadorDOCX
from .xlsx_procesador import ProcesadorXLSX
from .postgresql_procesador import ProcesadorPostgreSQL

# Diccionario que mapea extensiones de archivo a sus procesadores
PROCESADORES = {
    '.txt': ProcesadorTXT(),
    '.pdf': ProcesadorPDF(),
    '.docx': ProcesadorDOCX(),
    '.xlsx': ProcesadorXLSX(),
    '.sql': ProcesadorPostgreSQL(),  # Para procesamiento de BD
}

# Variable global para el procesador PostgreSQL (permitirá configurar la conexión una vez)
procesador_postgresql = ProcesadorPostgreSQL()

def obtener_procesador(extension):
    """
    Obtiene el procesador adecuado para una extensión de archivo
    
    Args:
        extension (str): Extensión de archivo (con el punto, ej: '.pdf')
        
    Returns:
        ProcesadorDocumento o None: El procesador correspondiente o None si no hay procesador
    """
    return PROCESADORES.get(extension.lower())

def obtener_procesador_postgresql():
    """
    Obtiene el procesador para PostgreSQL (singleton)
    
    Returns:
        ProcesadorPostgreSQL: Instancia única del procesador PostgreSQL
    """
    return procesador_postgresql 