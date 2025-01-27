// app/static/js/login.js

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(loginForm);

            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken() // Inclui o token CSRF no cabeçalho
                    },
                    body: formData
                });
                const result = await response.json();

                if (response.ok) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Sucesso',
                        text: result.message,
                        confirmButtonText: 'Ok'
                    }).then(() => {
                        window.location.href = '/banca';
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Erro',
                        text: result.message,
                        confirmButtonText: 'Ok'
                    });
                }
            } catch (error) {
                console.error('Erro ao fazer login:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Erro',
                    text: 'Erro ao fazer login. Tente novamente.',
                    confirmButtonText: 'Ok'
                });
            }
        });
    }
});

/**
 * Função para obter o token CSRF do meta tag
 */
function getCsrfToken() {
    const tokenMeta = document.querySelector('meta[name="csrf-token"]');
    return tokenMeta ? tokenMeta.getAttribute('content') : '';
}


# Melhorias aplicadas ao arquivo