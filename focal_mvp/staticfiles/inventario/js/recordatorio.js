/* ==========================================================================
   Asistente FOCAL – Hover/tap: anima GIF y muestra frases en un globo
   ========================================================================== */
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('assistantBtn');
  const img = document.getElementById('assistantImg');
  const bubble = document.getElementById('assistantBubble');
  if (!btn || !img || !bubble) return;

  const idleSrc = btn.dataset.idleSrc; // PNG estático
  const gifSrc  = btn.dataset.gifSrc;  // GIF animado

  // Pre-carga el GIF para que no “parpadee” al primer hover
  const pre = new Image();
  pre.src = gifSrc;

  const PHRASES = ['¡Hola! ¿Te ayudo?', '¡Soy tu asistente!'];
  let phraseIndex = 0;
  let cycleTimer = null;
  let hideTimer = null;
  let active = false; // para móviles (toggle con tap)

  function setImageAnimated(animated) {
    img.src = animated ? gifSrc : idleSrc;
  }

  function showBubbleOnce() {
    bubble.textContent = PHRASES[phraseIndex];
    phraseIndex = (phraseIndex + 1) % PHRASES.length;

    btn.classList.add('show-bubble');
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => {
      btn.classList.remove('show-bubble');
    }, 2400);
  }

  function startCycle() {
    setImageAnimated(true);
    showBubbleOnce();
    clearInterval(cycleTimer);
    cycleTimer = setInterval(showBubbleOnce, 3000);
  }

  function stopCycle() {
    clearInterval(cycleTimer);
    clearTimeout(hideTimer);
    btn.classList.remove('show-bubble');
    setImageAnimated(false);
  }

  // Desktop: hover/focus
  btn.addEventListener('mouseenter', () => {
    active = true;
    startCycle();
  });
  btn.addEventListener('focus', () => {
    active = true;
    startCycle();
  });

  btn.addEventListener('mouseleave', () => {
    active = false;
    stopCycle();
  });
  btn.addEventListener('blur', () => {
    active = false;
    stopCycle();
  });

  // Móvil: tocar para iniciar/detener
  btn.addEventListener('click', (e) => {
    // Evita que el botón cause scroll al top en alguna implementación
    e.preventDefault();
    active = !active;
    if (active) startCycle();
    else stopCycle();
  });
});