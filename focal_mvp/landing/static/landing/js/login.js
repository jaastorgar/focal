/**
 * FOCAL - Script para la Página de Login
 *
 * Funcionalidad: Oculta automáticamente los mensajes de alerta
 * (tanto los generales como los de error del formulario) después de 5 segundos.
 */
document.addEventListener('DOMContentLoaded', () => {
    // Seleccionamos todos los elementos que puedan contener mensajes de error o notificación
    const alertMessages = document.querySelectorAll('.alert, .non-field-errors');

    alertMessages.forEach(message => {
        setTimeout(() => {
            message.classList.add('fade-out');
            message.addEventListener('transitionend', () => {
                message.remove();
            }, { once: true });

        }, 5000); 
    });
});