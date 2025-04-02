import re

# Ruta del archivo HTML
archivo_html = "templates/index.html"

# Leer el contenido actual del archivo
with open(archivo_html, 'r', encoding='utf-8') as f:
    contenido = f.read()

# Patrón para buscar el div que contiene el campo tablas_json
patron = r'<div class="mb-3">\s*<label for="tablas_json".*?</div>\s*</div>'

# Reemplazar con una cadena vacía (eliminar)
nuevo_contenido = re.sub(patron, '', contenido, flags=re.DOTALL)

# Guardar el archivo modificado
with open(archivo_html, 'w', encoding='utf-8') as f:
    f.write(nuevo_contenido)

print(f"Archivo {archivo_html} actualizado correctamente.") 