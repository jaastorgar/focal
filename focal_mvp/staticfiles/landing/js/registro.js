/**
 * FOCAL - Script para la Página de Registro
 *
 * Mejoras:
 * 1. Mensajes de alerta desaparecen automáticamente después de 5 segundos.
 * 2. Validación de contraseña en tiempo real.
 * 3. Requisitos de contraseña se muestran solo al enfocar el campo de contraseña.
 */
document.addEventListener('DOMContentLoaded', () => {
    
    // --- MEJORA 1: Mensajes de alerta que desaparecen ---
    const alertMessages = document.querySelectorAll('.alert');
    alertMessages.forEach(message => {
        setTimeout(() => {
            message.classList.add('fade-out');
            message.addEventListener('transitionend', () => message.remove(), { once: true });
        }, 5000); // 5 segundos
    });

    // --- MEJORAS 2 y 3: Validación de contraseña ---
    const passwordInput = document.getElementById('id_almacenero-password');
    const confirmInput = document.getElementById('id_almacenero-confirm_password');
    const feedbackContainer = document.getElementById('password-feedback');

    // Si los elementos de contraseña no existen, no continuamos.
    if (!passwordInput || !confirmInput || !feedbackContainer) {
        return;
    }

    const requirements = {
        length: document.getElementById('req-length'),
        uppercase: document.getElementById('req-uppercase'),
        lowercase: document.getElementById('req-lowercase'),
        number: document.getElementById('req-number'),
        special: document.getElementById('req-special'),
        match: document.getElementById('req-match')
    };

    // Muestra el contenedor de requisitos al enfocar el campo de contraseña
    passwordInput.addEventListener('focus', () => {
        feedbackContainer.classList.add('visible');
    });

    // Oculta el contenedor de requisitos al salir del campo de contraseña
    passwordInput.addEventListener('blur', () => {
        feedbackContainer.classList.remove('visible');
    });

    const validateRequirement = (element, isValid) => {
        if (!element) return;
        if (isValid) {
            element.classList.add('valid');
            element.classList.remove('invalid');
        } else {
            element.classList.add('invalid');
            element.classList.remove('valid');
        }
    };

    const validatePassword = () => {
        const password = passwordInput.value;
        validateRequirement(requirements.length, password.length >= 8 && password.length <= 12);
        validateRequirement(requirements.uppercase, /[A-Z]/.test(password));
        validateRequirement(requirements.lowercase, /[a-z]/.test(password));
        validateRequirement(requirements.number, /[0-9]/.test(password));
        validateRequirement(requirements.special, /[^A-Za-z0-9]/.test(password));
        checkPasswordMatch();
    };

    const checkPasswordMatch = () => {
        const password = passwordInput.value;
        const confirmValue = confirmInput.value;
        const passwordsMatch = password === confirmValue && confirmValue.length > 0;
        
        validateRequirement(requirements.match, passwordsMatch);

        if (confirmValue.length > 0 && !passwordsMatch) {
            confirmInput.setCustomValidity("Las contraseñas no coinciden.");
        } else {
            confirmInput.setCustomValidity("");
        }
    };

    passwordInput.addEventListener('input', validatePassword);
    confirmInput.addEventListener('input', checkPasswordMatch);
});