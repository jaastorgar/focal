document.addEventListener('DOMContentLoaded', function () {
    // --- ELEMENTOS DEL DOM ---
    const inputSku = document.getElementById('id_sku_busqueda');
    const btnBuscar = document.getElementById('btn-buscar-sku');
    const divMensaje = document.getElementById('sku-validation-message');
    const seccionInfo = document.getElementById('producto-info-section');
    const seccionAcciones = document.getElementById('acciones-producto');
    const btnAsociar = document.getElementById('btn-asociar-producto');

    // Elementos de información del producto
    const infoNombre = document.getElementById('info-nombre');
    const infoSku = document.getElementById('info-sku');
    const infoMarca = document.getElementById('info-marca');
    const infoCategoria = document.getElementById('info-categoria');
    const infoDramage = document.getElementById('info-dramage');
    const infoUnidadMedida = document.getElementById('info-unidad-medida');

    // Variable para almacenar temporalmente los datos del producto encontrado
    let productoEncontradoData = null;

    if (!inputSku || !btnBuscar) {
        console.warn("Elementos de búsqueda de SKU no encontrados.");
        return;
    }

    // --- FUNCIONES AUXILIARES ---

    /**
     * Muestra un mensaje en la sección de validación.
     * @param {string} mensaje - El texto del mensaje.
     * @param {string} tipo - 'success', 'error', 'warning', etc. (para estilos CSS)
     */
    function mostrarMensaje(mensaje, tipo = 'info') {
        divMensaje.textContent = mensaje;
        divMensaje.className = `validation-message ${tipo}`;
        // Opcional: hacer scroll hacia el mensaje
        // divMensaje.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    /**
     * Limpia y oculta la sección de información del producto.
     */
    function limpiarInfoProducto() {
        infoNombre.textContent = '';
        infoSku.textContent = '';
        infoMarca.textContent = '';
        infoCategoria.textContent = '';
        infoDramage.textContent = '';
        infoUnidadMedida.textContent = '';
        seccionInfo.style.display = 'none';
        seccionAcciones.style.display = 'none';
        productoEncontradoData = null;
    }

    /**
     * Rellena la sección de información del producto con los datos recibidos.
     * @param {Object} datos - Objeto con las propiedades del producto.
     */
    function mostrarInfoProducto(datos) {
        infoNombre.textContent = datos.nombre || 'N/A';
        infoSku.textContent = datos.sku || 'N/A';
        infoMarca.textContent = datos.marca || 'N/A';
        // Para categoría, asumimos que el backend envía el valor "humano"
        infoCategoria.textContent = datos.categoria_mostrable || datos.categoria || 'N/A'; 
        infoDramage.textContent = datos.dramage || 'N/A';
        // Para unidad_medida, asumimos que el backend envía el valor "humano"
        infoUnidadMedida.textContent = datos.unidad_medida_mostrable || datos.unidad_medida || 'N/A';

        seccionInfo.style.display = 'block';
        // La sección de acciones se mostrará u ocultará según el estado en la respuesta
    }

    // --- LÓGICA PRINCIPAL ---

    /**
     * Realiza la llamada AJAX para buscar el producto por SKU.
     * @param {string} sku - El código SKU a buscar.
     */
    async function buscarProductoPorSku(sku) {
        if (!sku) {
            mostrarMensaje('Por favor, ingresa un SKU.', 'error');
            return;
        }

        mostrarMensaje('Buscando...', 'info');
        limpiarInfoProducto(); // Limpiar info anterior

        try {
            const response = await fetch(`/api/obtener-datos-sku/${encodeURIComponent(sku)}/`);
            
            if (!response.ok) {
                if (response.status === 404) {
                    mostrarMensaje('Producto no encontrado globalmente.', 'error');
                } else {
                    const errorData = await response.json();
                    mostrarMensaje(errorData.mensaje || 'Error al buscar el producto.', 'error');
                }
                return;
            }

            const data = await response.json();

            if (data.status === 'duplicado_local') {
                // El producto ya está en el inventario de esta empresa
                mostrarMensaje(data.mensaje, 'warning');
                // Opcional: podrías redirigir directamente al detalle
                // window.location.href = `/inventario/${data.producto_id}/detalle/`; 
                
            } else if (data.status === 'encontrado_global') {
                // Producto encontrado globalmente, pero no en esta empresa
                mostrarMensaje('Producto encontrado. Puedes asociarlo a tu inventario.', 'success');
                productoEncontradoData = data.datos; // Guardar datos
                mostrarInfoProducto(data.datos);
                
                // Mostrar botón para asociar
                seccionAcciones.style.display = 'block';
                // Configurar el enlace del botón de asociar
                // (Asumimos una URL de asociación, ajusta según tu backend)
                btnAsociar.href = `/inventario/asociar-producto/?sku=${encodeURIComponent(data.datos.sku)}`;
                
            } else if (data.status === 'nuevo') {
                // Producto completamente nuevo
                mostrarMensaje('Este es un producto nuevo. Puedes registrarlo.', 'info');
                // Aquí podrías abrir un modal para crearlo o redirigir
                // Por ahora, solo mostramos un mensaje.
            } else {
                mostrarMensaje('Respuesta inesperada del servidor.', 'error');
            }

        } catch (error) {
            console.error('Error en la búsqueda de SKU:', error);
            mostrarMensaje('Error de conexión. Inténtalo de nuevo.', 'error');
        }
    }

    // --- EVENTOS ---

    // Evento click del botón buscar
    btnBuscar.addEventListener('click', function () {
        const sku = inputSku.value.trim();
        buscarProductoPorSku(sku);
    });

    // Evento "Enter" en el input de SKU
    inputSku.addEventListener('keypress', function (event) {
        if (event.key === 'Enter') {
            event.preventDefault(); // Evitar submit de formulario si lo hubiera
            const sku = inputSku.value.trim();
            buscarProductoPorSku(sku);
        }
    });

});