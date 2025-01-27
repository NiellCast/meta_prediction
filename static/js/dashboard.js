// app/static/js/dashboard.js

document.addEventListener('DOMContentLoaded', () => {
    // Carrega dados iniciais
    carregarDados();
    carregarSaldos();
    carregarTransacoes();
    carregarEvolucao(); // Se implementar gráficos

    // Associa eventos aos formulários
    const metaForm = document.getElementById('metaForm');
    if (metaForm) {
        metaForm.addEventListener('submit', atualizarMeta);
    }

    const transacaoForm = document.getElementById('transacaoForm');
    if (transacaoForm) {
        transacaoForm.addEventListener('submit', adicionarTransacao);
    }

    const saldoForm = document.getElementById('saldoForm');
    if (saldoForm) {
        saldoForm.addEventListener('submit', salvarSaldoDoDia);
    }

    // Botão "Zerar Banca"
    const zerarBancaBtn = document.getElementById('zerarBancaBtn');
    if (zerarBancaBtn) {
        zerarBancaBtn.addEventListener('click', zerarBanca);
    }

    // Botão "Logout"
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
});

/**
 * Logout do usuário.
 */
async function logout() {
    try {
        const resp = await fetch('/logout', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken() // Inclui o token CSRF no cabeçalho
            }
        });
        const result = await resp.json();
        if (resp.ok) {
            Swal.fire({
                icon: 'success',
                title: 'Sucesso',
                text: result.message,
                confirmButtonText: 'Ok'
            }).then(() => {
                window.location.href = '/login';
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: 'Erro ao efetuar logout.',
                confirmButtonText: 'Ok'
            });
        }
    } catch (error) {
        console.error('Erro no logout:', error);
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: 'Erro ao efetuar logout.',
            confirmButtonText: 'Ok'
        });
    }
}

/**
 * Atualiza a meta.
 */
async function atualizarMeta(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);

    // Validação no frontend
    const novaMeta = formData.get('nova_meta').replace(',', '.');
    if (isNaN(novaMeta) || parseFloat(novaMeta) <= 0) {
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: 'Por favor, insira um valor válido para a meta.',
            confirmButtonText: 'Ok'
        });
        return;
    }

    try {
        const resp = await fetch('/update_meta', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken() // Inclui o token CSRF no cabeçalho
            },
            body: formData
        });

        const result = await resp.json();

        if (resp.ok) {
            Swal.fire({
                icon: 'success',
                title: 'Sucesso',
                text: 'Meta atualizada com sucesso!',
                confirmButtonText: 'Ok'
            });
            // Atualiza a exibição da meta
            const metaSpan = document.getElementById('metaValor');
            if (metaSpan) {
                metaSpan.textContent = result.meta;
            }
            carregarDados();
            form.reset();
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: result.message || 'Erro ao atualizar meta.',
                confirmButtonText: 'Ok'
            });
        }
    } catch (error) {
        console.error('Erro ao atualizar meta:', error);
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: 'Erro ao atualizar meta. Tente novamente.',
            confirmButtonText: 'Ok'
        });
    }
}

/**
 * Adiciona uma transação.
 */
async function adicionarTransacao(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);

    // Validação no frontend
    const valor = formData.get('valor').replace(',', '.');
    if (isNaN(valor) || parseFloat(valor) <= 0) {
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: 'Por favor, insira um valor válido para a transação.',
            confirmButtonText: 'Ok'
        });
        return;
    }

    try {
        const resp = await fetch('/add_transacao', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken() // Inclui o token CSRF no cabeçalho
            },
            body: formData
        });

        const result = await resp.json();

        if (resp.ok) {
            Swal.fire({
                icon: 'success',
                title: 'Sucesso',
                text: result.message,
                confirmButtonText: 'Ok'
            });
            carregarDados();
            carregarTransacoes();
            form.reset();
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: result.message || 'Erro ao adicionar transação.',
                confirmButtonText: 'Ok'
            });
        }
    } catch (error) {
        console.error('Erro ao adicionar transação:', error);
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: 'Erro ao adicionar transação. Tente novamente.',
            confirmButtonText: 'Ok'
        });
    }
}

/**
 * Salva o saldo do dia.
 */
