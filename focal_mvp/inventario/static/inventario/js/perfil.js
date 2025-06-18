// Función para mostrar/ocultar las secciones
function toggleSection(sectionId) {
  const section = document.getElementById(sectionId);
  const sections = document.querySelectorAll('section');

  // Ocultar todas las secciones
  sections.forEach(sec => sec.style.display = 'none');

  // Mostrar la sección seleccionada
  if (section) {
    section.style.display = section.style.display === 'block' ? 'none' : 'block';
  }
}

// Opcional: Establecer la primera sección visible por defecto
document.addEventListener('DOMContentLoaded', () => {
  toggleSection('almacenero');
});