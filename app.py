import os
import logging
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import threading
import jinja2
import json

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar módulos del proyecto
from procesadores import obtener_procesador, obtener_procesador_postgresql
from modelo_busqueda import Indexador, Buscador
import config

# Crear la aplicación Flask
app = Flask(__name__)
app.secret_key = "indexador_secreto_f8s7df8s7df87sd87f"

# Filtro personalizado para convertir saltos de línea a <br>
@app.template_filter('nl2br')
def nl2br(value):
    """Convierte saltos de línea (\n) a etiquetas <br>"""
    if value:
        return jinja2.utils.markupsafe.Markup(value.replace('\n', '<br>'))
    return ""

# Manejador de error 404
@app.errorhandler(404)
def page_not_found(e):
    """Maneja el error 404 (página no encontrada)"""
    return render_template('404.html'), 404

# Crear directorios necesarios
config.crear_directorios()

# Inicializar el indexador y buscador
indexador = Indexador(directorio_datos=config.DATA_FOLDER, 
                     tamano_fragmento=config.DEFAULT_FRAGMENT_SIZE, 
                     solapamiento=config.DEFAULT_OVERLAP)
buscador = Buscador(indexador)

# Variables para controlar el estado de indexación
indexacion_en_progreso = False
documentos_indexados = set()
bd_indexacion_completada = False

def allowed_file(filename):
    """Verifica si un archivo tiene una extensión permitida"""
    return os.path.splitext(filename)[1].lower() in config.ALLOWED_EXTENSIONS

def procesar_documento(ruta_archivo):
    """Procesa un solo documento y lo indexa"""
    global documentos_indexados
    
    try:
        # Obtener el nombre y extensión del archivo
        nombre_archivo = os.path.basename(ruta_archivo)
        _, extension = os.path.splitext(ruta_archivo)
        
        logger.info(f"Procesando documento: {nombre_archivo}")
        
        # Verificar si ya está indexado
        if nombre_archivo in documentos_indexados:
            logger.info(f"El documento {nombre_archivo} ya está indexado. Omitiendo.")
            return
        
        # Obtener el procesador adecuado
        procesador = obtener_procesador(extension.lower())
        
        if not procesador:
            logger.warning(f"No hay procesador disponible para la extensión {extension}")
            return
        
        # Extraer texto y metadatos
        texto = procesador.extraer_texto(ruta_archivo)
        metadatos = procesador.obtener_metadatos(ruta_archivo)
        
        # Indexar el documento
        indexador.indexar_documento(texto, metadatos)
        
        # Marcar como indexado
        documentos_indexados.add(nombre_archivo)
        
        logger.info(f"Documento {nombre_archivo} procesado e indexado correctamente")
    except Exception as e:
        logger.error(f"Error al procesar el documento {ruta_archivo}: {e}")

def procesar_tabla_postgresql(config_tabla):
    """
    Procesa una tabla de PostgreSQL y la indexa
    
    Args:
        config_tabla (dict): Configuración de la tabla a indexar
    """
    global documentos_indexados
    
    try:
        # Validar configuración
        if not isinstance(config_tabla, dict) or 'tabla' not in config_tabla:
            logger.error("Configuración de tabla inválida")
            return
        
        tabla = config_tabla['tabla']
        logger.info(f"Procesando tabla PostgreSQL: {tabla}")
        
        # Obtener procesador PostgreSQL configurado
        procesador = obtener_procesador_postgresql()
        procesador.establecer_conexion(**config.PG_CONFIG)
        
        # Extraer texto y metadatos
        texto = procesador.extraer_texto(config_tabla)
        metadatos = procesador.obtener_metadatos(config_tabla)
        
        # Verificar si ya está indexado
        nombre_archivo = metadatos['nombre']
        if nombre_archivo in documentos_indexados:
            logger.info(f"La tabla {tabla} ya está indexada con ID {nombre_archivo}. Omitiendo.")
            return
        
        # Indexar el documento
        indexador.indexar_documento(texto, metadatos)
        
        # Marcar como indexado
        documentos_indexados.add(nombre_archivo)
        
        logger.info(f"Tabla PostgreSQL {tabla} procesada e indexada correctamente")
    except Exception as e:
        logger.error(f"Error al procesar la tabla PostgreSQL {config_tabla.get('tabla', 'desconocida')}: {e}")

