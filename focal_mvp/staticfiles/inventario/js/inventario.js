document.addEventListener('DOMContentLoaded', () => {
    // Seleccionamos todos los mensajes de alerta individuales
    const alertMessages = document.querySelectorAll('.alert');

    alertMessages.forEach(message => {
        // Establecemos un temporizador para cada mensaje
        setTimeout(() => {
            // Añadimos una clase para iniciar la transición de desvanecimiento
            message.classList.add('fade-out');

            // Escuchamos el evento que se dispara cuando la transición termina
            message.addEventListener('transitionend', () => {
                message.remove();
            }, { once: true }); // { once: true } asegura que el listener se ejecute solo una vez

        }, 5000); // El mensaje comenzará a desvanecerse después de 5 segundos
    });
});