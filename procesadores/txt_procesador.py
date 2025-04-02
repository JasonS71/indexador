import os
from .base_procesador import ProcesadorDocumento

class ProcesadorTXT(ProcesadorDocumento):
    """Procesador para archivos de texto plano (.txt)"""
    
    def extraer_texto(self, ruta_archivo):
        """
        Extrae el texto de un archivo .txt
        
        Args:
            ruta_archivo (str): Ruta al archivo a procesar
            
        Returns:
            str: Texto extraído del documento con marcadores de línea
        """
        try:
            texto_con_lineas = ""
            with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
                lineas = archivo.readlines()
                for num_linea, linea in enumerate(lineas, 1):
                    texto_con_lineas += f"[LINEA:{num_linea}]{linea}"
                return texto_con_lineas
        except UnicodeDecodeError:
            # Intentar con otra codificación si utf-8 falla
            texto_con_lineas = ""
            with open(ruta_archivo, 'r', encoding='latin-1') as archivo:
                lineas = archivo.readlines()
                for num_linea, linea in enumerate(lineas, 1):
                    texto_con_lineas += f"[LINEA:{num_linea}]{linea}"
                return texto_con_lineas
    
    def obtener_metadatos(self, ruta_archivo):
        """
        Obtiene los metadatos básicos del archivo .txt
        
        Args:
            ruta_archivo (str): Ruta al archivo a procesar
            
        Returns:
            dict: Metadatos del documento
        """
        stats = os.stat(ruta_archivo)
        return {
            'nombre': os.path.basename(ruta_archivo),
            'extension': '.txt',
            'tamaño': stats.st_size,
            'fecha_modificacion': stats.st_mtime,
            'ruta': ruta_archivo
        } 