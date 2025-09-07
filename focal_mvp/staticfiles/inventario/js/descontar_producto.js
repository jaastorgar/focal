document.addEventListener('DOMContentLoaded', function () {
    const skuInput = document.getElementById('id_sku');
    const cantidadInput = document.getElementById('id_cantidad');
    const form = document.getElementById('descontar-form');
    const submitButton = form.querySelector('button[type="submit"]');

    // Verificar que todos los elementos necesarios existan
    if (!skuInput || !cantidadInput || !form || !submitButton) {
        console.warn("Algunos elementos del formulario de descontar producto no fueron encontrados.");
        return;
    }

    // --- FUNCIONALIDAD PARA LECTOR DE CÓDIGO DE BARRAS ---
    skuInput.addEventListener('change', function() {
        const sku = this.value.trim();
        
        // === CAMBIO: Solo mover el foco, no simular Enter ===
        if (sku !== '') {
            // Limpiar mensajes de validación anteriores si los hay
            const validationMessage = document.getElementById('codigo-barras-validation');
            if (validationMessage) {
                validationMessage.textContent = '';
                validationMessage.className = 'validation-message';
            }
            
            // Mover el foco al campo de cantidad
            cantidadInput.focus();
        }
        // ===================================================
    });

    skuInput.addEventListener('input', function() {
        const sku = this.value.trim();
        const validationMessage = document.getElementById('codigo-barras-validation');
        
        if (validationMessage) {
            if (sku === '') {
                validationMessage.textContent = '';
                validationMessage.className = 'validation-message';
            } else {
                // Aquí podrías hacer una llamada AJAX para verificar el SKU
                // y mostrar si es válido o no
                validationMessage.textContent = 'SKU escaneado. Ahora ingresa la cantidad.';
                validationMessage.className = 'validation-message info';
            }
        }
    });

    // --- MANEJO DEL ENVÍO DEL FORMULARIO ---
    form.addEventListener('submit', function(e) {
        const sku = skuInput.value.trim();
        const cantidad = cantidadInput.value.trim();

        // Validación básica antes de enviar
        if (!sku) {
            e.preventDefault();
            alert('Por favor, escanea o ingresa un código de barras (SKU).');
            skuInput.focus();
            return false;
        }

        if (!cantidad || isNaN(cantidad) || parseInt(cantidad) <= 0) {
            e.preventDefault();
            alert('Por favor, ingresa una cantidad válida (número entero positivo).');
            cantidadInput.focus();
            return false;
        }

        // Deshabilitar botón para prevenir envíos múltiples
        submitButton.disabled = true;
        submitButton.textContent = 'Procesando...';
    });
});