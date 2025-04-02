"""
Script para corregir la plantilla de resultados y evitar íconos duplicados.
Este script reemplaza tanto el div antiguo como el duplicado con una única versión actualizada.
"""

# Ruta del archivo HTML
archivo_html = "templates/resultados.html"

with open(archivo_html, 'r', encoding='utf-8') as f:
    lineas = f.readlines()

nuevo_contenido = []
in_header = False
icon_added = False

for i, linea in enumerate(lineas):
    # Detectar si estamos en la sección del card-header
    if '<div class="card-header d-flex justify-content-between align-items-center">' in linea:
        in_header = True
        icon_added = False
        nuevo_contenido.append(linea)
    # Si es una línea con el ícono del documento
    elif in_header and ('<i class="fas fa-file-' in linea or '<i class="fas {% if fragmento.es_bd %}fa-database' in linea):
        # Si es el primer ícono que encontramos en este header
        if not icon_added:
            # Añadir el ícono actualizado
            nuevo_contenido.append('''                            <div>
                                <i class="fas {% if fragmento.es_bd %}fa-database{% 
                                    elif fragmento.documento.endswith('.pdf') %}fa-file-pdf{% 
                                    elif fragmento.documento.endswith('.docx') %}fa-file-word{% 
                                    elif fragmento.documento.endswith('.xlsx') %}fa-file-excel{% 
                                    else %}fa-file-text{% endif %} text-primary me-2"></i>
                                {{ fragmento.documento }}
                            </div>\n''')
            icon_added = True
            
            # Saltarse las siguientes líneas del div anterior
            for j in range(3):
                if i + j < len(lineas) and ('</div>' in lineas[i + j]):
                    break
        # Si ya añadimos un ícono, saltamos esta línea
    # Si llegamos a la sección de botones, desactivamos el flag
    elif in_header and '<a href="{{ url_for(' in linea:
        in_header = False
        nuevo_contenido.append(linea)
    else:
        nuevo_contenido.append(linea)

# Guardar el archivo modificado
with open(archivo_html, 'w', encoding='utf-8') as f:
    f.writelines(nuevo_contenido)

print(f"Archivo {archivo_html} actualizado correctamente.") 