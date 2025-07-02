document.addEventListener('DOMContentLoaded', () => {
    const buttonsContainer = document.querySelector('.perfil-buttons');
    const sections = document.querySelectorAll('.perfil-section');
    const buttons = document.querySelectorAll('.perfil-buttons button');

    // Si no encontramos los elementos necesarios, salimos para evitar errores.
    if (!buttonsContainer || sections.length === 0 || buttons.length === 0) {
        console.error("No se encontraron los elementos necesarios para las pestañas del perfil.");
        return;
    }

    // Función para manejar el cambio de pestaña
    const switchTab = (targetId) => {
        // Ocultamos todas las secciones y quitamos la clase 'active' de todos los botones
        sections.forEach(section => {
            section.classList.remove('visible');
        });
        buttons.forEach(button => {
            button.classList.remove('active');
        });

        // Mostramos la sección correcta y marcamos el botón como activo
        const targetSection = document.getElementById(targetId);
        const targetButton = document.querySelector(`button[onclick*="'${targetId}'"]`);
        
        if (targetSection) {
            targetSection.classList.add('visible');
        }
        if (targetButton) {
            targetButton.classList.add('active');
        }
    };

    // Usamos delegación de eventos en el contenedor de los botones
    buttonsContainer.addEventListener('click', (event) => {
        // Nos aseguramos de que el clic fue en un botón
        if (event.target.tagName === 'BUTTON') {
            // Extraemos el ID de la sección del atributo onclick
            const onclickAttribute = event.target.getAttribute('onclick');
            const targetId = onclickAttribute.match(/'([^']+)'/)[1];
            
            if (targetId) {
                switchTab(targetId);
            }
        }
    });

    // Mostramos la primera sección por defecto al cargar la página
    if (buttons.length > 0) {
        const firstButtonOnclick = buttons[0].getAttribute('onclick');
        const firstTargetId = firstButtonOnclick.match(/'([^']+)'/)[1];
        switchTab(firstTargetId);
    }
});