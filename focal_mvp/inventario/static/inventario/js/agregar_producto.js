document.addEventListener('DOMContentLoaded', function() {
    // --- Selección de Elementos del DOM ---
    const form = document.getElementById('producto-form');
    const campoSku = document.getElementById('id_sku'); 
    const validationMessage = document.getElementById('codigo-barras-validation');
    const submitButton = document.getElementById('submit-button');

    if (!form || !campoSku || !validationMessage || !submitButton) {
        return;
    }

    campoSku.focus();

    // --- Lógica Principal al Cambiar el SKU ---
    campoSku.addEventListener('change', function() {
        const sku = this.value.trim();
        resetValidationState();
        resetProductFields();

        if (sku) {
            fetch(`/api/obtener-datos-sku/${sku}/`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Error de red: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    handleApiResponse(data);
                })
                .catch(error => handleApiError(error));
        }
    });

    // --- Funciones Auxiliares ---

    function updateValidationMessage(message, status) {
        validationMessage.textContent = message;
        validationMessage.className = `validation-message ${status}`;
    }

    function handleApiResponse(data) {
        if (data.status === 'duplicado_local') {
            updateValidationMessage(data.mensaje, 'error');
            campoSku.classList.add('input-error');
            submitButton.disabled = true;

        } else if (data.status === 'encontrado_global') {
            updateValidationMessage('Producto encontrado. Datos pre-cargados.', 'success');
            autoFillProductData(data.datos);
            document.querySelector('[name="form-0-precio_compra"]')?.focus();

        } else if (data.status === 'nuevo') {
            updateValidationMessage('SKU disponible para un nuevo registro.', 'success');
            document.getElementById('id_nombre').focus();
        }
    }

    function handleApiError(error) {
        updateValidationMessage('Error al verificar. Inténtalo de nuevo.', 'error');
        submitButton.disabled = true;
    }

    function autoFillProductData(productoData) {
        if (!productoData) {
            return;
        }
        document.getElementById('id_nombre').value = productoData.nombre || '';
        document.getElementById('id_marca').value = productoData.marca || '';
        document.getElementById('id_categoria').value = productoData.categoria || '';
        document.getElementById('id_dramage').value = productoData.dramage || '';
        document.getElementById('id_unidad_medida').value = productoData.unidad_medida || '';
    }

    function resetProductFields() {
        const fieldsToReset = ['nombre', 'marca', 'categoria', 'dramage', 'unidad_medida'];
        fieldsToReset.forEach(fieldName => {
            const field = document.getElementById(`id_${fieldName}`);
            if (field) field.value = '';
        });
        const precioCompra = document.querySelector('[name="form-0-precio_compra"]');
        const precioVenta = document.querySelector('[name="form-0-precio_venta"]');
        if (precioCompra) precioCompra.value = '';
        if (precioVenta) precioVenta.value = '';
    }

    function resetValidationState() {
        validationMessage.textContent = '';
        validationMessage.className = 'validation-message';
        campoSku.classList.remove('input-error');
        submitButton.disabled = false;
    }
});