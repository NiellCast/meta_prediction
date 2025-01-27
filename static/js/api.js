// app/static/js/api.js

/**
 * Exibe um toast do Bootstrap.
 * @param {string} message - A mensagem a ser exibida.
 * @param {string} type - O tipo de toast (success, danger, etc.).
 */
function showToast(message, type) {
    const toastContainer = document.getElementById('toastContainer');
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    toastContainer.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
    });
}

/**
 * Exibe um modal de confirmação usando o Bootstrap.
 * @param {string} message - A mensagem de confirmação.
 * @param {function} callback - A função a ser executada se o usuário confirmar.
 */
function showConfirmationModal(message, callback) {
    const modalBody = document.getElementById('confirmationModalBody');
    const confirmButton = document.getElementById('confirmActionBtn');
    modalBody.textContent = message;

    const modal = new bootstrap.Modal(document.getElementById('confirmationModal'));
    modal.show();

    // Remove qualquer evento anterior para evitar múltiplas chamadas
    confirmButton.replaceWith(confirmButton.cloneNode(true));
    const newConfirmButton = document.getElementById('confirmActionBtn');
    newConfirmButton.addEventListener('click', () => {
        modal.hide();
        callback();
    });
}

/**
 * Função para obter o token CSRF do meta tag
 */
function getCsrfToken() {
    const tokenMeta = document.querySelector('meta[name="csrf-token"]');
    return tokenMeta ? tokenMeta.getAttribute('content') : '';
}


# Melhorias aplicadas ao arquivo