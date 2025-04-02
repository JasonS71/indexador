import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Tuple
import logging
import re

logger = logging.getLogger(__name__)

class Buscador:
    """
    Clase que implementa búsqueda semántica híbrida en documentos indexados
    
    Esta clase utiliza una combinación de búsqueda semántica (mediante embeddings)
    y búsqueda por coincidencia de palabras clave para encontrar los fragmentos 
    más relevantes de los documentos indexados que respondan a una consulta.
    """
    
    def __init__(self, indexador, modelo=None):
        """
        Inicializa el buscador con un indexador y opcionalmente un modelo de embeddings
        
        Args:
            indexador: Instancia del indexador que contiene los documentos y embeddings
            modelo: Modelo de SentenceTransformer para generar embeddings (opcional)
                   Si no se proporciona, usa el mismo modelo del indexador
        """
        self.indexador = indexador
        self.modelo = modelo if modelo is not None else indexador.modelo
        logger.info("Buscador inicializado con éxito")
    
    def buscar(self, consulta: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Realiza una búsqueda híbrida (semántica + palabras clave) en los documentos indexados
        
        La búsqueda combina:
        1. Similitud semántica mediante embeddings (70% del ranking)
        2. Coincidencia exacta de palabras clave (30% del ranking)
        
        Requisito: Los resultados deben contener al menos una palabra clave de la consulta
        para ser incluidos, a menos que no haya ninguna coincidencia exacta.
        
        Args:
            consulta: Consulta o pregunta del usuario
            top_k: Número máximo de resultados a devolver
            
        Returns:
            Lista de resultados ordenados por relevancia combinada
        """
        if not self.indexador.embeddings:
            logger.warning("No hay documentos indexados para buscar")
            return []
        
        terminos_especificos = self._extraer_terminos_especificos(consulta)
        palabras_clave = self._extraer_palabras_clave(consulta)
        
        if not palabras_clave:
            logger.warning("No se encontraron palabras clave en la consulta")
            palabras_clave = terminos_especificos
        
        try:
            embedding_consulta = self.modelo.encode(consulta)
        except Exception as e:
            logger.error(f"Error al generar embedding de la consulta: {e}")
            return []
        
        resultados = []
        
        for fragmento_id, embedding_fragmento in self.indexador.embeddings.items():
            similitud_semantica = self._calcular_similitud(embedding_consulta, embedding_fragmento)
            
            texto_fragmento = self.indexador.fragmentos.get(fragmento_id, "")
            metadatos = self.indexador.metadatos.get(fragmento_id, {})
            
            coincidencias_palabras = self._encontrar_coincidencias_palabras(texto_fragmento, palabras_clave)
            
            if not coincidencias_palabras:
                continue
            
            num_coincidencias = len(coincidencias_palabras)
            max_coincidencias = min(len(palabras_clave), 5)
            boost_coincidencias = min(num_coincidencias / max_coincidencias, 1.0) * 0.4
            
            similitud_combinada = (similitud_semantica * 0.7) + boost_coincidencias
            
            es_excel = metadatos.get('extension', '').lower() == '.xlsx'
            if es_excel and num_coincidencias > 0:
                similitud_combinada *= 1.1
            
            resultados.append({
                "id": fragmento_id,
                "texto": texto_fragmento,
                "similitud": float(similitud_combinada),
                "similitud_semantica": float(similitud_semantica),
                "metadatos": metadatos,
                "palabras_clave": coincidencias_palabras,
                "num_coincidencias": num_coincidencias
            })
        
        if not resultados:
            logger.info("No se encontraron resultados con palabras clave exactas, probando búsqueda flexible")
            return self._busqueda_flexible(consulta, embedding_consulta, palabras_clave, top_k)
        
        resultados_ordenados = sorted(resultados, key=lambda x: x["similitud"], reverse=True)
        
        return resultados_ordenados[:top_k]
    
    def _busqueda_flexible(self, consulta: str, embedding_consulta, palabras_clave: List[str], top_k: int) -> List[Dict[str, Any]]:
        """
        Realiza una búsqueda más flexible cuando no hay coincidencias exactas de palabras clave.
        
        Esta función se ejecuta como respaldo cuando la búsqueda principal no encuentra 
        resultados con coincidencias exactas. Prueba coincidencias parciales y, si aún no
        hay resultados, recurre a la similitud semántica pura.
        
        Args:
            consulta: Consulta original
            embedding_consulta: Embedding ya calculado de la consulta
            palabras_clave: Lista de palabras clave
            top_k: Número máximo de resultados
            
        Returns:
            Lista de resultados ordenados por relevancia
        """
        resultados = []
        
        for fragmento_id, embedding_fragmento in self.indexador.embeddings.items():
            similitud_semantica = self._calcular_similitud(embedding_consulta, embedding_fragmento)
            
            if similitud_semantica < 0.3:
                continue
                
            texto_fragmento = self.indexador.fragmentos.get(fragmento_id, "")
            metadatos = self.indexador.metadatos.get(fragmento_id, {})
            
            coincidencias_parciales = []
            for palabra in palabras_clave:
                if len(palabra) > 3 and palabra.lower() in texto_fragmento.lower():
                    coincidencias_parciales.append(palabra)
            
            resultados.append({
                "id": fragmento_id,
                "texto": texto_fragmento,
                "similitud": float(similitud_semantica),
                "similitud_semantica": float(similitud_semantica),
                "metadatos": metadatos,
                "palabras_clave": coincidencias_parciales,
                "num_coincidencias": len(coincidencias_parciales)
            })
        
        if not resultados:
            for fragmento_id, embedding_fragmento in self.indexador.embeddings.items():
                similitud_semantica = self._calcular_similitud(embedding_consulta, embedding_fragmento)
                
                if similitud_semantica < 0.2:
                    continue
                    
                texto_fragmento = self.indexador.fragmentos.get(fragmento_id, "")
                metadatos = self.indexador.metadatos.get(fragmento_id, {})
                
                resultados.append({
                    "id": fragmento_id,
                    "texto": texto_fragmento,
                    "similitud": float(similitud_semantica),
                    "similitud_semantica": float(similitud_semantica),
                    "metadatos": metadatos,
                    "palabras_clave": [],
                    "num_coincidencias": 0
                })
        
        resultados_ordenados = sorted(resultados, key=lambda x: x["similitud"], reverse=True)
        return resultados_ordenados[:top_k]
    
    def _extraer_terminos_especificos(self, texto: str) -> List[str]:
        """
        Extrae términos específicos importantes de una consulta
        
        Identifica y extrae:
        - Nombres propios (palabras que comienzan con mayúscula)
        - Términos que contienen números (códigos, fechas, etc.)
        
        Args:
            texto: Texto de la consulta del usuario
            
        Returns:
            Lista de términos específicos encontrados
        """
        terminos = []
        palabras = texto.split()
        
        for palabra in palabras:
            palabra_limpia = palabra.strip('.,;:?!()[]{}""\'')
            
            if len(palabra_limpia) < 2:
                continue
                
            if palabra_limpia[0].isupper():
                terminos.append(palabra_limpia)
            
            if any(c.isdigit() for c in palabra_limpia):
                terminos.append(palabra_limpia)
        
        return terminos

    def _extraer_palabras_clave(self, texto: str) -> List[str]:
        """
        Extrae todas las palabras clave importantes de una consulta
        
        Identifica palabras significativas excluyendo las más comunes (stop words).
        Estas palabras clave serán utilizadas para la búsqueda exacta.
        
        Args:
            texto: Texto de la consulta del usuario
            
        Returns:
            Lista de palabras clave encontradas
        """
        stop_words = {
            'a', 'al', 'algo', 'algunas', 'algunos', 'ante', 'antes', 'como', 'con', 'contra',
            'cual', 'cuando', 'de', 'del', 'desde', 'donde', 'durante', 'e', 'el', 'ella',
            'ellas', 'ellos', 'en', 'entre', 'era', 'erais', 'eran', 'eras', 'eres', 'es',
            'esa', 'esas', 'ese', 'eso', 'esos', 'esta', 'estaba', 'estabais', 'estaban',
            'estabas', 'estad', 'estada', 'estadas', 'estado', 'estados', 'estamos', 'estan',
            'estando', 'estar', 'estaremos', 'estará', 'estarán', 'estarás', 'estaré', 'estaréis',
            'estaría', 'estaríais', 'estaríamos', 'estarían', 'estarías', 'estas', 'este',
            'estemos', 'esto', 'estos', 'estoy', 'estuve', 'estuviera', 'estuvierais',
            'estuvieran', 'estuvieras', 'estuvieron', 'estuviese', 'estuvieseis', 'estuviesen',
            'estuvieses', 'estuvimos', 'estuviste', 'estuvisteis', 'estuviéramos',
            'estuviésemos', 'estuvo', 'fue', 'fuera', 'fuerais', 'fueran', 'fueras', 'fueron',
            'fuese', 'fueseis', 'fuesen', 'fueses', 'fui', 'fuimos', 'fuiste', 'fuisteis',
            'fuéramos', 'fuésemos', 'ha', 'habéis', 'había', 'habíais', 'habíamos', 'habían',
            'habías', 'habida', 'habidas', 'habido', 'habidos', 'habiendo', 'habremos',
            'habrá', 'habrán', 'habrás', 'habré', 'habréis', 'habría', 'habríais', 'habríamos',
            'habrían', 'habrías', 'han', 'has', 'hasta', 'hay', 'haya', 'hayamos', 'hayan',
            'hayas', 'hayáis', 'he', 'hemos', 'hube', 'hubiera', 'hubierais', 'hubieran',
            'hubieras', 'hubieron', 'hubiese', 'hubieseis', 'hubiesen', 'hubieses', 'hubimos',
            'hubiste', 'hubisteis', 'hubiéramos', 'hubiésemos', 'hubo', 'la', 'las', 'le',
            'les', 'lo', 'los', 'me', 'mi', 'mis', 'mucho', 'muchos', 'muy', 'más', 'mí',
            'mía', 'mías', 'mío', 'míos', 'nada', 'ni', 'no', 'nos', 'nosotras', 'nosotros',
            'nuestra', 'nuestras', 'nuestro', 'nuestros', 'o', 'os', 'otra', 'otras', 'otro',
            'otros', 'para', 'pero', 'poco', 'por', 'porque', 'que', 'quien', 'quienes', 'qué',
            'se', 'sea', 'seamos', 'sean', 'seas', 'seremos', 'será', 'serán', 'serás', 'seré',
            'seréis', 'sería', 'seríais', 'seríamos', 'serían', 'serías', 'seáis', 'si', 'sido',
            'siendo', 'sin', 'sobre', 'sois', 'somos', 'son', 'soy', 'su', 'sus', 'suya', 'suyas',
            'suyo', 'suyos', 'sí', 'también', 'tanto', 'te', 'tendremos', 'tendrá', 'tendrán',
            'tendrás', 'tendré', 'tendréis', 'tendría', 'tendríais', 'tendríamos', 'tendrían',
            'tendrías', 'tened', 'tenemos', 'tenga', 'tengamos', 'tengan', 'tengas', 'tengo',
            'tengáis', 'tenida', 'tenidas', 'tenido', 'tenidos', 'teniendo', 'tenéis', 'tenía',
            'teníais', 'teníamos', 'tenían', 'tenías', 'ti', 'tiene', 'tienen', 'tienes', 'todo',
            'todos', 'tu', 'tus', 'tuve', 'tuviera', 'tuvierais', 'tuvieran', 'tuvieras',
            'tuvieron', 'tuviese', 'tuvieseis', 'tuviesen', 'tuvieses', 'tuvimos', 'tuviste',
            'tuvisteis', 'tuviéramos', 'tuviésemos', 'tuvo', 'tuya', 'tuyas', 'tuyo', 'tuyos',
            'tú', 'un', 'una', 'uno', 'unos', 'vosotras', 'vosotros', 'vuestra', 'vuestras',
            'vuestro', 'vuestros', 'y', 'ya', 'yo', 'él', 'éramos'
        }
        
        palabras_clave = []
        palabras = texto.lower().split()
        
        for palabra in palabras:
            palabra_limpia = palabra.strip('.,;:?!()[]{}""\'')
            
            if len(palabra_limpia) > 3 and palabra_limpia not in stop_words:
                palabras_clave.append(palabra_limpia)
        
        return palabras_clave
    
    def _encontrar_coincidencias_palabras(self, texto: str, palabras_clave: List[str]) -> List[str]:
        """
        Encuentra coincidencias exactas de palabras clave en un texto
        
        Busca coincidencias exactas de palabras completas, utilizando límites
        de palabra en expresiones regulares para evitar coincidencias parciales.
        
        Args:
            texto: Texto del fragmento donde buscar
            palabras_clave: Lista de palabras clave a buscar
            
        Returns:
            Lista de palabras clave encontradas en el texto
        """
        coincidencias = []
        
        for palabra in palabras_clave:
            if self._es_coincidencia_exacta(texto, palabra):
                coincidencias.append(palabra)
        
        return coincidencias
    
    def _calcular_boost_terminos(self, texto: str, terminos: List[str]) -> float:
        """
        Calcula un factor de impulso basado en la presencia de términos específicos
        
        Las coincidencias exactas reciben mayor peso que las coincidencias parciales.
        
        Args:
            texto: Texto del fragmento donde buscar los términos
            terminos: Lista de términos específicos a buscar
            
        Returns:
            Factor de boost normalizado entre 0 y 0.5
        """
        if not terminos:
            return 0.0
        
        texto_lower = texto.lower()
        coincidencias = 0
        
        for termino in terminos:
            if termino.lower() in texto_lower:
                if self._es_coincidencia_exacta(texto, termino):
                    coincidencias += 2
                else:
                    coincidencias += 1
        
        max_boost = 0.5
        factor_boost = min(coincidencias / (len(terminos) * 2), 1.0) * max_boost
        
        return factor_boost
    
    def _es_coincidencia_exacta(self, texto: str, termino: str) -> bool:
        """
        Verifica si un término aparece como palabra completa en el texto
        
        Utiliza expresiones regulares con límites de palabra (\b) para asegurar
        que se encuentre la palabra exacta y no como parte de otra palabra.
        
        Args:
            texto: Texto donde buscar
            termino: Término específico a buscar
            
        Returns:
            True si existe al menos una coincidencia exacta
        """
        patron = r'\b' + re.escape(termino) + r'\b'
        return bool(re.search(patron, texto, re.IGNORECASE))
    
    def _calcular_similitud(self, embedding1, embedding2) -> float:
        """
        Calcula la similitud coseno entre dos vectores de embedding
        
        La similitud coseno mide el coseno del ángulo entre dos vectores,
        proporcionando un valor entre -1 y 1 (normalizado a 0-1).
        
        Args:
            embedding1: Vector de embedding de la consulta
            embedding2: Vector de embedding del fragmento
            
        Returns:
            Valor de similitud coseno entre 0 y 1
        """
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
        
        return np.dot(embedding1, embedding2) / (norm1 * norm2)
    
    def responder_pregunta(self, pregunta, num_fragmentos=5, umbral_similitud=0.2):
        """
        Responde a una pregunta utilizando los fragmentos más relevantes encontrados
        
        Busca los fragmentos más similares a la pregunta, priorizando aquellos con
        coincidencias de palabras clave, y construye una respuesta a partir de ellos.
        
        Args:
            pregunta: Pregunta o consulta del usuario
            num_fragmentos: Número máximo de fragmentos a utilizar
            umbral_similitud: Umbral mínimo de similitud (actualmente no se usa debido 
                             al filtrado por palabras clave)
            
        Returns:
            Diccionario con la respuesta generada y los fragmentos utilizados
        """
        fragmentos_relevantes = self.buscar(pregunta, top_k=num_fragmentos)
        
        if not fragmentos_relevantes:
            return {
                "respuesta": "No se encontraron documentos relevantes para responder esta pregunta.",
                "fragmentos_utilizados": []
            }
        
        contexto_fragmentos = []
        palabras_clave = self._extraer_palabras_clave(pregunta)
        
        for fragmento in fragmentos_relevantes:
            es_bd = fragmento["metadatos"].get("tipo") == "base_de_datos"
            nombre_tabla = fragmento["metadatos"].get("tabla", "")
            
            num_registro = None
            texto = fragmento["texto"]
            if es_bd:
                match = re.search(r'\[REGISTRO:(\d+)\]', texto)
                if match:
                    num_registro = match.group(1)
            
            contexto_fragmentos.append({
                "id": fragmento["id"],
                "texto": fragmento["texto"],
                "similitud": fragmento["similitud"],
                "similitud_semantica": fragmento.get("similitud_semantica", fragmento["similitud"]),
                "documento": fragmento["metadatos"].get("nombre", "Desconocido"),
                "ruta": fragmento["metadatos"].get("ruta", ""),
                "es_bd": es_bd,
                "tabla": nombre_tabla,
                "registro": num_registro,
                "palabras_clave": fragmento.get("palabras_clave", []),
                "num_coincidencias": fragmento.get("num_coincidencias", 0),
                "metadatos": {
                    "posicion": fragmento["metadatos"].get("pagina", 
                                fragmento["metadatos"].get("linea", 
                                fragmento["metadatos"].get("fragmento_num", "")))
                }
            })
        
        respuesta = ""
        for ctx in contexto_fragmentos:
            respuesta += f"Del documento '{ctx['documento']}':\n{ctx['texto']}\n\n"
        
        return {
            "respuesta": respuesta,
            "fragmentos_utilizados": contexto_fragmentos,
            "palabras_clave": palabras_clave
        } 