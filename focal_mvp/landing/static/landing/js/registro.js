// registro.js
document.addEventListener('DOMContentLoaded', () => {
    // === FUNCIÓN DE VALIDACIÓN DE RUN/RUT ===
    function validarRunRut(runRut) {
        // Limpiar el input: mayúsculas, sin puntos, sin guiones
        let valor = runRut.replace(/\./g, '').replace(/-/g, '').toUpperCase().trim();

        // Verificar formato mínimo (al menos 2 caracteres: número y dígito verificador)
        if (valor.length < 2) return false;

        // Separar el cuerpo del dígito verificador
        const cuerpo = valor.slice(0, -1);
        const dv = valor.slice(-1);

        // Verificar que el cuerpo sea numérico
        if (!/^\d+$/.test(cuerpo)) return false;

        // Calcular dígito verificador esperado
        let suma = 0;
        let multiplo = 2;

        // Recorrer el cuerpo de derecha a izquierda
        for (let i = cuerpo.length - 1; i >= 0; i--) {
            suma += parseInt(cuerpo.charAt(i)) * multiplo;
            multiplo++;
            if (multiplo === 8) multiplo = 2;
        }

        const resto = suma % 11;
        let dvCalculado = 11 - resto;

        if (dvCalculado === 11) dvCalculado = '0';
        else if (dvCalculado === 10) dvCalculado = 'K';
        else dvCalculado = dvCalculado.toString();

        // Comparar con el dígito ingresado
        return dv === dvCalculado;
    }

    // === 1. VALIDACIÓN DE CONTRASEÑA (usando data attributes) ===
    const passwordInput = document.querySelector('[id$="password1"]'); // Busca cualquier ID que termine en 'password1'
    const confirmInput = document.querySelector('[id$="password2"]');  // Busca cualquier ID que termine en 'password2'
    const feedbackContainer = document.getElementById('password-feedback');

    if (passwordInput && confirmInput && feedbackContainer) {
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
    } else {
        // Opcional: mensaje de depuración si no se encuentran los campos
        // console.log("Campos de contraseña no encontrados, se omite la validación.");
    }

    // === 2. VALIDACIÓN DE RUN/RUT ===
    // Validar RUN del administrador
    const runInput = document.querySelector('input[name$="run"]');
    if (runInput) {
        const runFeedback = document.createElement('div');
        runFeedback.className = 'run-feedback';
        runFeedback.style.fontSize = '0.85rem';
        runFeedback.style.marginTop = '5px';
        runInput.parentNode.insertBefore(runFeedback, runInput.nextSibling);

        const validarRun = () => {
            const valor = runInput.value.trim();
            if (valor === '') {
                runFeedback.textContent = '';
                runFeedback.className = 'run-feedback';
            } else if (validarRunRut(valor)) {
                runFeedback.textContent = 'RUN válido';
                runFeedback.className = 'run-feedback valid';
                runFeedback.style.color = 'green';
            } else {
                runFeedback.textContent = 'RUN inválido';
                runFeedback.className = 'run-feedback invalid';
                runFeedback.style.color = 'red';
            }
        };

        runInput.addEventListener('input', validarRun);
        runInput.addEventListener('blur', validarRun);
    }

    // Validar RUT de la empresa
    const rutInput = document.querySelector('input[name$="rut"]');
    if (rutInput) {
        const rutFeedback = document.createElement('div');
        rutFeedback.className = 'rut-feedback';
        rutFeedback.style.fontSize = '0.85rem';
        rutFeedback.style.marginTop = '5px';
        rutInput.parentNode.insertBefore(rutFeedback, rutInput.nextSibling);

        const validarRut = () => {
            const valor = rutInput.value.trim();
            if (valor === '') {
                rutFeedback.textContent = '';
                rutFeedback.className = 'rut-feedback';
            } else if (validarRunRut(valor)) {
                rutFeedback.textContent = 'RUT válido';
                rutFeedback.className = 'rut-feedback valid';
                rutFeedback.style.color = 'green';
            } else {
                rutFeedback.textContent = 'RUT inválido';
                rutFeedback.className = 'rut-feedback invalid';
                rutFeedback.style.color = 'red';
            }
        };

        rutInput.addEventListener('input', validarRut);
        rutInput.addEventListener('blur', validarRut);
    }

    // === 3. CARGA DINÁMICA DE COMUNAS POR REGIÓN (usando data attributes) ===
    // Busca todos los selects de región que tengan el atributo data-region-target
    document.querySelectorAll('select[data-region-target]').forEach(regionSelect => {
        const formPrefix = regionSelect.dataset.regionTarget; // Obtiene 'almacenero' o 'empresa'

        // Encuentra el select de comuna correspondiente usando el mismo data attribute
        const comunaSelect = document.querySelector(`select[data-comuna-target="${formPrefix}"]`);

        if (!comunaSelect) {
            console.warn(`Select de comuna no encontrado para el target: ${formPrefix}`);
            return;
        }

        // Función para cargar comunas
        const cargarComunas = () => {
            const region = regionSelect.value;

            // Limpiar comunas
            comunaSelect.innerHTML = '<option value="">Cargando...</option>';

            if (!region) {
                comunaSelect.innerHTML = '<option value="">Primero seleccione una región</option>';
                return;
            }

            fetch(`/get-comunas/?region=${encodeURIComponent(region)}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    comunaSelect.innerHTML = '<option value="">Seleccione la comuna</option>';
                    if (data.comunas && data.comunas.length > 0) {
                        data.comunas.forEach(comuna => {
                            const option = document.createElement('option');
                            option.value = comuna[0];
                            option.textContent = comuna[1];
                            comunaSelect.appendChild(option);
                        });
                    } else {
                        comunaSelect.innerHTML = '<option value="">No hay comunas disponibles</option>';
                    }
                })
                .catch(err => {
                    console.error('Error al cargar comunas:', err);
                    comunaSelect.innerHTML = '<option value="">Error al cargar comunas</option>';
                });
        };

        // Asignar evento change
        regionSelect.addEventListener('change', cargarComunas);

        // Cargar comunas si ya hay una región seleccionada (edición)
        if (regionSelect.value) {
            cargarComunas();
        }
    });
});