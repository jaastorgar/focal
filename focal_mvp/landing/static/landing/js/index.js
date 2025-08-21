document.addEventListener('DOMContentLoaded', () => {
    const menuToggle = document.querySelector('.menu-toggle');
    const mainNav = document.querySelector('.main-nav');

    // === FUNCIONALIDAD DEL MENÚ MÓVIL ===
    if (menuToggle && mainNav) {
        menuToggle.addEventListener('click', () => {
            mainNav.classList.toggle('active');
        });

        // Cerrar menú si se hace clic fuera o en un enlace
        document.querySelectorAll('.main-nav a').forEach(link => {
            link.addEventListener('click', () => {
                if (link.closest('ul') === mainNav.querySelector('ul') && !link.classList.contains('btn')) {
                    mainNav.classList.remove('active');
                }
            });
        });
    }
    // ===================================

    // === FUNCIONALIDAD DE ALERTAS AUTOMÁTICAS ===
    // Buscar todas las alertas en la página
    const alertas = document.querySelectorAll('.alert');
    
    if (alertas.length > 0) {
        alertas.forEach(alerta => {
            const tipoAlerta = Array.from(alerta.classList).find(cls => 
                cls.startsWith('alert-') && !cls.includes('error') && !cls.includes('danger')
            );
            
            if (tipoAlerta) {
                setTimeout(() => {
                    alerta.style.transition = 'opacity 0.5s ease-out';
                    alerta.style.opacity = '0';
                    
                    setTimeout(() => {
                        alerta.style.display = 'none';
                    }, 500); 
                }, 5000); 
            }
        });
    }
    // ==========================================

    // === FUNCIONALIDAD DE BOTÓN DE CIERRE DE ALERTAS ===
    // Buscar botones de cierre dentro de las alertas
    const botonesCerrar = document.querySelectorAll('.alert-close, .alert .close, .alert button[type="button"]');
    
    botonesCerrar.forEach(boton => {
        boton.addEventListener('click', function() {
            const alerta = this.closest('.alert');
            if (alerta) {
                alerta.style.transition = 'opacity 0.3s ease-out';
                alerta.style.opacity = '0';
                
                setTimeout(() => {
                    alerta.style.display = 'none';
                }, 300); 
            }
        });
    });
});