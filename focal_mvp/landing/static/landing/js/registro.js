document.addEventListener('DOMContentLoaded', () => {
    // --- SELECTORES CON PREFIJOS ---
    // Usamos los prefijos 'almacenero' y 'empresa' que definimos en la vista
    const passwordInput = document.getElementById('id_almacenero-password1');
    const confirmInput = document.getElementById('id_almacenero-password2');
    const feedbackContainer = document.getElementById('password-feedback');

    if (!passwordInput || !confirmInput || !feedbackContainer) {
        console.warn("Elementos de validación de contraseña no encontrados. El script no se ejecutará.");
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

    passwordInput.addEventListener('focus', () => {
        feedbackContainer.style.display = 'block';
    });

    passwordInput.addEventListener('blur', () => {
        feedbackContainer.style.display = 'none';
    });

    const validateRequirement = (element, isValid) => {
        if (!element) return;
        element.classList.toggle('valid', isValid);
        element.classList.toggle('invalid', !isValid);
    };

    const validatePassword = () => {
        const password = passwordInput.value;
        validateRequirement(requirements.length, password.length >= 8 && password.length <= 12);
        validateRequirement(requirements.uppercase, /[A-Z]/.test(password));
        validateRequirement(requirements.lowercase, /[a-z]/.test(password));
        validateRequirement(requirements.number, /[0-9]/.test(password));
        validateRequirement(requirements.special, /[\W_]/.test(password));
        checkPasswordMatch();
    };

    const checkPasswordMatch = () => {
        const password = passwordInput.value;
        const confirmValue = confirmInput.value;
        const passwordsMatch = password === confirmValue && confirmValue.length > 0;
        
        validateRequirement(requirements.match, passwordsMatch);
    };

    passwordInput.addEventListener('input', validatePassword);
    confirmInput.addEventListener('input', checkPasswordMatch);
});