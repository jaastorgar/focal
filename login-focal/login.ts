const form = document.getElementById('login-form') as HTMLFormElement;
const message = document.getElementById('message') as HTMLParagraphElement;

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const email = (document.getElementById('email') as HTMLInputElement).value;
  const password = (document.getElementById('password') as HTMLInputElement).value;

  try {
    const response = await fetch('http://localhost:3000/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (response.ok) {
      message.textContent = `Bienvenido, ${data.user.nombre}`;
      localStorage.setItem('token', data.token); // Guardar token si se desea
    } else {
      message.textContent = data.message;
    }
  } catch (error) {
    console.error('Error en login:', error);
    message.textContent = 'Error de conexión con el servidor';
  }
});