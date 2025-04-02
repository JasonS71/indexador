from abc import ABC, abstractmethod

class ProcesadorDocumento(ABC):
    """Clase base abstracta para todos los procesadores de documentos"""
    
    @abstractmethod
    def extraer_texto(self, ruta_archivo):
        """
        Extrae el texto del documento.
        
        Args:
            ruta_archivo (str): Ruta al archivo a procesar
            
        Returns:
            str: Texto extraído del documento
        """
        pass
    
    @abstractmethod
    def obtener_metadatos(self, ruta_archivo):
        """
        Obtiene los metadatos del documento.
        
        Args:
            ruta_archivo (str): Ruta al archivo a procesar
            
        Returns:
            dict: Metadatos del documento
        """
        pass 