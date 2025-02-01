// register.js

document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('register-form');
    if (!registerForm) {
        console.error('Formulário de registro não encontrado.');
        return;
    }

    registerForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const username = document.getElementById('username').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value.trim();
        const confirm_password = document.getElementById('confirm_password').value.trim();

        if (!username || !email || !password || !confirm_password) {
            Swal.fire({
                icon: 'warning',
                title: 'Campos Vazios',
                text: 'Por favor, preencha todos os campos.',
                confirmButtonText: 'Ok'
            });
            return;
        }

        if (password !== confirm_password) {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: 'As senhas não coincidem.',
                confirmButtonText: 'Ok'
            });
            return;
        }

        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content'),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, email, password, confirm_password })
            });
            const data = await response.json();

            if (response.ok) {
                Swal.fire({
                    icon: 'success',
                    title: 'Sucesso',
                    text: data.message,
                    confirmButtonText: 'Ok'
                }).then(() => {
                    window.location.href = '/login';
                });
            } else {
                let errorMsg = data.message || 'Erro ao registrar usuário.';
                if (data.errors) {
                    for (const [field, errors] of Object.entries(data.errors)) {
                        errorMsg += `\n${field}: ${errors.join(', ')}`;
                    }
                }
                Swal.fire({
                    icon: 'error',
                    title: 'Erro de Registro',
                    text: errorMsg,
                    confirmButtonText: 'Ok'
                });
            }
        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: 'Erro ao processar o registro. Tente novamente.',
                confirmButtonText: 'Ok'
            });
            console.error('Erro ao processar o registro:', error);
        }
    });
});