def indexar_documentos_default():
    """Indexa todos los documentos en la carpeta por defecto"""
    global indexacion_en_progreso, documentos_indexados, bd_indexacion_completada
    
    try:
        indexacion_en_progreso = True
        
        # Limpiar el índice para empezar desde cero
        logger.info("Limpiando índice existente antes de reindexar...")
        indexador.limpiar_indice()
        documentos_indexados.clear()
        bd_indexacion_completada = False
        logger.info("Índice limpiado correctamente, comenzando reindexación...")
        
        # Listar archivos en el directorio por defecto
        for nombre_archivo in os.listdir(config.DEFAULT_DOCS_FOLDER):
            ruta_completa = os.path.join(config.DEFAULT_DOCS_FOLDER, nombre_archivo)
            
            # Verificar si es un archivo y tiene extensión permitida
            if os.path.isfile(ruta_completa) and allowed_file(nombre_archivo):
                procesar_documento(ruta_completa)
        
        # Luego indexar archivos en la carpeta de uploads
        for nombre_archivo in os.listdir(config.UPLOAD_FOLDER):
            ruta_completa = os.path.join(config.UPLOAD_FOLDER, nombre_archivo)
            
            # Verificar si es un archivo y tiene extensión permitida
            if os.path.isfile(ruta_completa) and allowed_file(nombre_archivo):
                procesar_documento(ruta_completa)
        
        # Finalmente, indexar las tablas de PostgreSQL configuradas
        logger.info("Indexando tablas de PostgreSQL...")
        
        # Verificar si hay tablas configuradas para indexar
        if config.PG_TABLES:
            for config_tabla in config.PG_TABLES:
                procesar_tabla_postgresql(config_tabla)
            bd_indexacion_completada = True
            logger.info("Indexación de tablas PostgreSQL completada")
        else:
            logger.info("No hay tablas PostgreSQL configuradas para indexar")
        
        logger.info("Indexación de documentos completada")
    except Exception as e:
        logger.error(f"Error en la indexación de documentos: {e}")
    finally:
        indexacion_en_progreso = False

# Iniciar la indexación de documentos por defecto en un hilo separado
thread_indexacion = threading.Thread(target=indexar_documentos_default)
thread_indexacion.daemon = True
thread_indexacion.start()

@app.route('/')
def index():
    """Página principal de la aplicación"""
    return render_template('index.html', 
                          indexacion_en_progreso=indexacion_en_progreso,
                          num_docs_indexados=len(documentos_indexados),
                          bd_indexacion_completada=bd_indexacion_completada,
                          pg_config=config.PG_CONFIG)

@app.route('/buscar', methods=['POST'])
def buscar():
    """Endpoint para realizar búsquedas"""
    consulta = request.form.get('consulta', '')
    
    if not consulta.strip():
        flash('Por favor ingresa una consulta válida', 'warning')
        return redirect(url_for('index'))
    
    # Verificar si la indexación está en progreso
    if indexacion_en_progreso:
        flash('La indexación de documentos está en progreso. Los resultados pueden estar incompletos.', 'info')
    
    # Realizar la búsqueda
    try:
        respuesta = buscador.responder_pregunta(consulta)
        return render_template('resultados.html', 
                              consulta=consulta,
                              respuesta=respuesta['respuesta'],
                              fragmentos=respuesta['fragmentos_utilizados'])
    except Exception as e:
        logger.error(f"Error al procesar la búsqueda: {e}")
        flash(f'Error al procesar la búsqueda: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/subir', methods=['POST'])
def subir_archivo():
    """Endpoint para subir archivos"""
    if 'archivo' not in request.files:
        flash('No se ha seleccionado ningún archivo', 'warning')
        return redirect(url_for('index'))
        
    archivo = request.files['archivo']
    
    if archivo.filename == '':
        flash('No se ha seleccionado ningún archivo', 'warning')
        return redirect(url_for('index'))
    
    if archivo and allowed_file(archivo.filename):
        # Asegurar que el nombre de archivo sea seguro
        nombre_seguro = secure_filename(archivo.filename)
        ruta_guardado = os.path.join(config.UPLOAD_FOLDER, nombre_seguro)
        
        # Guardar el archivo
        archivo.save(ruta_guardado)
        
        # Procesar e indexar el archivo en un hilo separado
        threading.Thread(target=procesar_documento, args=(ruta_guardado,)).start()
        
        flash(f'Archivo {nombre_seguro} subido correctamente y en proceso de indexación', 'success')
    else:
        extensiones = ', '.join(config.ALLOWED_EXTENSIONS)
        flash(f'Formato de archivo no permitido. Formatos soportados: {extensiones}', 'danger')
        
    return redirect(url_for('index'))