async function salvarSaldoDoDia(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);

    // Validação no frontend
    const saldo = formData.get('saldo').replace(',', '.');
    if (isNaN(saldo) || parseFloat(saldo) < 0) { // Permitido saldo zero
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: 'Por favor, insira um valor válido para o saldo.',
            confirmButtonText: 'Ok'
        });
        return;
    }

    try {
        const resp = await fetch('/add_saldo', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken() // Inclui o token CSRF no cabeçalho
            },
            body: formData
        });

        const result = await resp.json();

        if (resp.ok) {
            Swal.fire({
                icon: 'success',
                title: 'Sucesso',
                text: result.message,
                confirmButtonText: 'Ok'
            });
            carregarDados();
            carregarSaldos();
            form.reset();
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: result.message || 'Erro ao salvar saldo do dia.',
                confirmButtonText: 'Ok'
            });
        }
    } catch (error) {
        console.error('Erro ao salvar saldo do dia:', error);
        Swal.fire({
            icon: 'error',
            title: 'Erro',
            text: 'Erro ao salvar saldo do dia. Tente novamente.',
            confirmButtonText: 'Ok'
        });
    }
}

/**
 * Zera a banca.
 */
async function zerarBanca() {
    const result = await Swal.fire({
        title: 'Tem certeza?',
        text: "Isso excluirá todos os saldos e transações.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sim, zerar!',
        cancelButtonText: 'Cancelar'
    });

    if (result.isConfirmed) {
        try {
            const resp = await fetch('/delete_all_saldos', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken() // Inclui o token CSRF no cabeçalho
                }
            });

            const resData = await resp.json();

            if (resp.ok) {
                Swal.fire({
                    icon: 'success',
                    title: 'Sucesso',
                    text: resData.message,
                    confirmButtonText: 'Ok'
                });
                carregarDados();
                carregarSaldos();
                carregarTransacoes();
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Erro',
                    text: resData.message || 'Erro ao zerar a banca.',
                    confirmButtonText: 'Ok'
                });
            }
        } catch (error) {
            console.error('Erro ao zerar a banca:', error);
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: 'Erro ao zerar a banca. Tente novamente.',
                confirmButtonText: 'Ok'
            });
        }
    }
}

/**
 * Carrega os dados gerais (saldo total, depósitos, saques, lucro).
 */
async function carregarDados() {
    try {
        const resp = await fetch('/get_dados');
        if (resp.ok) {
            const data = await resp.json();
            document.getElementById('infoTotalBanca').textContent = data.total_banca;
            document.getElementById('infoDepositos').textContent = data.depositos;
            document.getElementById('infoLucro').textContent = data.lucro;
            document.getElementById('infoSaques').textContent = data.saques;
            // Atualizar a meta atual
            const metaSpan = document.getElementById('metaValor');
            if (metaSpan && data.meta) {
                metaSpan.textContent = data.meta;
            }
        } else {
            showToast('Erro ao carregar dados financeiros.', 'danger');
        }
    } catch (error) {
        showToast('Erro de conexão ao carregar dados financeiros.', 'danger');
        console.error(error);
    }
}

/**
 * Carrega os saldos registrados e preenche a tabela.
 */
