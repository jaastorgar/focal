document.addEventListener('DOMContentLoaded', () => {
    // Seleccionamos los elementos clave
    const fileInput = document.getElementById('id_archivo_ventas');
    const customButton = document.querySelector('.file-upload-label'); // Nuestro botón falso
    const fileNameDisplay = document.getElementById('file-name-display');

    // Verificamos que todos los elementos existan para evitar errores
    if (fileInput && customButton && fileNameDisplay) {
        
        // --- LA SOLUCIÓN REAL ---
        // Cuando el usuario hace clic en nuestro botón falso...
        customButton.addEventListener('click', () => {
            // ...le decimos al JavaScript que haga clic en el botón de archivo real (que está oculto).
            fileInput.click();
        });
        // --- FIN DE LA SOLUCIÓN ---

        // Esta parte se encarga de mostrar el nombre del archivo una vez seleccionado
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                fileNameDisplay.textContent = fileInput.files[0].name;
            } else {
                fileNameDisplay.textContent = 'Ningún archivo seleccionado';
            }
        });
    }
});