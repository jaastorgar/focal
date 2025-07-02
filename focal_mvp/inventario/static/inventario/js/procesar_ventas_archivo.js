document.addEventListener('DOMContentLoaded', () => {
    // Busca el input de archivo por el ID que Django le asigna
    const fileInput = document.getElementById('id_archivo_ventas');
    const fileNameDisplay = document.getElementById('file-name-display');

    if (fileInput && fileNameDisplay) {
        // Añade un listener que se activa cuando el usuario selecciona un archivo
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                // Mostramos el nombre del primer archivo seleccionado
                fileNameDisplay.textContent = fileInput.files[0].name;
            } else {
                // Si el usuario cancela, volvemos al mensaje por defecto
                fileNameDisplay.textContent = 'Ningún archivo seleccionado';
            }
        });
    }
});