// login.js

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    if (!loginForm) {
        console.error('Formulário de login não encontrado.');
        return;
    }

    loginForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value.trim();

        if (!username || !password) {
            Swal.fire({
                icon: 'warning',
                title: 'Campos Vazios',
                text: 'Por favor, preencha todos os campos.',
                confirmButtonText: 'Ok'
            });
            return;
        }

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content'),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            const data = await response.json();

            if (response.ok) {
                Swal.fire({
                    icon: 'success',
                    title: 'Bem-vindo!',
                    text: data.message,
                    confirmButtonText: 'Ok'
                }).then(() => {
                    window.location.href = '/banca';
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Erro de Login',
                    text: data.message || 'Credenciais inválidas.',
                    confirmButtonText: 'Ok'
                });
            }
        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: 'Erro ao processar o login. Tente novamente.',
                confirmButtonText: 'Ok'
            });
            console.error('Erro ao processar o login:', error);
        }
    });
});
