document.addEventListener('DOMContentLoaded', function () {
    const skuInput = document.getElementById('id_sku');
    const cantidadInput = document.getElementById('id_cantidad');
    const form = document.getElementById('descontar-form');

    // Funcionalidad para lector de código de barras
    skuInput.addEventListener('change', function() {
        // Simular Enter después de escanear
        if (this.value.trim() !== '') {
            cantidadInput.focus();
        }
    });

    cantidadInput.addEventListener('change', function() {
        // Simular Enter después de ingresar cantidad
        if (this.value.trim() !== '' && skuInput.value.trim() !== '') {
            form.submit();
        }
    });
});