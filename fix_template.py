import re

# Ruta del archivo HTML
archivo_html = "templates/resultados.html"

# Leer el contenido actual del archivo
with open(archivo_html, 'r', encoding='utf-8') as f:
    contenido = f.read()

# Patrón para encontrar las divs duplicadas con íconos
patron_div_antiguo = r'<div>\s*<i class="fas fa-file-[^>]*></i>\s*{{ fragmento\.documento }}\s*</div>'

# Reemplazar con el nuevo formato que incluye la condición es_bd
nuevo_div = '''<div>
                                <i class="fas {% if fragmento.es_bd %}fa-database{% 
                                    elif fragmento.documento.endswith('.pdf') %}fa-file-pdf{% 
                                    elif fragmento.documento.endswith('.docx') %}fa-file-word{% 
                                    elif fragmento.documento.endswith('.xlsx') %}fa-file-excel{% 
                                    else %}fa-file-text{% endif %} text-primary me-2"></i>
                                {{ fragmento.documento }}
                            </div>'''

# Reemplazar todas las ocurrencias del div antiguo con el nuevo
nuevo_contenido = re.sub(patron_div_antiguo, nuevo_div, contenido, flags=re.DOTALL)

# Verificar que no haya dos divs idénticos seguidos
patron_divs_duplicados = nuevo_div + r'\s*' + nuevo_div
if re.search(patron_divs_duplicados, nuevo_contenido, flags=re.DOTALL):
    # Si hay divs duplicados, mantener solo uno
    nuevo_contenido = re.sub(patron_divs_duplicados, nuevo_div, nuevo_contenido, flags=re.DOTALL)

# Guardar el archivo modificado
with open(archivo_html, 'w', encoding='utf-8') as f:
    f.write(nuevo_contenido)

print(f"Archivo {archivo_html} actualizado correctamente.") 