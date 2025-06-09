document.addEventListener("DOMContentLoaded", () => {
  const passwordInput = document.getElementById("id_almacenero-password");
  const confirmPasswordInput = document.getElementById("id_almacenero-confirm_password");

  if (!passwordInput || !confirmPasswordInput) return;

  // Validación en vivo
  const feedback = document.createElement("div");
  feedback.id = "password-feedback";
  feedback.style.marginTop = "8px";
  feedback.style.fontSize = "0.9rem";
  feedback.style.color = "#D32F2F";
  passwordInput.parentNode.appendChild(feedback);

  const passwordRequirements = {
    length: /.{8,12}/,
    uppercase: /[A-Z]/,
    lowercase: /[a-z]/,
    number: /[0-9]/,
    specialChar: /[^A-Za-z0-9]/
  };

  function renderFeedback(password) {
    const checks = {
      length: passwordRequirements.length.test(password),
      uppercase: passwordRequirements.uppercase.test(password),
      lowercase: passwordRequirements.lowercase.test(password),
      number: passwordRequirements.number.test(password),
      special: passwordRequirements.specialChar.test(password)
    };

    feedback.innerHTML = `
      <ul style="padding-left: 20px;">
        <li style="color:${checks.length ? 'green' : 'red'}">8 a 12 caracteres</li>
        <li style="color:${checks.uppercase ? 'green' : 'red'}">Al menos una mayúscula</li>
        <li style="color:${checks.lowercase ? 'green' : 'red'}">Al menos una minúscula</li>
        <li style="color:${checks.number ? 'green' : 'red'}">Al menos un número</li>
        <li style="color:${checks.special ? 'green' : 'red'}">Al menos un carácter especial</li>
      </ul>
    `;
  }

  passwordInput.addEventListener("input", () => {
    renderFeedback(passwordInput.value);
  });

  confirmPasswordInput.addEventListener("input", () => {
    if (confirmPasswordInput.value !== passwordInput.value) {
      confirmPasswordInput.setCustomValidity("Las contraseñas no coinciden");
    } else {
      confirmPasswordInput.setCustomValidity("");
    }
  });
});