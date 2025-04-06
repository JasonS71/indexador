# Indexador de Documentos

## Descripción
Sistema de búsqueda inteligente que permite indexar y buscar información en documentos de diferentes formatos (PDF, DOCX, TXT, XLSX) y bases de datos PostgreSQL utilizando tecnología de procesamiento de lenguaje natural.

## Características Principales
- Soporte para múltiples formatos de documentos (PDF, DOCX, TXT, XLSX)
- Conexión e indexación de tablas PostgreSQL
- Interfaz web intuitiva para gestión de documentos
- Visualización de resultados con contexto (número de página/línea)
- Resaltado automático de coincidencias y términos relevantes
- Configuración ajustable de parámetros de indexación
- Visualización especializada para contenido de Excel y PostgreSQL

## Guía Visual
A continuación se muestran los pasos principales para utilizar el sistema:

### 1. Interfaz Principal
Una vez inicializado el proyecto, se mostrará la siguiente interfaz:

<!-- IMAGEN 1: Captura de pantalla de la interfaz principal del sistema -->
![Interfaz Principal](readme_imagenes/Interfaz%20Principal.png)

### 2. Conexión a PostgreSQL
Para conectar a una base de datos PostgreSQL, complete el formulario como se muestra:

<!-- IMAGEN 2: Captura de pantalla del formulario de conexión a PostgreSQL -->
![Conexión a PostgreSQL](readme_imagenes/Conexion%20Postgres.png)

### 3. Subida de Documentos
Para subir documentos al sistema, utilice la sección de subida de archivos:

<!-- IMAGEN 3: Captura de pantalla de la sección para subir documentos -->
![Subida de Documentos](readme_imagenes/Subir%20documentos.png)

### 4. Resultados de Búsqueda
Los resultados de búsqueda se mostrarán con las coincidencias resaltadas:

<!-- IMAGEN 4: Captura de pantalla de los resultados de búsqueda -->
![Resultados de Búsqueda](readme_imagenes/Resultado%20de%20Busqueda.png)

## Tecnologías Utilizadas
- Python 3.9+
- Flask (Framework web)
- Sentence-Transformers (Modelos de embeddings para NLP)
- PyPDF2 (Procesamiento de PDFs)
- python-docx (Procesamiento de documentos Word)
- pandas y openpyxl (Procesamiento de Excel)
- psycopg2 (Conexión a PostgreSQL)
- Bootstrap 5 (Interfaz de usuario)
- Font Awesome (Iconos)

## Estructura del Proyecto
```
proyecto/
├── app.py                      # Aplicación principal Flask
├── config.py                   # Configuración del sistema
├── templates/                  # Plantillas HTML
│   ├── index.html              # Página principal y búsqueda
│   ├── documentos.html         # Gestión de documentos
│   ├── resultados.html         # Visualización de resultados
│   ├── ver_documento.html      # Visor de documentos
│   └── base.html               # Plantilla base
├── static/                     # Archivos estáticos (CSS, JS)
├── procesadores/               # Procesadores de documentos
│   ├── pdf_procesador.py       # Procesador de archivos PDF
│   ├── docx_procesador.py      # Procesador de archivos Word
│   ├── txt_procesador.py       # Procesador de archivos de texto
│   ├── xlsx_procesador.py      # Procesador de archivos Excel
│   └── postgresql_procesador.py # Procesador de datos PostgreSQL
├── modelo_busqueda/            # Lógica de búsqueda
│   ├── indexador.py            # Indexación de documentos
│   └── buscador.py             # Motor de búsqueda
├── uploads/                    # Directorio para archivos subidos
├── documentos_por_defecto/     # Documentos incluidos por defecto
└── indexados_datos/            # Directorio para datos indexados
```

## Requisitos Previos
- Python 3.9 o superior
- Pip (gestor de paquetes de Python)
- PostgreSQL (opcional, solo si se desea indexar bases de datos)

## Instalación

### Clonar el Repositorio
```bash
git clone https://github.com/JasonS71/indexador.git
cd indexador
```

### Crear Entorno Virtual (Recomendado)
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate
```

### Instalar Dependencias
```bash
pip install -r requirements.txt
```

## Configuración Inicial
```bash
# Crear directorios necesarios (si no existen)
mkdir -p static templates uploads documentos_por_defecto indexados_datos
```

## Uso
1. Iniciar el servidor:
```bash
python app.py
```
2. Acceder a `http://localhost:5000` en el navegador
3. Subir documentos a través de la interfaz o usar los documentos predeterminados
4. Realizar búsquedas en los documentos indexados

## Funcionalidades de Búsqueda
El sistema ofrece dos tipos de búsqueda combinados:
1. **Búsqueda Semántica**: Encuentra resultados conceptualmente relacionados con la consulta, incluso si no comparten las mismas palabras exactas.
2. **Búsqueda por Palabras Clave**: Prioriza resultados que contengan al menos una palabra clave de la consulta.

Todos los resultados mostrarán:
- Puntuación de similitud
- Número de coincidencias de palabras clave
- Ubicación en el documento (página/línea)
- Resaltado automático de términos relevantes

## Configuración Avanzada
### Parámetros de Indexación
- **Tamaño de Fragmento**: Define la longitud de los fragmentos de texto (100-5000 caracteres)
- **Solapamiento**: Define el solapamiento entre fragmentos consecutivos (10-2500 caracteres)

Estos parámetros pueden ajustarse desde la interfaz web en la sección "Configuración Avanzada".

### Conexión a PostgreSQL
Puedes configurar la conexión a PostgreSQL directamente desde la interfaz web:
1. En la sección "Conexión a PostgreSQL", introduce los datos de conexión:
   - Host
   - Puerto
   - Nombre de la BD
   - Usuario
   - Contraseña
2. Haz clic en "Configurar y conectar"

El sistema automáticamente detectará todas las tablas disponibles en la base de datos y las indexará para su búsqueda.

## Funcionamiento Técnico
1. **Procesamiento de Documentos**
   - Los documentos se procesan según su formato específico
   - Se extraen texto y metadatos (autor, fecha, etc.)
   - Se divide el texto en fragmentos con solapamiento
   - Se preserva información de posición (página/línea)

2. **Indexación**
   - Cada fragmento se convierte en un vector de embedding usando Sentence-Transformers
   - Los embeddings, texto original y metadatos se almacenan de forma eficiente
   - El sistema mantiene un índice de todos los documentos procesados

3. **Búsqueda Híbrida**
   - La consulta se procesa para extraer palabras clave importantes
   - Se genera un embedding de la consulta
   - Se compara con los embeddings almacenados (similitud coseno)
   - Se verifica la presencia de palabras clave exactas
   - Se combina la similitud semántica (70%) con coincidencias de palabras clave (30%)
   - Se devuelven los fragmentos más relevantes ordenados por puntuación combinada

## Licencia
[MIT](LICENSE)

## Contacto
Para reportar problemas o sugerir mejoras, por favor abrir un issue en el repositorio de GitHub.
