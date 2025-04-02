"""
Script para eliminar los estilos CSS duplicados en la plantilla de resultados.
"""
# Ruta del archivo HTML
archivo_html = "templates/resultados.html"

with open(archivo_html, 'r', encoding='utf-8') as f:
    contenido = f.read()

# Buscar la sección de estilos CSS
inicio_css = contenido.find('{% block extra_css %}')
if inicio_css != -1:
    # Extraer todo el bloque CSS
    fin_css = contenido.find('</style>', inicio_css)
    if fin_css != -1:
        fin_css += 8  # Incluir la etiqueta de cierre </style>
        
        # Obtener el bloque CSS completo
        bloque_css = contenido[inicio_css:fin_css]
        
        # Crear un bloque CSS actualizado sin duplicados
        nuevo_css = """{% block extra_css %}
<style>
    /* Estilos para los fragmentos de texto */
    .fragmento-texto {
        font-size: 0.95rem;
        line-height: 1.6;
        background-color: #f9f9f9;
        padding: 1rem;
        border-radius: 6px;
        border-left: 4px solid #007bff;
        white-space: pre-line;
    }
    
    /* Color principal consistente */
    .text-primary {
        color: #007bff !important;
    }
    
    /* Contenedor de insignias (badges) */
    .badge-container {
        display: flex;
        flex-direction: column;
    }
    
    /* Contenedor para detalles de similitud */
    .similitud-detalle {
        display: flex;
        gap: 5px;
    }
    
    /* Formato especial para resultados de Excel */
    .resultado-excel .fragmento-texto {
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
    }
    
    /* Formato especial para resultados de PostgreSQL */
    .resultado-bd .fragmento-texto {
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 0.9rem;
        background-color: #f5f5f5;
        border-left: 4px solid #336791; /* Color azul de PostgreSQL */
    }
    
    /* Resaltado para nombres de campos en PostgreSQL */
    .fragmento-texto .campo-bd {
        color: #336791;
        font-weight: bold;
    }
    
    /* Resaltar registros de BD */
    .fragmento-texto .registro-bd {
        background-color: #e9ecef;
        padding: 4px;
        margin: 8px 0;
        border-radius: 4px;
        display: block;
    }
    
    /* Estilos para encabezados de tarjeta */
    .card-header {
        background-color: #f8f9fa;
    }
    
    /* Resaltado para términos encontrados */
    .termino-match {
        background-color: rgba(255, 235, 59, 0.4);
        padding: 2px 0;
        border-radius: 3px;
    }
</style>
"""
        
        # Reemplazar el bloque CSS original con el nuevo
        nuevo_contenido = contenido.replace(bloque_css, nuevo_css)
        
        # Guardar el archivo modificado
        with open(archivo_html, 'w', encoding='utf-8') as f:
            f.write(nuevo_contenido)
        
        print(f"Archivo {archivo_html} actualizado correctamente.")
    else:
        print("No se encontró la etiqueta de cierre de estilos")
else:
    print("No se encontró el bloque de estilos extra") 