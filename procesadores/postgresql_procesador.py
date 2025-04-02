import os
import logging
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProcesadorPostgreSQL:
    """
    Clase para procesar y extraer datos de PostgreSQL
    """
    
    def __init__(self, conexion_params=None):
        """
        Inicializa el procesador PostgreSQL
        
        Args:
            conexion_params (dict): Parámetros de conexión a la BD
        """
        self.conexion_params = conexion_params or {}
        
    def establecer_conexion(self, host, port, dbname, user, password):
        """
        Establece los parámetros de conexión a la base de datos
        
        Args:
            host (str): Host del servidor PostgreSQL
            port (int): Puerto del servidor
            dbname (str): Nombre de la base de datos
            user (str): Usuario
            password (str): Contraseña
        """
        self.conexion_params = {
            'host': host,
            'port': port,
            'dbname': dbname,
            'user': user,
            'password': password
        }
        
    def _conectar(self):
        """
        Crea una conexión a la base de datos PostgreSQL
        
        Returns:
            tuple: (conexión, cursor) o (None, None) si hay error
        """
        try:
            conexion = psycopg2.connect(**self.conexion_params)
            cursor = conexion.cursor(cursor_factory=RealDictCursor)
            return conexion, cursor
        except Exception as e:
            logger.error(f"Error al conectar a PostgreSQL: {e}")
            return None, None
    
    def extraer_texto(self, config_consulta):
        """
        Extrae texto de una tabla de PostgreSQL
        
        Args:
            config_consulta (dict): Configuración de la consulta
                {
                    'tabla': 'nombre_tabla',
                    'campos': ['campo1', 'campo2', ...],
                    'condicion': 'campo1 = valor' (opcional),
                    'limite': 1000 (opcional)
                }
            
        Returns:
            str: Texto extraído de la BD con marcadores de posición
        """
        try:
            # Validar configuración mínima
            if not isinstance(config_consulta, dict) or 'tabla' not in config_consulta:
                raise ValueError("Configuración de consulta inválida: debe incluir al menos 'tabla'")
            
            # Obtener parámetros de la consulta
            tabla = config_consulta['tabla']
            campos = config_consulta.get('campos', ['*'])
            condicion = config_consulta.get('condicion', '')
            limite = config_consulta.get('limite', 1000)
            
            # Construir consulta SQL
            campos_str = ", ".join(campos) if campos != ['*'] else '*'
            sql = f"SELECT {campos_str} FROM {tabla}"
            
            if condicion:
                sql += f" WHERE {condicion}"
                
            if limite:
                sql += f" LIMIT {limite}"
            
            # Ejecutar consulta
            conexion, cursor = self._conectar()
            if not conexion or not cursor:
                return ""
            
            cursor.execute(sql)
            resultados = cursor.fetchall()
            
            # Construir texto a partir de los resultados
            texto_completo = []
            
            # Añadir un encabezado al texto
            texto_completo.append(f"[BD:{tabla}]")
            texto_completo.append(f"Consulta ejecutada: {sql}")
            texto_completo.append("-" * 50)
            
            # Procesar cada registro
            for i, registro in enumerate(resultados, 1):
                # Añadir marcador de línea/registro
                texto_completo.append(f"[REGISTRO:{i}]")
                
                # Convertir registro a texto legible
                for campo, valor in registro.items():
                    # Formatear el valor dependiendo de su tipo
                    if isinstance(valor, (datetime)):
                        valor_formateado = valor.strftime("%Y-%m-%d %H:%M:%S")
                    elif valor is None:
                        valor_formateado = "NULL"
                    else:
                        valor_formateado = str(valor)
                    
                    texto_completo.append(f"{campo}: {valor_formateado}")
                
                texto_completo.append("-" * 30)
            
            # Cerrar conexión
            cursor.close()
            conexion.close()
            
            return "\n".join(texto_completo)
            
        except Exception as e:
            logger.error(f"Error al extraer texto de PostgreSQL: {e}")
            return f"Error al extraer texto de PostgreSQL: {str(e)}"
    
    def obtener_metadatos(self, config_consulta):
        """
        Obtiene metadatos de la tabla consultada
        
        Args:
            config_consulta (dict): Configuración de la consulta
            
        Returns:
            dict: Metadatos de la tabla
        """
        try:
            # Crear un ID único para la tabla/consulta
            tabla = config_consulta.get('tabla', 'tabla_desconocida')
            condicion = config_consulta.get('condicion', '')
            
            # Crear un nombre de archivo virtual para la indexación
            nombre_archivo = f"bd_{tabla}_{datetime.now().strftime('%Y%m%d%H%M%S')}.sql"
            
            metadatos = {
                'nombre': nombre_archivo,
                'extension': '.sql',
                'tipo': 'base_de_datos',
                'tabla': tabla,
                'fecha_extraccion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'configuracion': json.dumps(config_consulta)
            }
            
            # Obtener información adicional de la tabla
            conexion, cursor = self._conectar()
            if conexion and cursor:
                try:
                    # Obtener número de registros
                    sql_count = f"SELECT COUNT(*) FROM {tabla}"
                    if condicion:
                        sql_count += f" WHERE {condicion}"
                    
                    cursor.execute(sql_count)
                    total_registros = cursor.fetchone()['count']
                    metadatos['total_registros'] = total_registros
                    
                    # Obtener estructura de la tabla
                    sql_estructura = f"""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = '{tabla}'
                    """
                    cursor.execute(sql_estructura)
                    estructura = cursor.fetchall()
                    
                    # Convertir a formato más simple
                    metadatos['estructura'] = {
                        row['column_name']: row['data_type']
                        for row in estructura
                    }
                    
                except Exception as e:
                    logger.warning(f"No se pudo obtener información detallada de la tabla: {e}")
                finally:
                    cursor.close()
                    conexion.close()
            
            return metadatos
            
        except Exception as e:
            logger.error(f"Error al obtener metadatos de PostgreSQL: {e}")
            return {
                'nombre': f"bd_error_{datetime.now().strftime('%Y%m%d%H%M%S')}.sql",
                'extension': '.sql',
                'error': str(e)
            } 