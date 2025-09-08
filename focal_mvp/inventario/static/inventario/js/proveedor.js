// static/inventario/js/proveedor.js
// JS para formulario de Proveedor SIN región ni comuna.
// - Formatea/valida RUT (Chile).
// - Restringe teléfono a dígitos.
// - Valida nombre, email y rut si están presentes.
// - Evita doble envío.

(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    // Helpers
    const $ = (id) => document.getElementById(id);

    // Obtén el formulario de forma flexible
    const form =
      document.getElementById('proveedor-form') ||
      document.querySelector('form[action*="proveedor"]') ||
      document.querySelector('form');

    if (!form) return;

    const btnSubmit =
      form.querySelector('button[type="submit"]') ||
      form.querySelector('.btn-submit');

    // Campos comunes (si no existen, se ignoran)
    const inputNombre =
      $('id_nombre') || $('id_name') || form.querySelector('[name="nombre"]');
    const inputRut =
      $('id_rut') || form.querySelector('[name="rut"], [name="RUT"]');
    const inputEmail =
      $('id_email') || form.querySelector('input[type="email"]');
    const inputTelefono =
      $('id_telefono') ||
      $('id_telefono_contacto') ||
      form.querySelector('input[name*="fono"], input[name*="telefono"]');

    // ------ Utilidades de mensajes ------
    function ensureMsgEl(input) {
      if (!input) return null;
      let msg = input.nextElementSibling;
      if (!msg || !msg.classList || !msg.classList.contains('field-hint')) {
        msg = document.createElement('small');
        msg.className = 'field-hint';
        msg.style.display = 'block';
        msg.style.marginTop = '0.25rem';
        msg.style.fontSize = '.85rem';
        msg.style.color = '#B00020'; // rojo de error discreto
        input.insertAdjacentElement('afterend', msg);
      }
      return msg;
    }

    function setError(input, message) {
      if (!input) return;
      const msg = ensureMsgEl(input);
      if (msg) {
        msg.textContent = message || '';
        msg.style.visibility = message ? 'visible' : 'hidden';
      }
      input.classList.toggle('is-invalid', Boolean(message));
      input.setAttribute('aria-invalid', message ? 'true' : 'false');
    }

    // ------ RUT (formato y validación) ------
    function cleanRut(v) {
      return (v || '')
        .toString()
        .replace(/[.\s-]/g, '')
        .replace(/k$/, 'K')
        .toUpperCase();
    }

    function dvRut(numStr) {
      let M = 0,
        S = 1;
      for (; numStr; numStr = Math.floor(numStr / 10)) {
        S = (S + (numStr % 10) * (9 - (M++ % 6))) % 11;
      }
      return S ? String(S - 1) : 'K';
    }

    function formatRut(v) {
      v = cleanRut(v);
      if (v.length <= 1) return v;
      const cuerpo = v.slice(0, -1);
      const dv = v.slice(-1);
      // Agrega puntos cada 3
      const cuerpoFmt = cuerpo.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      return `${cuerpoFmt}-${dv}`;
    }

    function isValidRut(v) {
      v = cleanRut(v);
      if (v.length < 2) return false;
      const cuerpo = v.slice(0, -1);
      const dv = v.slice(-1);
      if (!/^\d+$/.test(cuerpo)) return false;
      return dvRut(Number(cuerpo)) === dv;
    }

    if (inputRut) {
      // Formateo en vivo
      inputRut.addEventListener('input', function () {
        const pos = this.selectionStart;
        const before = this.value;
        const formatted = formatRut(before);
        this.value = formatted;
        // Mantener posición cercana (simple estimación)
        const diff = formatted.length - before.length;
        this.setSelectionRange(pos + diff, pos + diff);
        // Limpia error mientras escribe
        setError(this, '');
      });

      inputRut.addEventListener('blur', function () {
        const v = this.value.trim();
        if (!v) {
          setError(this, 'El RUT es requerido.');
          return;
        }
        if (!isValidRut(v)) {
          setError(this, 'RUT inválido. Revisa dígito verificador.');
        } else {
          setError(this, '');
        }
      });
    }

    // ------ Teléfono: sólo dígitos + largo razonable ------
    if (inputTelefono) {
      inputTelefono.addEventListener('input', function () {
        const digits = this.value.replace(/\D+/g, '');
        this.value = digits.slice(0, 15);
        setError(this, '');
      });
    }

    // ------ Email: validación básica ------
    function looksLikeEmail(v) {
      return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v);
    }
    if (inputEmail) {
      inputEmail.addEventListener('input', function () {
        setError(this, '');
      });
      inputEmail.addEventListener('blur', function () {
        const v = this.value.trim();
        if (v && !looksLikeEmail(v)) {
          setError(this, 'Ingresa un correo válido.');
        }
      });
    }

    // ------ Nombre: requerido ------
    if (inputNombre) {
      inputNombre.addEventListener('input', function () {
        setError(this, '');
      });
    }

    // ------ Envío: validaciones + anti doble click ------
    form.addEventListener('submit', function (e) {
      let firstInvalid = null;

      if (inputNombre && inputNombre.value.trim().length < 2) {
        setError(inputNombre, 'El nombre es requerido.');
        firstInvalid = firstInvalid || inputNombre;
      }

      if (inputRut) {
        const v = inputRut.value.trim();
        if (!v) {
          setError(inputRut, 'El RUT es requerido.');
          firstInvalid = firstInvalid || inputRut;
        } else if (!isValidRut(v)) {
          setError(inputRut, 'RUT inválido. Revisa dígito verificador.');
          firstInvalid = firstInvalid || inputRut;
        }
      }

      if (inputEmail && inputEmail.value.trim() && !looksLikeEmail(inputEmail.value.trim())) {
        setError(inputEmail, 'Ingresa un correo válido.');
        firstInvalid = firstInvalid || inputEmail;
      }

      if (inputTelefono && inputTelefono.value && inputTelefono.value.length < 6) {
        setError(inputTelefono, 'Teléfono muy corto.');
        firstInvalid = firstInvalid || inputTelefono;
      }

      if (firstInvalid) {
        e.preventDefault();
        firstInvalid.focus();
        return;
      }

      // Anti doble envío
      if (btnSubmit) {
        btnSubmit.disabled = true;
        btnSubmit.dataset.originalText = btnSubmit.textContent;
        btnSubmit.textContent = 'Guardando…';
      }
    });

    // Rehabilitar botón si el navegador vuelve del cache
    window.addEventListener('pageshow', function (evt) {
      if (evt.persisted && btnSubmit) {
        btnSubmit.disabled = false;
        if (btnSubmit.dataset.originalText) {
          btnSubmit.textContent = btnSubmit.dataset.originalText;
        }
      }
    });
  });
})();