document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('sku-search-form');
    const skuInput = document.getElementById('id_sku_busqueda');
    const validationMessage = document.getElementById('sku-validation-message');

    // Validar el formato del SKU antes de enviar el formulario
    form.addEventListener('submit', function (event) {
        const sku = skuInput.value.trim();
        if (!/^\d+$/.test(sku)) {
            event.preventDefault(); // Evitar el envío del formulario
            validationMessage.textContent = 'El SKU debe ser un número válido.';
            validationMessage.style.color = 'red';
        } else {
            validationMessage.textContent = ''; // Limpiar mensajes de error
        }
    });
});