async function carregarSaldos() {
    try {
        const resp = await fetch('/get_saldos');
        if (resp.ok) {
            const saldos = await resp.json();
            const tb = document.getElementById('bancasTableBody');
            tb.innerHTML = '';
            saldos.forEach(s => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${s.data}</td>
                    <td>R$ ${s.valor.toFixed(2)}</td>
                    <td>
                        <button class="delete-saldo-btn btn btn-danger btn-sm" data-id="${s.id}">Excluir</button>
                        <button class="edit-saldo-btn btn btn-secondary btn-sm" data-id="${s.id}">Editar</button>
                    </td>
                `;
                tb.appendChild(row);
            });
            adicionarEventosSaldos();
        } else {
            showToast('Erro ao carregar saldos registrados.', 'danger');
        }
    } catch (error) {
        showToast('Erro de conexão ao carregar saldos registrados.', 'danger');
        console.error(error);
    }
}

/**
 * Adiciona eventos aos botões de excluir e editar saldos.
 */
function adicionarEventosSaldos() {
    // Botões de excluir saldo
    document.querySelectorAll('.delete-saldo-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const id = button.dataset.id;
            const confirmResult = await Swal.fire({
                title: 'Tem certeza?',
                text: "Deseja excluir este saldo?",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Sim, excluir!',
                cancelButtonText: 'Cancelar'
            });

            if (confirmResult.isConfirmed) {
                try {
                    const resp = await fetch(`/delete_saldo/${id}`, {
                        method: 'DELETE',
                        headers: {
                            'X-CSRFToken': getCsrfToken() // Inclui o token CSRF no cabeçalho
                        }
                    });

                    const resData = await resp.json();

                    if (resp.ok) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Sucesso',
                            text: resData.message,
                            confirmButtonText: 'Ok'
                        });
                        carregarDados();
                        carregarSaldos();
                    } else {
                        Swal.fire({
                            icon: 'error',
                            title: 'Erro',
                            text: resData.message || 'Erro ao excluir saldo.',
                            confirmButtonText: 'Ok'
                        });
                    }
                } catch (error) {
                    console.error('Erro ao excluir saldo:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Erro',
                        text: 'Erro ao excluir saldo. Tente novamente.',
                        confirmButtonText: 'Ok'
                    });
                }
            }
        });
    });

    // Botões de editar saldo
    document.querySelectorAll('.edit-saldo-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const id = button.dataset.id;
            const { value: novoValor } = await Swal.fire({
                title: 'Editar Saldo',
                input: 'text',
                inputLabel: 'Digite o novo valor (R$):',
                inputPlaceholder: 'Ex: 1500,00',
                showCancelButton: true,
                inputValidator: (value) => {
                    if (!value) {
                        return 'Você precisa digitar um valor!';
                    }
                    const valorNum = parseFloat(value.replace(',', '.'));
                    if (isNaN(valorNum) || valorNum < 0) { // Permitido saldo zero
                        return 'Valor inválido. Insira um número maior ou igual a zero.';
                    }
                }
            });

            if (novoValor !== undefined) {
                const formData = new FormData();
                formData.append('novo_valor', novoValor.replace(',', '.'));

                try {
                    const resp = await fetch(`/update_saldo/${id}`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCsrfToken() // Inclui o token CSRF no cabeçalho
                        },
                        body: formData
                    });

                    const resData = await resp.json();

                    if (resp.ok) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Sucesso',
                            text: resData.message,
                            confirmButtonText: 'Ok'
                        });
                        carregarDados();
                        carregarSaldos();
                    } else {
                        Swal.fire({
                            icon: 'error',
                            title: 'Erro',
                            text: resData.message || 'Erro ao atualizar saldo.',
                            confirmButtonText: 'Ok'
                        });
                    }
                } catch (error) {
                    console.error('Erro ao atualizar saldo:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Erro',
                        text: 'Erro ao atualizar saldo. Tente novamente.',
                        confirmButtonText: 'Ok'
                    });
                }
            }
        });
    });
}

/**
 * Carrega as transações e preenche a tabela.
 */
async function carregarTransacoes() {
    try {
        const resp = await fetch('/get_transacoes');
        if (resp.ok) {
            const transacoes = await resp.json();
            const tbody = document.getElementById('transacoesTableBody');
            tbody.innerHTML = '';

            transacoes.forEach(transacao => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${transacao.id}</td>
                    <td>${transacao.tipo.charAt(0).toUpperCase() + transacao.tipo.slice(1)}</td>
                    <td>R$ ${transacao.valor.toFixed(2)}</td>
                    <td>${transacao.data}</td>
                    <td>
                        <button class="delete-transacao-btn btn btn-danger btn-sm" data-id="${transacao.id}">Excluir</button>
                        <button class="edit-transacao-btn btn btn-secondary btn-sm" data-id="${transacao.id}">Editar</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });

            adicionarEventosTransacoes();
        } else {
            showToast('Erro ao carregar transações registradas.', 'danger');
        }
    } catch (error) {
        showToast('Erro de conexão ao carregar transações registradas.', 'danger');
        console.error(error);
    }
}

/**
 * Adiciona eventos aos botões de excluir e editar transações.
 */
function adicionarEventosTransacoes() {
    // Botões de excluir transação
    document.querySelectorAll('.delete-transacao-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const id = button.dataset.id;
            const confirmResult = await Swal.fire({
                title: 'Tem certeza?',
                text: "Deseja excluir esta transação?",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Sim, excluir!',
                cancelButtonText: 'Cancelar'
            });

            if (confirmResult.isConfirmed) {
                try {
                    const resp = await fetch(`/delete_transacao/${id}`, {
                        method: 'DELETE',
                        headers: {
                            'X-CSRFToken': getCsrfToken() // Inclui o token CSRF no cabeçalho
                        }
                    });

                    const resData = await resp.json();

                    if (resp.ok) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Sucesso',
                            text: resData.message,
                            confirmButtonText: 'Ok'
                        });
                        carregarDados();
                        carregarTransacoes();
                    } else {
                        Swal.fire({
                            icon: 'error',
                            title: 'Erro',
                            text: resData.message || 'Erro ao excluir transação.',
                            confirmButtonText: 'Ok'
                        });
                    }
                } catch (error) {
                    console.error('Erro ao excluir transação:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Erro',
                        text: 'Erro ao excluir transação. Tente novamente.',
                        confirmButtonText: 'Ok'
                    });
                }
            }
        });
    });

    // Botões de editar transação
    document.querySelectorAll('.edit-transacao-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const id = button.dataset.id;
            const { value: novoValor } = await Swal.fire({
                title: 'Editar Transação',
                input: 'text',
                inputLabel: 'Digite o novo valor (R$):',
                inputPlaceholder: 'Ex: 300,00',
                showCancelButton: true,
                inputValidator: (value) => {
                    if (!value) {
                        return 'Você precisa digitar um valor!';
                    }
                    const valorNum = parseFloat(value.replace(',', '.'));
                    if (isNaN(valorNum) || valorNum <= 0) {
                        return 'Valor inválido. Insira um número maior que zero.';
                    }
                }
            });

            if (novoValor) {
                const formData = new FormData();
                formData.append('novo_valor', novoValor.replace(',', '.'));

                try {
                    const resp = await fetch(`/update_transacao/${id}`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCsrfToken() // Inclui o token CSRF no cabeçalho
                        },
                        body: formData
                    });

                    const resData = await resp.json();

                    if (resp.ok) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Sucesso',
                            text: resData.message,
                            confirmButtonText: 'Ok'
                        });
                        carregarDados();
                        carregarTransacoes();
                    } else {
                        Swal.fire({
                            icon: 'error',
                            title: 'Erro',
                            text: resData.message || 'Erro ao atualizar transação.',
                            confirmButtonText: 'Ok'
                        });
                    }
                } catch (error) {
                    console.error('Erro ao atualizar transação:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Erro',
                        text: 'Erro ao atualizar transação. Tente novamente.',
                        confirmButtonText: 'Ok'
                    });
                }
            }
        });
    });
}

/**
 * Carrega a evolução da banca e plota o gráfico.
 */
async function carregarEvolucao() {
    try {
        const resp = await fetch('/get_evolucao');
        if (resp.ok) {
            const evolucao = await resp.json();
            const labels = evolucao.map(item => item.data);
            const bancaData = evolucao.map(item => parseFloat(item.banca.replace(".", "").replace(",", ".")));
            const lucroData = evolucao.map(item => parseFloat(item.lucro.replace(".", "").replace(",", ".")));
            const depositosData = evolucao.map(item => parseFloat(item.depositos.replace(".", "").replace(",", ".")));
            const saquesData = evolucao.map(item => parseFloat(item.saques.replace(".", "").replace(",", ".")));

            if (window.chartEvolucao) {
                window.chartEvolucao.destroy();
            }

            const ctx = document.getElementById('evolucaoChart').getContext('2d');
            window.chartEvolucao = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Banca',
                            data: bancaData,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            fill: false
                        },
                        {
                            label: 'Lucro',
                            data: lucroData,
                            borderColor: 'rgba(255, 99, 132, 1)',
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            fill: false
                        },
                        {
                            label: 'Depósitos',
                            data: depositosData,
                            borderColor: 'rgba(54, 162, 235, 1)',
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            fill: false
                        },
                        {
                            label: 'Saques',
                            data: saquesData,
                            borderColor: 'rgba(255, 206, 86, 1)',
                            backgroundColor: 'rgba(255, 206, 86, 0.2)',
                            fill: false
                        }
                    ]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        } else {
            showToast('Erro ao carregar evolução dos dados.', 'danger');
        }
    } catch (error) {
        showToast('Erro de conexão ao carregar evolução dos dados.', 'danger');
        console.error(error);
    }
}


# Melhorias aplicadas ao arquivo