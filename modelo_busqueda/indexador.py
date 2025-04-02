import os
import json
import pickle
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any, Tuple
import logging
import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Indexador:
    """Clase encargada de indexar documentos y crear embeddings para búsqueda"""
    
    def __init__(self, ruta_modelo="paraphrase-multilingual-MiniLM-L12-v2", 
                 directorio_datos="indexados_datos", tamano_fragmento=300, solapamiento=50):
        """
        Inicializa el indexador
        
        Args:
            ruta_modelo (str): Nombre o ruta del modelo de SentenceTransformer a utilizar
            directorio_datos (str): Directorio donde guardar los datos indexados
            tamano_fragmento (int): Tamaño aproximado de cada fragmento de texto en caracteres
            solapamiento (int): Cantidad de solapamiento entre fragmentos sucesivos
        """
        self.tamano_fragmento = tamano_fragmento
        self.solapamiento = solapamiento
        self.directorio_datos = directorio_datos
        
        # Crear directorio de datos si no existe
        if not os.path.exists(directorio_datos):
            os.makedirs(directorio_datos)
            
        # Cargar el modelo de embeddings
        try:
            logger.info(f"Cargando modelo de embeddings {ruta_modelo}...")
            self.modelo = SentenceTransformer(ruta_modelo)
            logger.info("Modelo cargado correctamente")
        except Exception as e:
            logger.error(f"Error al cargar el modelo: {e}")
            raise
            
        # Diccionarios para almacenar datos
        self.embeddings = {}  # Mapa de ID de fragmento a su embedding
        self.fragmentos = {}  # Mapa de ID de fragmento a su texto
        self.metadatos = {}   # Mapa de ID de fragmento a sus metadatos

        # Cargar datos existentes
        self._cargar_datos()
    
    def _cargar_datos(self):
        """Carga datos indexados previamente si existen"""
        ruta_embeddings = os.path.join(self.directorio_datos, "embeddings.pkl")
        ruta_fragmentos = os.path.join(self.directorio_datos, "fragmentos.json")
        ruta_metadatos = os.path.join(self.directorio_datos, "metadatos.json")
        
        try:
            if os.path.exists(ruta_embeddings):
                with open(ruta_embeddings, 'rb') as f:
                    self.embeddings = pickle.load(f)
                logger.info(f"Embeddings cargados: {len(self.embeddings)} fragmentos")
                
            if os.path.exists(ruta_fragmentos):
                with open(ruta_fragmentos, 'r', encoding='utf-8') as f:
                    self.fragmentos = json.load(f)
                    
            if os.path.exists(ruta_metadatos):
                with open(ruta_metadatos, 'r', encoding='utf-8') as f:
                    self.metadatos = json.load(f)
        except Exception as e:
            logger.error(f"Error al cargar datos indexados: {e}")
            # Reiniciar para evitar problemas
            self.embeddings = {}
            self.fragmentos = {}
            self.metadatos = {}
    
    def _guardar_datos(self):
        """
        Guarda los datos indexados en disco
        """
        ruta_embeddings = os.path.join(self.directorio_datos, "embeddings.pkl")
        ruta_fragmentos = os.path.join(self.directorio_datos, "fragmentos.json")
        ruta_metadatos = os.path.join(self.directorio_datos, "metadatos.json")
        
        try:
            # Crear directorio si no existe
            os.makedirs(self.directorio_datos, exist_ok=True)
            
            # Guardar embeddings (usando pickle por ser arrays numpy)
            with open(ruta_embeddings, 'wb') as f:
                pickle.dump(self.embeddings, f)
            
            # Para fragmentos, simplemente asegurar que sean strings
            fragmentos_serializables = {}
            for fragmento_id, texto in self.fragmentos.items():
                fragmentos_serializables[fragmento_id] = str(texto)
            
            with open(ruta_fragmentos, 'w', encoding='utf-8') as f:
                json.dump(fragmentos_serializables, f, ensure_ascii=False, indent=2)
            
            # Para metadatos, asegurar que todos los valores sean serializables
            metadatos_serializables = {}
            for doc_id, metadatos in self.metadatos.items():
                # Crear una copia de los metadatos para no modificar el original
                metadatos_doc = {}
                
                # Asegurar que todos los valores sean serializables
                for key, value in metadatos.items():
                    if isinstance(value, (datetime.datetime, datetime.date)):
                        metadatos_doc[key] = str(value)
                    elif not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        try:
                            # Intentar serializar a JSON como prueba
                            json.dumps(value)
                            metadatos_doc[key] = value
                        except (TypeError, OverflowError):
                            metadatos_doc[key] = str(value)
                    else:
                        metadatos_doc[key] = value
                
                metadatos_serializables[doc_id] = metadatos_doc
            
            with open(ruta_metadatos, 'w', encoding='utf-8') as f:
                json.dump(metadatos_serializables, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Datos guardados correctamente. Total fragmentos: {len(self.embeddings)}")
        except Exception as e:
            logger.error(f"Error al guardar datos indexados: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _fragmentar_texto(self, texto: str, metadatos: Dict[str, Any]) -> List[Tuple[str, Dict]]:
        """
        Divide el texto en fragmentos más pequeños para indexar, conservando información de página o línea
        
        Args:
            texto (str): Texto completo a fragmentar
            metadatos (dict): Metadatos del documento original
            
        Returns:
            List[Tuple[str, Dict]]: Lista de tuplas (fragmento, metadatos_fragment)
        """
        if not texto or len(texto.strip()) == 0:
            return []
            
        fragmentos = []
        
        # Detectar y procesar marcadores de posición (página o línea)
        lineas = texto.split('\n')
        texto_procesado = []
        posiciones = []  # Lista para almacenar la posición de cada palabra
        pagina_actual = 1
        linea_actual = 1
        
        for linea in lineas:
            # Buscar marcadores de página o línea
            if linea.startswith('[PAGINA:'):
                try:
                    pagina_actual = int(linea.split(':')[1].split(']')[0])
                    continue
                except:
                    pass  # Si hay error en el formato, ignorar
            elif linea.startswith('[LINEA:'):
                try:
                    linea_actual = int(linea.split(':')[1].split(']')[0])
                    linea = linea.split(']', 1)[1] if ']' in linea else linea
                except:
                    pass  # Si hay error en el formato, ignorar
            
            # Agregar la línea al texto procesado
            palabras_linea = linea.split()
            texto_procesado.extend(palabras_linea)
            
            # Guardar posición para cada palabra
            for _ in palabras_linea:
                if metadatos['extension'] == '.pdf':
                    posiciones.append(pagina_actual)
                else:
                    posiciones.append(linea_actual)
            
            # Incrementar línea si no es PDF
            if metadatos['extension'] != '.pdf':
                linea_actual += 1
                
        # Ahora fragmentar el texto procesado
        palabras = texto_procesado
        
        if len(palabras) == 0:
            return []
            
        # Estimar cuántas palabras equivalen al tamaño de fragmento deseado
        palabras_por_fragmento = max(1, self.tamano_fragmento // (len(texto) // max(len(palabras), 1) if len(palabras) > 0 else 1))
        palabras_solapamiento = max(1, self.solapamiento // (len(texto) // max(len(palabras), 1) if len(palabras) > 0 else 1))
        
        inicio = 0
        while inicio < len(palabras):
            fin = min(inicio + palabras_por_fragmento, len(palabras))
            fragmento = " ".join(palabras[inicio:fin])
            
            # Crear metadatos específicos para este fragmento
            metadatos_fragmento = metadatos.copy()
            metadatos_fragmento["fragmento_num"] = len(fragmentos) + 1
            metadatos_fragmento["fragmento_inicio"] = inicio
            metadatos_fragmento["fragmento_fin"] = fin
            metadatos_fragmento["fragmento_text"] = fragmento[:100] + "..." if len(fragmento) > 100 else fragmento
            
            # Agregar información de posición (página o línea)
            if posiciones and inicio < len(posiciones):
                if metadatos['extension'] == '.pdf':
                    metadatos_fragmento["pagina"] = posiciones[inicio]
                else:
                    metadatos_fragmento["linea"] = posiciones[inicio]
            
            fragmentos.append((fragmento, metadatos_fragmento))
            
            # Avanzar con solapamiento
            inicio += palabras_por_fragmento - palabras_solapamiento
            if inicio >= fin:  # Por si acaso, para evitar ciclos infinitos
                inicio = fin
        
        return fragmentos
    
    def indexar_documento(self, texto: str, metadatos: Dict[str, Any]) -> List[str]:
        """
        Indexa un documento completo dividiéndolo en fragmentos
        
        Args:
            texto (str): Contenido del documento a indexar
            metadatos (dict): Metadatos del documento
            
        Returns:
            List[str]: Lista de IDs de fragmentos creados
        """
        fragmentos_metadatos = self._fragmentar_texto(texto, metadatos)
        ids_fragmentos = []
        
        for i, (fragmento, meta) in enumerate(fragmentos_metadatos):
            # Crear ID único para el fragmento
            fragmento_id = f"{metadatos['nombre']}_{i}"
            
            # Guardar fragmento y sus metadatos
            self.fragmentos[fragmento_id] = fragmento
            self.metadatos[fragmento_id] = meta
            
            # Generar embedding del fragmento
            embedding = self.modelo.encode(fragmento)
            
            # Almacenar embedding
            self.embeddings[fragmento_id] = embedding
            
            ids_fragmentos.append(fragmento_id)
            
        logger.info(f"Documento indexado: {metadatos['nombre']}, {len(ids_fragmentos)} fragmentos")
        
        # Guardar después de indexar
        self._guardar_datos()
        
        return ids_fragmentos
    
    def eliminar_documento(self, nombre_documento: str) -> bool:
        """
        Elimina un documento y sus fragmentos del índice
        
        Args:
            nombre_documento (str): Nombre del documento a eliminar
            
        Returns:
            bool: True si se eliminó correctamente, False en caso contrario
        """
        fragmentos_a_eliminar = []
        
        # Encontrar fragmentos que pertenecen al documento
        for fragmento_id in self.fragmentos.keys():
            if fragmento_id.startswith(nombre_documento + "_"):
                fragmentos_a_eliminar.append(fragmento_id)
        
        # Eliminar fragmentos
        for fragmento_id in fragmentos_a_eliminar:
            self.fragmentos.pop(fragmento_id, None)
            self.metadatos.pop(fragmento_id, None)
            self.embeddings.pop(fragmento_id, None)
        
        logger.info(f"Documento eliminado: {nombre_documento}, {len(fragmentos_a_eliminar)} fragmentos")
        
        # Guardar cambios
        self._guardar_datos()
        
        return len(fragmentos_a_eliminar) > 0
    
    def limpiar_indice(self):
        """Elimina todos los datos indexados y limpia las estructuras de datos"""
        # Limpiar las estructuras de datos en memoria
        self.embeddings = {}
        self.fragmentos = {}
        self.metadatos = {}
        
        # Eliminar archivos de datos si existen
        ruta_embeddings = os.path.join(self.directorio_datos, "embeddings.pkl")
        ruta_fragmentos = os.path.join(self.directorio_datos, "fragmentos.json")
        ruta_metadatos = os.path.join(self.directorio_datos, "metadatos.json")
        
        archivos = [ruta_embeddings, ruta_fragmentos, ruta_metadatos]
        
        for archivo in archivos:
            if os.path.exists(archivo):
                try:
                    os.remove(archivo)
                    logger.info(f"Archivo eliminado: {archivo}")
                except Exception as e:
                    logger.error(f"Error al eliminar archivo {archivo}: {e}")
        
        logger.info("Índice limpiado correctamente")
        
        # Guardar el estado vacío
        self._guardar_datos() 