@app.route('/estado')
def estado_indexacion():
    """Endpoint para verificar el estado de la indexación"""
    return jsonify({
        'indexacion_en_progreso': indexacion_en_progreso,
        'documentos_indexados': list(documentos_indexados),
        'num_documentos': len(documentos_indexados),
        'bd_indexacion_completada': bd_indexacion_completada
    })

@app.route('/documentos')
def listar_documentos():
    """Endpoint para listar los documentos indexados"""
    return render_template('documentos.html', 
                          documentos=sorted(list(documentos_indexados)),
                          indexacion_en_progreso=indexacion_en_progreso,
                          bd_indexacion_completada=bd_indexacion_completada)

@app.route('/ver_documento/<path:nombre>')
def ver_documento(nombre):
    """Endpoint para ver/abrir un documento"""
    # Obtener el fragmento de texto a resaltar (si existe)
    fragmento_texto = request.args.get('fragmento_texto', '')
    
    # Buscar el documento en las carpetas disponibles
    posibles_rutas = [
        os.path.join(config.DEFAULT_DOCS_FOLDER, nombre),
        os.path.join(config.UPLOAD_FOLDER, nombre)
    ]
    
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            # Si es un archivo de texto, abrirlo y mostrarlo en una plantilla
            _, extension = os.path.splitext(nombre)
            if extension.lower() == '.txt':
                try:
                    with open(ruta, 'r', encoding='utf-8') as archivo:
                        contenido = archivo.read()
                    
                    # Buscar la posición del fragmento en el texto (si se proporcionó)
                    posicion_fragmento = -1
                    if fragmento_texto:
                        posicion_fragmento = contenido.find(fragmento_texto)
                    
                    return render_template('ver_documento.html', 
                                          nombre=nombre, 
                                          contenido=contenido,
                                          tipo="texto",
                                          fragmento_texto=fragmento_texto,
                                          posicion_fragmento=posicion_fragmento)
                except Exception as e:
                    flash(f'Error al leer el documento: {str(e)}', 'danger')
                    return redirect(url_for('index'))
            else:
                # Para otros tipos de archivos, servir el archivo para descarga/visualización
                return send_from_directory(os.path.dirname(ruta), 
                                          os.path.basename(ruta),
                                          as_attachment=False)
    
    # Comprobar si es un documento de base de datos (no existe como archivo físico)
    if nombre.startswith('bd_') and nombre.endswith('.sql'):
        flash(f'Los documentos de base de datos no pueden visualizarse directamente.', 'info')
        return redirect(url_for('documentos'))
    
    # Si no se encuentra el documento
    flash(f'No se encontró el documento: {nombre}', 'warning')
    return redirect(url_for('index'))

@app.route('/eliminar/<nombre>', methods=['POST'])
def eliminar_documento(nombre):
    """Endpoint para eliminar un documento del índice"""
    global documentos_indexados
    
    try:
        # Eliminar el documento del índice
        if indexador.eliminar_documento(nombre):
            documentos_indexados.discard(nombre)
            flash(f'Documento {nombre} eliminado correctamente del índice', 'success')
        else:
            flash(f'No se encontró el documento {nombre} en el índice', 'warning')
    except Exception as e:
        logger.error(f"Error al eliminar el documento {nombre}: {e}")
        flash(f'Error al eliminar el documento: {str(e)}', 'danger')
        
    return redirect(url_for('documentos'))

@app.route('/reiniciar_indexacion', methods=['POST'])
def reiniciar_indexacion():
    """Endpoint para reiniciar la indexación de documentos"""
    global indexacion_en_progreso
    
    if indexacion_en_progreso:
        flash('La indexación ya está en progreso, espera a que termine', 'warning')
        return redirect(url_for('index'))
    
    # Iniciar la indexación en un hilo separado
    thread_indexacion = threading.Thread(target=indexar_documentos_default)
    thread_indexacion.daemon = True
    thread_indexacion.start()
    
    flash('Se ha iniciado la reindexación de documentos', 'success')
    return redirect(url_for('index'))

