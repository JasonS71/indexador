"""
Script para iniciar la aplicación de Indexador y Buscador Inteligente de Documentos.
Este script simplifica el inicio para los usuarios.
"""

import os
import sys
import webbrowser
import time
import threading

def abrir_navegador():
    """Abre el navegador después de un breve retraso"""
    time.sleep(2)  # Dar tiempo a que la aplicación inicie
    webbrowser.open('http://localhost:5000')

if __name__ == "__main__":
    print("=================================================================")
    print("      Indexador y Buscador Inteligente de Documentos")
    print("=================================================================")
    print("")
    print("Iniciando la aplicación...")
    
    # Verificar que las dependencias estén instaladas
    try:
        import flask
        import sentence_transformers
        print("✓ Dependencias verificadas correctamente")
    except ImportError as e:
        print("✗ Error: Falta instalar algunas dependencias")
        print(f"  Error específico: {str(e)}")
        print("\nPor favor, ejecuta antes: pip install -r requirements.txt")
        sys.exit(1)
    
    # Verificar directorios necesarios
    directorios = ["uploads", "documentos_por_defecto", "indexados_datos"]
    for directorio in directorios:
        if not os.path.exists(directorio):
            os.makedirs(directorio)
            print(f"✓ Creado directorio: {directorio}")
    
    # Abrir el navegador automáticamente
    threading.Thread(target=abrir_navegador, daemon=True).start()
    
    print("\nIniciando servidor web en http://localhost:5000")
    print("Presiona Ctrl+C para detener la aplicación\n")
    
    # Importar e iniciar la aplicación
    from app import app
    app.run(debug=True, port=5000) 