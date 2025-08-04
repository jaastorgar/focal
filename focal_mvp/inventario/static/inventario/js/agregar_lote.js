document.addEventListener('DOMContentLoaded', function() {
    // Seleccionamos los elementos del DOM una sola vez
    const campoCodigoBarras = document.getElementById('id_codigo_barras');
    const campoNombreProducto = document.getElementById('id_nombre_producto');
    const campoOcultoProductoId = document.getElementById('id_producto_id'); // name="producto" en el HTML
    const campoCantidad = document.getElementById('id_cantidad');
    const form = document.getElementById('lote-form');

    // Salimos temprano si no encontramos el campo principal, evitando errores
    if (!campoCodigoBarras) {
        return;
    }

    // Ponemos el foco en el campo de código de barras para el escaneo inmediato
    campoCodigoBarras.focus();

    // El evento 'change' es ideal para escáneres porque se dispara después de que el valor cambia
    // y el campo pierde el foco (lo que simula la tecla "Enter" del escáner).
    campoCodigoBarras.addEventListener('change', function() {
        const codigo = this.value.trim(); // Añadido trim para limpiar espacios

        if (codigo) {
            // Construimos la URL de la API de forma dinámica
            const apiUrl = `/api/buscar-producto/${encodeURIComponent(codigo)}/`;

            fetch(apiUrl)
                .then(response => {
                    // Si la respuesta no es "ok" (ej. un error 404 o 500),
                    // leemos el mensaje de error del cuerpo de la respuesta y lo rechazamos
                    if (!response.ok) {
                        return response.json().then(err => Promise.reject(err));
                    }
                    // Si todo está bien, convertimos la respuesta a JSON
                    return response.json();
                })
                .then(data => {
                    // Si la API nos confirma que encontró el producto
                    if (data.encontrado) {
                        campoNombreProducto.value = data.nombre;
                        // ✅ CORREGIDO: Usar 'oferta_id' que es lo que devuelve la API
                        campoOcultoProductoId.value = data.oferta_id;
                        campoCantidad.focus();
                    }
                })
                .catch(error => {
                    // Este bloque se ejecuta si la promesa fue rechazada (producto no encontrado)
                    console.error('Error al buscar producto:', error.mensaje || 'Error de conexión');
                    alert(error.mensaje || '¡Producto no encontrado! Por favor, regístralo primero.');

                    // Limpiamos los campos para permitir un nuevo escaneo
                    limpiarCampos();
                    campoCodigoBarras.focus(); // Devolvemos el foco al campo de escaneo
                });
        }
    });

    // Función para limpiar campos
    function limpiarCampos() {
        campoCodigoBarras.value = '';
        campoNombreProducto.value = '';
        campoOcultoProductoId.value = '';
    }

    // Opcional: Escuchamos el evento de envío del formulario para dar feedback al usuario
    form.addEventListener('submit', function(e) {
        // Validar que se haya seleccionado un producto
        if (!campoOcultoProductoId.value || campoOcultoProductoId.value === 'undefined') {
            e.preventDefault();
            alert('Por favor, escanea un código de barras válido primero.');
            campoCodigoBarras.focus();
            return false;
        }

        // Deshabilitamos el botón de envío para prevenir clics múltiples mientras se procesa
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Guardando...';
        }
    });
});