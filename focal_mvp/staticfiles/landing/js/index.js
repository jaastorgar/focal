document.addEventListener('DOMContentLoaded', () => {
    const menuToggle = document.querySelector('.menu-toggle');
    const mainNav = document.querySelector('.main-nav');

    menuToggle.addEventListener('click', () => {
        mainNav.classList.toggle('active');
    });

    // Cerrar menú si se hace clic fuera o en un enlace
    document.querySelectorAll('.main-nav a').forEach(link => {
        link.addEventListener('click', () => {
            // Solo cerrar si el clic es en un enlace del menú de navegación (no en los botones que tienen una ruta)
            if (link.closest('ul') === mainNav.querySelector('ul') && !link.classList.contains('btn')) {
                mainNav.classList.remove('active');
            }
        });
    });
});