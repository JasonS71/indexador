import os
import PyPDF2
from .base_procesador import ProcesadorDocumento

class ProcesadorPDF(ProcesadorDocumento):
    """Procesador para archivos PDF (.pdf)"""
    
    def extraer_texto(self, ruta_archivo):
        """
        Extrae el texto de un archivo PDF
        
        Args:
            ruta_archivo (str): Ruta al archivo a procesar
            
        Returns:
            str: Texto extraído del documento con marcadores de página
        """
        texto_completo = ""
        
        try:
            with open(ruta_archivo, 'rb') as archivo:
                lector_pdf = PyPDF2.PdfReader(archivo)
                num_paginas = len(lector_pdf.pages)
                
                for num_pagina in range(num_paginas):
                    pagina = lector_pdf.pages[num_pagina]
                    texto_pagina = pagina.extract_text()
                    
                    # Insertar marcador de página en el texto
                    texto_completo += f"[PAGINA:{num_pagina+1}]\n{texto_pagina}\n\n"
                    
                return texto_completo
        except Exception as e:
            print(f"Error al procesar el PDF {ruta_archivo}: {e}")
            return ""
    
    def obtener_metadatos(self, ruta_archivo):
        """
        Obtiene los metadatos del archivo PDF
        
        Args:
            ruta_archivo (str): Ruta al archivo a procesar
            
        Returns:
            dict: Metadatos del documento
        """
        metadatos = {
            'nombre': os.path.basename(ruta_archivo),
            'extension': '.pdf',
            'tamaño': os.stat(ruta_archivo).st_size,
            'fecha_modificacion': os.stat(ruta_archivo).st_mtime,
            'ruta': ruta_archivo
        }
        
        try:
            with open(ruta_archivo, 'rb') as archivo:
                lector_pdf = PyPDF2.PdfReader(archivo)
                metadatos['paginas'] = len(lector_pdf.pages)
                
                info = lector_pdf.metadata
                if info:
                    # Añadir metadatos del PDF si están disponibles
                    for key, value in info.items():
                        if key.startswith('/'):
                            key = key[1:]  # Quitar la / inicial
                        metadatos[key] = value
                
        except Exception as e:
            print(f"Error al obtener metadatos del PDF {ruta_archivo}: {e}")
            
        return metadatos 