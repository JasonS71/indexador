// Scripts para el Indexador y Buscador Inteligente de Documentos

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Manejar la animación de tarjetas al cargar la página
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
    });
    
    // Funcionalidad para verificar el estado de indexación si está en progreso
    function checkIndexingStatus() {
        const indexingElement = document.querySelector('.indexacion-en-progreso');
        if (indexingElement) {
            fetch('/estado')
                .then(response => response.json())
                .then(data => {
                    if (!data.indexacion_en_progreso) {
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    }
                })
                .catch(error => console.error('Error al verificar estado:', error));
        }
    }
    
    // Si existe el elemento de indexación en progreso, verificar su estado periódicamente
    const indexingStatus = document.querySelector('.indexacion-en-progreso');
    if (indexingStatus) {
        setInterval(checkIndexingStatus, 5000); // Verificar cada 5 segundos
    }
    
    // Validación del formulario de búsqueda
    const searchForm = document.querySelector('form[action*="buscar"]');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const consultaInput = this.querySelector('input[name="consulta"]');
            if (!consultaInput.value.trim()) {
                e.preventDefault();
                alert('Por favor ingresa una consulta válida');
                consultaInput.focus();
            }
        });
    }
    
    // Validación del formulario de subida de archivos
    const uploadForm = document.querySelector('form[action*="subir"]');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            const fileInput = this.querySelector('input[type="file"]');
            if (!fileInput.files.length) {
                e.preventDefault();
                alert('Por favor selecciona un archivo para subir');
                fileInput.focus();
            }
        });
    }
    
    // Mostrar el nombre del archivo seleccionado en el input de archivo
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileName = this.files[0]?.name;
            const fileLabel = this.nextElementSibling;
            if (fileLabel && fileName) {
                fileLabel.textContent = fileName;
            }
        });
    }
}); 