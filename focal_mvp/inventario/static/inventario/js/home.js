// static/inventario/js/home.js
// Flujo solicitado:
// 1) Al entrar: Navbar muestra SOLO "Menú" (sin nombre).
// 2) En el contenido aparece "Bienvenido, {Nombre}".
// 3) A los 5s se oculta el mensaje y el NOMBRE aparece ARRIBA de “Menú” en el navbar.

(function () {
  const WELCOME_TIMEOUT_MS = 5000;

  document.addEventListener("DOMContentLoaded", () => {
    // --------- 1) Obtener nombre de varias fuentes seguras ---------
    const fallback = "";
    const nameDoc = (document.documentElement.dataset.username || "").trim();
    const nameBody = (document.body.dataset.username || "").trim();
    const nameMeta = (document.querySelector('meta[name="app-username"]')?.content || "").trim();
    const globalName = (window.APP_USER && window.APP_USER.name) ? String(window.APP_USER.name).trim() : "";

    const username = nameDoc || nameBody || nameMeta || globalName || fallback;

    // --------- 2) Ganchos del DOM ---------
    const banner = document.getElementById("welcome-banner");
    const bannerText = document.getElementById("welcome-text");
    const navMenuLabel = document.getElementById("nav-menu-label"); // Debe decir "Menú"
    const navUsername = document.getElementById("nav-username");     // Aquí aparecerá el nombre

    if (!navMenuLabel || !navUsername) return; // si falta estructura, no romper

    // Estado inicial del navbar: sólo “Menú”
    navMenuLabel.textContent = "Menú";
    navUsername.textContent = "";
    navUsername.style.opacity = "0";
    navUsername.style.transition = "opacity 280ms ease";

    // --------- 3) Mostrar Bienvenida (si hay nombre y hay banner) ---------
    if (banner && bannerText && username) {
      // Preparar transición
      banner.style.opacity = "0";
      banner.style.transform = "translateY(-6px)";
      banner.style.transition = "opacity 300ms ease, transform 300ms ease";

      bannerText.textContent = `Bienvenido, ${username}`;

      // Fade in inicial
      requestAnimationFrame(() => {
        banner.style.opacity = "1";
        banner.style.transform = "translateY(0)";
      });

      // Tras 5s: ocultar banner y subir el nombre al navbar
      setTimeout(() => {
        // Fade out del banner
        const hideBanner = () => {
          banner.style.display = "none";
          banner.removeEventListener("transitionend", hideBanner);
        };
        banner.addEventListener("transitionend", hideBanner);
        banner.style.opacity = "0";
        banner.style.transform = "translateY(-6px)";

        // Mostrar nombre en navbar con fade in
        navUsername.textContent = username;
        requestAnimationFrame(() => {
          navUsername.style.opacity = "1";
        });
      }, WELCOME_TIMEOUT_MS);

    } else {
      // Sin banner o sin username: mostrar directo arriba del Menú
      if (username) {
        navUsername.textContent = username;
        navUsername.style.opacity = "1";
      }
      if (banner) banner.style.display = "none";
    }
  });
})();