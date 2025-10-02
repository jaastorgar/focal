// static/inventario/js/home.js
// 1) Banner "Bienvenido, {Nombre}" y luego sube el nombre al navbar.
// 2) Dropdown accesible (click, fuera, Esc).
// 3) Asistente: imagen estática → GIF al hover/focus + globito con mensajes.

(function () {
  const WELCOME_TIMEOUT_MS = 3000;
  const ASSISTANT_INITIAL_DELAY = 100;  // delay inicial antes de mostrar mensajes (100ms)
  const ASSISTANT_BUBBLE_TIME_1 = 5000; // tiempo del primer mensaje (5 segundos)
  const ASSISTANT_BUBBLE_GAP   = 500;  // pausa de transición entre mensajes (3 segundos)
  const ASSISTANT_BUBBLE_TIME_2 = 1; // tiempo que dura visible el segundo mensaje (5 segundos)
  const ASSISTANT_FINAL_DELAY  = 1;  // tiempo adicional al final antes de ocultar (3 segundos)

  function getUsername() {
    const a = (document.documentElement.dataset.username || "").trim();
    const b = (document.body.dataset.username || "").trim();
    const c = (document.querySelector('meta[name="app-username"]')?.content || "").trim();
    const d = (window.APP_USER && window.APP_USER.name) ? String(window.APP_USER.name).trim() : "";
    return a || b || c || d || "";
  }

  /* --------------------------- Bienvenida / Navbar --------------------------- */
  function setupWelcome(username) {
    const banner = document.getElementById("welcome-banner");
    const bannerText = document.getElementById("welcome-text");
    const navUsername = document.getElementById("nav-username");
    const navMenuLabel = document.getElementById("nav-menu-label");

    if (!navUsername || !navMenuLabel) return;

    navMenuLabel.textContent = "Menú";
    navUsername.textContent = "";
    navUsername.style.opacity = "0";
    navUsername.style.transition = "opacity 280ms ease";

    if (banner && bannerText && username) {
      bannerText.textContent = `Bienvenido, ${username}`;
      banner.style.opacity = "0";
      banner.style.transform = "translateY(-6px)";
      banner.style.transition = "opacity 300ms ease, transform 300ms ease";
      requestAnimationFrame(() => {
        banner.style.opacity = "1";
        banner.style.transform = "translateY(0)";
      });

      setTimeout(() => {
        const end = () => {
          banner.style.display = "none";
          banner.removeEventListener("transitionend", end);
        };
        banner.addEventListener("transitionend", end);
        banner.style.opacity = "0";
        banner.style.transform = "translateY(-6px)";

        navUsername.textContent = username;
        requestAnimationFrame(() => { navUsername.style.opacity = "1"; });
      }, WELCOME_TIMEOUT_MS);
    } else {
      if (username) {
        navUsername.textContent = username;
        navUsername.style.opacity = "1";
      }
      if (banner) banner.style.display = "none";
    }
  }

  /* -------------------------------- Dropdown -------------------------------- */
  function setupDropdown() {
    const trigger  = document.getElementById("nav-menu-label");
    const block    = document.getElementById("navUserBlock");
    const dropdown = document.getElementById("nav-dropdown");
    if (!trigger || !block || !dropdown) return;

    const open  = () => { block.classList.add("open");  trigger.setAttribute("aria-expanded", "true");  };
    const close = () => { block.classList.remove("open");trigger.setAttribute("aria-expanded", "false"); };

    trigger.addEventListener("click", (e) => { e.stopPropagation(); block.classList.contains("open") ? close() : open(); });
    document.addEventListener("click", (e) => { if (!block.contains(e.target)) close(); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });

    trigger.addEventListener("keydown", (e) => {
      if ((e.key === "Enter" || e.key === " ") && !block.classList.contains("open")) {
        e.preventDefault(); open();
        const firstItem = dropdown.querySelector('a,button,[tabindex]:not([tabindex="-1"])');
        firstItem?.focus();
      }
    });
  }

  /* ------------------------------ Asistente UI ------------------------------ */
  function setupAssistant() {
    const btn = document.getElementById("assistantBtn");
    const img = document.getElementById("assistantImg");
    const bubble = document.getElementById("assistantBubble");
    if (!btn || !img || !bubble) {
      console.warn('Asistente: No se encontraron todos los elementos necesarios');
      return;
    }

    const idleSrc = btn.dataset.idleSrc;
    const gifSrc  = btn.dataset.gifSrc;

    let timers = [];

    function clearTimers() {
      timers.forEach(t => clearTimeout(t));
      timers = [];
    }

    function showMessages() {
      console.log('Asistente: Esperando antes de mostrar mensajes');
      
      // Esperar el delay inicial antes de mostrar el primer mensaje
      timers.push(setTimeout(() => {
        console.log('Asistente: Mostrando primer mensaje');
        btn.classList.add("show-bubble");
        bubble.textContent = "Hola, ¿te ayudo?";
        
        // Cambiar al segundo mensaje después del tiempo del primer mensaje
        timers.push(setTimeout(() => {
          bubble.classList.add("fade-text");
          timers.push(setTimeout(() => {
            bubble.textContent = "¡Soy tu asistente!";
            bubble.classList.remove("fade-text");
          }, ASSISTANT_BUBBLE_GAP));
        }, ASSISTANT_BUBBLE_TIME_1));
        
        // Ocultar después de que el segundo mensaje haya estado visible + delay final
        timers.push(setTimeout(() => {
          hideBubble();
        }, ASSISTANT_BUBBLE_TIME_1 + ASSISTANT_BUBBLE_GAP + ASSISTANT_BUBBLE_TIME_2 + ASSISTANT_FINAL_DELAY));
      }, ASSISTANT_INITIAL_DELAY));
    }

    function hideBubble() {
      console.log('Asistente: Ocultando globo');
      btn.classList.remove("show-bubble");
      bubble.classList.remove("fade-text");
    }

    function toGif()  { 
      if (!img.src.includes(gifSrc)) {
        console.log('Asistente: Cambiando a GIF');
        img.src = gifSrc;
      }
    }
    function toIdle() { 
      if (!img.src.includes(idleSrc)) {
        console.log('Asistente: Cambiando a imagen estática');
        img.src = idleSrc;
      }
    }

    // Hover / Focus → GIF + mensajes
    const onEnter = () => { 
      console.log('Asistente: onEnter disparado');
      clearTimers(); 
      toGif(); 
      showMessages(); 
    };
    const onLeave = () => { 
      console.log('Asistente: onLeave disparado');
      clearTimers(); 
      hideBubble(); 
      toIdle(); 
    };

    btn.addEventListener("mouseenter", onEnter);
    btn.addEventListener("focus", onEnter);
    btn.addEventListener("mouseleave", onLeave);
    btn.addEventListener("blur", onLeave);

    console.log('Asistente: Event listeners registrados correctamente');

    // Acción principal del botón (si quieres abrir un panel)
    window.openAssistant = function () {
      // Aquí podrías abrir un modal/chat.
      // Por ahora sólo "reactivamos" animación y mensajes.
      onEnter();
    };
  }

  /* --------------------------------- Init ---------------------------------- */
  document.addEventListener("DOMContentLoaded", () => {
    console.log('Inicializando home.js');
    const username = getUsername();
    console.log('Username detectado:', username);
    setupWelcome(username);
    setupDropdown();
    setupAssistant();
  });
})();