@app.route('/ajustar_tamano_fragmentos', methods=['POST'])
def ajustar_tamano_fragmentos():
    """Endpoint para ajustar el tamaño de los fragmentos y reiniciar la indexación"""
    global indexacion_en_progreso, indexador
    
    if indexacion_en_progreso:
        flash('No se pueden cambiar los parámetros mientras hay una indexación en progreso', 'warning')
        return redirect(url_for('index'))
    
    try:
        # Obtener nuevos tamaños del formulario
        tamano_fragmento = int(request.form.get('tamano_fragmento', config.DEFAULT_FRAGMENT_SIZE))
        solapamiento = int(request.form.get('solapamiento', config.DEFAULT_OVERLAP))
        
        # Validar parámetros
        if tamano_fragmento < 100 or tamano_fragmento > 5000:
            flash('El tamaño de fragmento debe estar entre 100 y 5000', 'danger')
            return redirect(url_for('index'))
        
        if solapamiento < 10 or solapamiento > (tamano_fragmento // 2):
            flash('El solapamiento debe estar entre 10 y la mitad del tamaño del fragmento', 'danger')
            return redirect(url_for('index'))
        
        # Actualizar parámetros del indexador
        indexador = Indexador(directorio_datos=config.DATA_FOLDER,
                            tamano_fragmento=tamano_fragmento, 
                            solapamiento=solapamiento)
        
        # Iniciar indexación en un hilo separado
        indexacion_en_progreso = True
        thread = threading.Thread(target=indexar_documentos_default)
        thread.daemon = True
        thread.start()
        
        flash(f'Parámetros actualizados: Tamaño de fragmento={tamano_fragmento}, Solapamiento={solapamiento}. Reindexando...', 'success')
    except Exception as e:
        flash(f'Error al ajustar parámetros: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/configurar_bd', methods=['POST'])
def configurar_bd():
    """Endpoint para configurar la conexión a PostgreSQL y obtener automáticamente todas las tablas"""
    global indexacion_en_progreso
    
    if indexacion_en_progreso:
        flash('No se puede configurar la base de datos mientras hay una indexación en progreso', 'warning')
        return redirect(url_for('index'))
    
    try:
        # Obtener parámetros de conexión
        host = request.form.get('host', 'localhost')
        port = int(request.form.get('port', 5432))
        dbname = request.form.get('dbname', '')
        user = request.form.get('user', '')
        password = request.form.get('password', '')
        
        # Validar datos mínimos
        if not dbname or not user:
            flash('Nombre de la base de datos y usuario son obligatorios', 'danger')
            return redirect(url_for('index'))
        
        # Actualizar configuración
        config.PG_CONFIG.update({
            'host': host,
            'port': port,
            'dbname': dbname,
            'user': user,
            'password': password
        })
        
        # Verificar conexión
        procesador = obtener_procesador_postgresql()
        procesador.establecer_conexion(**config.PG_CONFIG)
        conn, cursor = procesador._conectar()
        
        if conn and cursor:
            # Obtener todas las tablas de la base de datos
            try:
                # Consultar tablas públicas de la base de datos
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                """)
                
                tablas = [row['table_name'] for row in cursor.fetchall()]
                
                if not tablas:
                    flash('No se encontraron tablas en la base de datos', 'warning')
                    conn.close()
                    return redirect(url_for('index'))
                
                # Configurar todas las tablas para indexación
                config.PG_TABLES = []
                for tabla in tablas:
                    config.PG_TABLES.append({
                        'tabla': tabla,
                        'campos': ['*'],  # Indexar todos los campos
                        'limite': 1000    # Limitar a 1000 registros por tabla
                    })
                
                logger.info(f"Se encontraron {len(tablas)} tablas para indexar: {', '.join(tablas)}")
                flash(f'Se indexarán {len(tablas)} tablas: {", ".join(tablas)}', 'success')
                
                # Iniciar indexación en un hilo separado
                thread = threading.Thread(target=indexar_documentos_default)
                thread.daemon = True
                thread.start()
                flash('Iniciando indexación de tablas PostgreSQL...', 'info')
                
            except Exception as e:
                logger.error(f"Error al obtener tablas de la base de datos: {e}")
                flash(f'Error al obtener tablas de la base de datos: {str(e)}', 'danger')
            finally:
                conn.close()
        else:
            flash('No se pudo conectar a la base de datos con los parámetros proporcionados', 'danger')
    
    except Exception as e:
        logger.error(f"Error al configurar la base de datos: {e}")
        flash(f'Error al configurar la base de datos: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000) 