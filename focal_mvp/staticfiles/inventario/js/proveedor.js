document.addEventListener('DOMContentLoaded', function () {
    const regionSelect = document.getElementById('id_region');
    const comunaSelect = document.getElementById('id_comuna');

    // Función para cargar las comunas según la región seleccionada
    function cargarComunas(region) {
        if (region === '') {
            comunaSelect.innerHTML = '<option value="">Primero seleccione una región</option>';
            return;
        }

        // Datos de REGIONES_COMUNAS (debes adaptarlo según tu estructura)
        const REGIONES_COMUNAS = {
            'Metropolitana': [
                { value: 'Santiago', label: 'Santiago' },
                { value: 'Vitacura', label: 'Vitacura' },
                { value: 'Providencia', label: 'Providencia' },
                // Agrega más comunas aquí...
            ],
            // Agrega más regiones aquí...
        };

        // Limpiar opciones existentes
        comunaSelect.innerHTML = '';

        // Agregar opción inicial
        comunaSelect.innerHTML += '<option value="">Seleccione una comuna</option>';

        // Llenar el select con las comunas de la región seleccionada
        const comunas = REGIONES_COMUNAS[region];
        if (comunas) {
            comunas.forEach(comuna => {
                comunaSelect.innerHTML += `<option value="${comuna.value}">${comuna.label}</option>`;
            });
        }
    }

    // Evento change para el campo de región
    regionSelect.addEventListener('change', function () {
        const selectedRegion = this.value;
        cargarComunas(selectedRegion);
    });

    // Cargar comunas inicialmente si hay una región preseleccionada
    cargarComunas(regionSelect.value);
});