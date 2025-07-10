document.addEventListener('DOMContentLoaded', () => {
    const passwordInput = document.getElementById('id_almacenero-password');
    const confirmInput = document.getElementById('id_almacenero-confirm_password');
    
    // Un objeto para mantener todos los elementos de feedback de la contraseña
    const requirements = {
        length: document.getElementById('req-length'),
        uppercase: document.getElementById('req-uppercase'),
        lowercase: document.getElementById('req-lowercase'),
        number: document.getElementById('req-number'),
        special: document.getElementById('req-special'),
        match: document.getElementById('req-match')
    };

    // Si los elementos no existen en la página, no hacemos nada.
    if (!passwordInput || !confirmInput || !requirements.length) {
        console.warn("No se encontraron los elementos necesarios para la validación de contraseña.");
        return;
    }

    // Función para validar un requisito específico y actualizar su clase CSS
    const validateRequirement = (element, isValid) => {
        if (isValid) {
            element.classList.add('valid');
            element.classList.remove('invalid');
        } else {
            element.classList.add('invalid');
            element.classList.remove('valid');
        }
    };

    // Función principal que se ejecuta cada vez que el usuario escribe en el campo de contraseña
    const validatePassword = () => {
        const password = passwordInput.value;
        validateRequirement(requirements.length, password.length >= 8 && password.length <= 12);
        validateRequirement(requirements.uppercase, /[A-Z]/.test(password));
        validateRequirement(requirements.lowercase, /[a-z]/.test(password));
        validateRequirement(requirements.number, /[0-9]/.test(password));
        validateRequirement(requirements.special, /[^A-Za-z0-9]/.test(password));
        
        // También validamos la coincidencia cada vez que la contraseña principal cambia
        checkPasswordMatch();
    };

    // Función principal que se ejecuta cada vez que el usuario escribe en el campo de confirmación
    const checkPasswordMatch = () => {
        const password = passwordInput.value;
        const confirmValue = confirmInput.value;
        const passwordsMatch = password === confirmValue && confirmValue.length > 0;
        
        validateRequirement(requirements.match, passwordsMatch);

        // Usamos la API de validación del navegador para la confirmación
        if (confirmValue.length > 0 && !passwordsMatch) {
            confirmInput.setCustomValidity("Las contraseñas no coinciden.");
        } else {
            confirmInput.setCustomValidity("");
        }
    };

    // Asignamos los listeners a los eventos 'input'
    passwordInput.addEventListener('input', validatePassword);
    confirmInput.addEventListener('input', checkPasswordMatch);
});