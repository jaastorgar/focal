document.addEventListener('DOMContentLoaded', () => {
    function validarRunRut(runRut) {
        let valor = runRut.replace(/\./g, '').replace(/-/g, '').toUpperCase().trim();

        if (valor.length < 2) return false;

        const cuerpo = valor.slice(0, -1);
        const dv = valor.slice(-1);

        if (!/^\d+$/.test(cuerpo)) return false;

        let suma = 0;
        let multiplo = 2;

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

        return dv === dvCalculado;
    }

    const passwordInput = document.querySelector('[id$="password1"]'); 
    const confirmInput = document.querySelector('[id$="password2"]');  
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
    }

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

    document.querySelectorAll('select[data-region-target]').forEach(regionSelect => {
        const formPrefix = regionSelect.dataset.regionTarget;

        const comunaSelect = document.querySelector(`select[data-comuna-target="${formPrefix}"]`);

        if (!comunaSelect) {
            console.warn(`Select de comuna no encontrado para el target: ${formPrefix}`);
            return;
        }

        const cargarComunas = () => {
            const region = regionSelect.value;

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

        regionSelect.addEventListener('change', cargarComunas);

        if (regionSelect.value) {
            cargarComunas();
        }
    });

    const alertas = document.querySelectorAll('.alert');

    if (alertas.length > 0) {
        alertas.forEach(alerta => {
            if (alerta.classList.contains('alert-success') || 
                alerta.classList.contains('alert-info') || 
                alerta.classList.contains('alert-warning')) {
                
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
});