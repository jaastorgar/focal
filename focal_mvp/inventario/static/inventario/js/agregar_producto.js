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

    // --- Validación en vivo: solo dígitos, máx 30, sin espacios ---
    campoSku.addEventListener('input', function() {
        const original = this.value;
        // Limpia espacios y no-dígitos
        const soloDigitos = original.replace(/\D+/g, '');
        if (soloDigitos !== original) {
            this.value = soloDigitos;
        }

        // Enforce máx 30
        if (this.value.length > 30) {
            this.value = this.value.slice(0, 30);
        }

        // Mensajes dinámicos
        resetValidationState();

        if (this.value.length === 0) {
            // limpio y dejo al form/required decidir si está vacío
            return;
        }
        if (!/^\d+$/.test(this.value)) {
            updateValidationMessage('El SKU debe contener solo números.', 'error');
            submitButton.disabled = true;
            return;
        }
        if (this.value.length > 30) {
            updateValidationMessage('Máximo 30 dígitos.', 'error');
            submitButton.disabled = true;
            return;
        }

        // OK localmente -> no deshabilito
        updateValidationMessage('', '');
        submitButton.disabled = false;
    });

    // --- Lógica Principal al Cambiar el SKU (consulta a API) ---
    campoSku.addEventListener('change', function() {
        const sku = this.value.trim();
        resetValidationState();
        resetProductFields();

        if (!sku) return;

        // Si ya falla localmente, no llamo a la API
        if (!/^\d+$/.test(sku) || sku.length > 30) {
            updateValidationMessage('SKU inválido (solo números, máx 30, sin espacios).', 'error');
            submitButton.disabled = true;
            return;
        }

        fetch(`/api/obtener-datos-sku/${sku}/`)
            .then(response => response.json().then(data => ({ ok: response.ok, status: response.status, data })))
            .then(({ ok, status, data }) => {
                if (!ok) {
                    throw new Error(data?.mensaje || `Error de red (${status})`);
                }
                handleApiResponse(data);
            })
            .catch(error => handleApiError(error));
    });

    // --- Antes de enviar, una última poda defensiva ---
    form.addEventListener('submit', function(e) {
        const trimmed = campoSku.value.trim();
        campoSku.value = trimmed.replace(/\D+/g, '').slice(0, 30);

        if (!campoSku.value || !/^\d+$/.test(campoSku.value) || campoSku.value.length > 30) {
            e.preventDefault();
            updateValidationMessage('SKU inválido (solo números, máx 30, sin espacios).', 'error');
            submitButton.disabled = true;
        }
    });

    // --- Funciones Auxiliares ---
    function updateValidationMessage(message, status) {
        validationMessage.textContent = message || '';
        validationMessage.className = `validation-message${status ? ' ' + status : ''}`;
    }

    function handleApiResponse(data) {
        if (data.status === 'invalido') {
            updateValidationMessage(data.mensaje || 'SKU inválido.', 'error');
            campoSku.classList.add('input-error');
            submitButton.disabled = true;

        } else if (data.status === 'duplicado_local') {
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
        console.error(error);
    }

    function autoFillProductData(productoData) {
        if (!productoData) return;
        document.getElementById('id_nombre') && (document.getElementById('id_nombre').value = productoData.nombre || '');
        document.getElementById('id_marca') && (document.getElementById('id_marca').value = productoData.marca || '');
        document.getElementById('id_categoria') && (document.getElementById('id_categoria').value = productoData.categoria || '');
        // Mantengo la clave 'dramage' que envía la API para compatibilidad,
        // pero si existe id_gramage lo completo allí.
        const gram = productoData.dramage || productoData.gramage || '';
        const gramageEl = document.getElementById('id_gramage') || document.getElementById('id_dramage');
        if (gramageEl) gramageEl.value = gram;
        document.getElementById('id_unidad_medida') && (document.getElementById('id_unidad_medida').value = productoData.unidad_medida || '');
    }

    function resetProductFields() {
        const fieldsToReset = ['nombre', 'marca', 'categoria', 'gramage', 'dramage', 'unidad_medida'];
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