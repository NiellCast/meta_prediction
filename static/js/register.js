// app/static/js/register.js

document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(registerForm);

            try {
                const response = await fetch('/register', {
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
                    // Exibir erros de validação
                    let errorMsg = result.message;
                    if (result.errors) {
                        for (const [field, errors] of Object.entries(result.errors)) {
                            errorMsg += `\n${field}: ${errors.join(', ')}`;
                        }
                    }
                    Swal.fire({
                        icon: 'error',
                        title: 'Erro',
                        text: errorMsg,
                        confirmButtonText: 'Ok'
                    });
                }
            } catch (error) {
                console.error('Erro ao registrar usuário:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Erro',
                    text: 'Erro ao registrar usuário. Tente novamente.',
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
