document.addEventListener('DOMContentLoaded', function () {
    // Obtener elementos del DOM
    const tipoObligacionSelect = document.getElementById('id_tipo_obligacion');
    const periodicidadGroup = document.getElementById('id_periodicidad').closest('.form-group');
    const diaMesGroup = document.getElementById('id_dia_mes').closest('.form-group');
    const mesAnioGroup = document.getElementById('id_mes_anio').closest('.form-group');

    // Función para mostrar/ocultar campos condicionales
    function toggleCamposCondicionales() {
        const valor = tipoObligacionSelect.value;
        if (valor === 'fija' || valor === 'variable') {
            periodicidadGroup.classList.add('mostrar');
            diaMesGroup.classList.add('mostrar');
            mesAnioGroup.classList.add('mostrar');
        } else {
            periodicidadGroup.classList.remove('mostrar');
            diaMesGroup.classList.remove('mostrar');
            mesAnioGroup.classList.remove('mostrar');
        }
    }

    // Escuchar cambios en el select de tipo de obligación
    tipoObligacionSelect.addEventListener('change', toggleCamposCondicionales);

    // Llamar al inicio para establecer el estado correcto
    toggleCamposCondicionales();

    // Validación del formulario antes de enviar
    const form = document.getElementById('recordatorio-form');
    if (form) {
        form.addEventListener('submit', function (e) {
            // Evitar envío si hay errores
            e.preventDefault();

            // Limpiar mensajes de error previos
            const errorMessages = document.querySelectorAll('.error-message');
            errorMessages.forEach(msg => msg.remove());

            let isValid = true;

            // Validar campo "tipo_obligacion"
            const tipoObligacion = tipoObligacionSelect.value;
            if (!tipoObligacion) {
                showError(tipoObligacionSelect, 'Por favor, seleccione un tipo de obligación.');
                isValid = false;
            }

            // Validar campo "periodicidad" si es necesario
            if (tipoObligacion === 'fija' || tipoObligacion === 'variable') {
                const periodicidad = document.getElementById('id_periodicidad').value;
                if (!periodicidad) {
                    showError(document.getElementById('id_periodicidad'), 'Por favor, seleccione una periodicidad.');
                    isValid = false;
                }
            }

            // Validar campo "dia_mes" si es necesario
            if (tipoObligacion === 'fija' || tipoObligacion === 'variable') {
                const diaMes = document.getElementById('id_dia_mes').value;
                if (diaMes && (diaMes < 1 || diaMes > 31)) {
                    showError(document.getElementById('id_dia_mes'), 'El día del mes debe estar entre 1 y 31.');
                    isValid = false;
                }
            }

            // Validar campo "mes_anio" si es necesario
            if (tipoObligacion === 'fija' || tipoObligacion === 'variable') {
                const mesAnio = document.getElementById('id_mes_anio').value;
                if (mesAnio && (mesAnio < 1 || mesAnio > 12)) {
                    showError(document.getElementById('id_mes_anio'), 'El mes del año debe estar entre 1 y 12.');
                    isValid = false;
                }
            }

            // Validar campo "fecha_primera_ejecucion"
            const fechaPrimeraEjecucion = document.getElementById('id_fecha_primera_ejecucion').value;
            if (!fechaPrimeraEjecucion) {
                showError(document.getElementById('id_fecha_primera_ejecucion'), 'Por favor, ingrese la fecha de primera ejecución.');
                isValid = false;
            }

            // Validar campo "proxima_fecha_ejecucion"
            const proximaFechaEjecucion = document.getElementById('id_proxima_fecha_ejecucion').value;
            if (!proximaFechaEjecucion) {
                showError(document.getElementById('id_proxima_fecha_ejecucion'), 'Por favor, ingrese la próxima fecha de ejecución.');
                isValid = false;
            }

            // Validar campo "dias_anticipacion_alerta"
            const diasAnticipacionAlerta = document.getElementById('id_dias_anticipacion_alerta').value;
            if (!diasAnticipacionAlerta) {
                showError(document.getElementById('id_dias_anticipacion_alerta'), 'Por favor, ingrese los días de anticipación para la alerta.');
                isValid = false;
            }

            // Si todo es válido, enviar el formulario
            if (isValid) {
                form.submit(); // Enviar el formulario normalmente
            }
        });
    }

    // Función auxiliar para mostrar mensajes de error
    function showError(field, message) {
        const errorDiv = document.createElement('small');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }
});