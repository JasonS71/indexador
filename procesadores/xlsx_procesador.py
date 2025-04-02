import os
import pandas as pd
from .base_procesador import ProcesadorDocumento

class ProcesadorXLSX(ProcesadorDocumento):
    """
    Procesador para archivos Excel (.xlsx)
    
    Esta clase se encarga de extraer el texto y metadatos de archivos Excel,
    preservando la estructura tabular y organizando los datos para facilitar
    la búsqueda tanto por columna como por contenido.
    """
    
    def extraer_texto(self, ruta_archivo):
        """
        Extrae el texto de un archivo Excel preservando la estructura tabular
        
        El formato generado incluye:
        - Marcadores de línea para facilitar la referencia ([LINEA:X])
        - Nombres de hoja como encabezados de sección
        - Datos representados en formato tabular con columnas separadas
        - Versión adicional en formato clave-valor para mejorar la búsqueda
        
        Args:
            ruta_archivo (str): Ruta completa al archivo Excel a procesar
            
        Returns:
            str: Texto extraído con estructura tabular preservada y marcadores de línea
        """
        try:
            excel = pd.ExcelFile(ruta_archivo)
            hojas = excel.sheet_names
            
            texto_completo = []
            num_fila = 1
            
            for hoja in hojas:
                df = pd.read_excel(ruta_archivo, sheet_name=hoja)
                df.columns = [str(col).strip() for col in df.columns]
                
                texto_completo.append(f"[LINEA:{num_fila}]## HOJA: {hoja} ##")
                num_fila += 1
                
                encabezados = " | ".join([f"{col}" for col in df.columns])
                texto_completo.append(f"[LINEA:{num_fila}]{encabezados}")
                num_fila += 1
                
                separador = "-" * len(encabezados)
                texto_completo.append(f"[LINEA:{num_fila}]{separador}")
                num_fila += 1
                
                for idx, fila in df.iterrows():
                    valores_limpios = [str(v).strip() if pd.notna(v) else "" for v in fila.values]
                    texto_fila_tabla = " | ".join(valores_limpios)
                    texto_completo.append(f"[LINEA:{num_fila}]{texto_fila_tabla}")
                    num_fila += 1
                    
                    pares = []
                    for col, valor in zip(df.columns, fila.values):
                        if pd.notna(valor) and str(valor).strip():
                            pares.append(f"{col}: {str(valor).strip()}")
                    
                    if pares:
                        texto_pares = "; ".join(pares)
                        texto_completo.append(f"[LINEA:{num_fila}]{texto_pares}")
                        num_fila += 1
                
                texto_completo.append(f"[LINEA:{num_fila}]\n")
                num_fila += 1
            
            return "\n".join(texto_completo)
        except Exception as e:
            print(f"Error al procesar el Excel {ruta_archivo}: {e}")
            return ""
    
    def obtener_metadatos(self, ruta_archivo):
        """
        Obtiene los metadatos del archivo Excel
        
        Extrae información general del archivo e información específica
        de cada hoja como número de filas, columnas y nombres de columnas.
        
        Args:
            ruta_archivo (str): Ruta completa al archivo Excel
            
        Returns:
            dict: Diccionario con metadatos del archivo, incluyendo:
                - nombre: Nombre del archivo
                - extension: .xlsx
                - tamaño: Tamaño en bytes
                - fecha_modificacion: Timestamp de última modificación
                - hojas: Lista de nombres de hojas
                - num_hojas: Cantidad de hojas
                - info_hojas: Diccionario con información detallada de cada hoja
        """
        metadatos = {
            'nombre': os.path.basename(ruta_archivo),
            'extension': '.xlsx',
            'tamaño': os.stat(ruta_archivo).st_size,
            'fecha_modificacion': os.stat(ruta_archivo).st_mtime,
            'ruta': ruta_archivo
        }
        
        try:
            excel = pd.ExcelFile(ruta_archivo)
            hojas = excel.sheet_names
            
            metadatos['hojas'] = hojas
            metadatos['num_hojas'] = len(hojas)
            
            info_hojas = {}
            for hoja in hojas:
                df = pd.read_excel(ruta_archivo, sheet_name=hoja)
                info_hojas[hoja] = {
                    'filas': len(df),
                    'columnas': len(df.columns),
                    'nombres_columnas': list(df.columns)
                }
            
            metadatos['info_hojas'] = info_hojas
                
        except Exception as e:
            print(f"Error al obtener metadatos del Excel {ruta_archivo}: {e}")
            
        return metadatos 