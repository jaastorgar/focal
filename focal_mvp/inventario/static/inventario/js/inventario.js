document.addEventListener('DOMContentLoaded', function () {
  setTimeout(function () {
    const mensajes = document.getElementById('mensajes');
    if (mensajes) {
      mensajes.style.transition = 'opacity 1s ease-out';
      mensajes.style.opacity = '0';
      setTimeout(() => mensajes.remove(), 1000);
    }
  }, 5000); // 5 segundos
});