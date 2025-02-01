// banca.js

document.addEventListener('DOMContentLoaded', () => {
    // Função para formatar números no padrão brasileiro (1.000,00)
    function formatNumberBR(value) {
        // Remove tudo que não é dígito ou vírgula
        let num = value.replace(/[^\d,]/g, '');

        if (num.length === 0) return '';

        // Remove vírgulas extras
        const parts = num.split(',');
        if (parts.length > 2) {
            num = parts[0] + ',' + parts.slice(1).join('');
        }

        // Remove zeros à esquerda
        num = num.replace(/^0+/, '');
        if (num.startsWith(',')) {
            num = '0' + num;
        }

        // Adiciona a vírgula antes dos últimos dois dígitos
        const commaIndex = num.lastIndexOf(',');
        if (commaIndex === -1) {
            if (num.length > 2) {
                num = num.slice(0, -2) + ',' + num.slice(-2);
            } else if (num.length === 1) {
                num = '0,0' + num;
            } else if (num.length === 2) {
                num = '0,' + num;
            }
        }

        // Adiciona pontos como separador de milhares
        let [integer, decimal] = num.split(',');
        integer = integer.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
        num = decimal ? integer + ',' + decimal : integer;

        return num;
    }

    // Função para remover formatação e retornar apenas números
    function unformatNumberBR(value) {
        return parseFloat(value.replace(/\./g, '').replace(',', '.')) || 0;
    }

    // Aplicar formatação enquanto o usuário digita
    const formattedInputs = document.querySelectorAll('.formatted-input');
    formattedInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            const cursorPosition = input.selectionStart;
            const originalLength = input.value.length;

            let formatted = formatNumberBR(input.value);
            input.value = formatted;

            const newLength = formatted.length;
            input.setSelectionRange(cursorPosition + (newLength - originalLength), cursorPosition + (newLength - originalLength));
        });
    });

    // Função para carregar Dados Gerais
    async function carregarDadosGerais() {
        try {
            const response = await fetch('/get_dados');
            if (response.ok) {
                const data = await response.json();
                document.getElementById('infoSaldo').textContent = data.total_banca.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                document.getElementById('infoDepositos').textContent = data.depositos.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                document.getElementById('infoLucro').textContent = data.lucro.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                document.getElementById('infoSaques').textContent = data.saques.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                document.getElementById('infoPorcentagem').textContent = `${data.porcentagem_ganho}%`;
                document.getElementById('infoMeta').textContent = data.meta.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Erro',
                    text: 'Erro ao carregar dados financeiros.',
                    confirmButtonText: 'Ok'
                });
            }
        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: 'Erro de conexão ao carregar dados financeiros.',
                confirmButtonText: 'Ok'
            });
            console.error('Erro ao carregar dados financeiros:', error);
        }
    }

    // Função para carregar Saldos
    async function carregarSaldos() {
        try {
            const response = await fetch('/get_saldos');
            if (response.ok) {
                const saldos = await response.json();
                const tbody = document.querySelector('#saldos-table tbody');
                tbody.innerHTML = '';

                if (saldos.length === 0) {
                    tbody.innerHTML = `<tr>
                        <td colspan="4" class="text-center py-4 text-gray-500">Nenhum saldo registrado.</td>
                    </tr>`;
                    return;
                }

                saldos.forEach(saldo => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td class="py-2 px-4 border-b">${saldo.id}</td>
                        <td class="py-2 px-4 border-b">${saldo.data}</td>
                        <td class="py-2 px-4 border-b">R$ ${saldo.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                        <td class="py-2 px-4 border-b space-x-2">
                            <button class="edit-saldo-button bg-color3 hover:bg-color4 text-white font-semibold py-1 px-3 rounded-md shadow-md">Editar</button>
                            <button class="delete-saldo-button bg-danger hover:bg-red-600 text-white font-semibold py-1 px-3 rounded-md shadow-md">Excluir</button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
                adicionarEventosSaldos();
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Erro',
                    text: 'Erro ao carregar saldos registrados.',
                    confirmButtonText: 'Ok'
                });
            }
        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: 'Erro de conexão ao carregar saldos registrados.',
                confirmButtonText: 'Ok'
            });
            console.error('Erro ao carregar saldos registrados:', error);
        }
    }

    // Função para carregar Transações
    async function carregarTransacoes() {
        try {
            const response = await fetch('/get_transacoes');
            if (response.ok) {
                const transacoes = await response.json();
                const tbody = document.querySelector('#transacoes-table tbody');
                tbody.innerHTML = '';

                if (transacoes.length === 0) {
                    tbody.innerHTML = `<tr>
                        <td colspan="5" class="text-center py-4 text-gray-500">Nenhuma transação registrada.</td>
                    </tr>`;
                    return;
                }

                transacoes.forEach(transacao => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td class="py-2 px-4 border-b">${transacao.id}</td>
                        <td class="py-2 px-4 border-b">${capitalizeFirstLetter(transacao.tipo)}</td>
                        <td class="py-2 px-4 border-b">R$ ${transacao.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                        <td class="py-2 px-4 border-b">${transacao.data}</td>
                        <td class="py-2 px-4 border-b space-x-2">
                            <button class="edit-transacao-button bg-color3 hover:bg-color4 text-white font-semibold py-1 px-3 rounded-md shadow-md">Editar</button>
                            <button class="delete-transacao-button bg-danger hover:bg-red-600 text-white font-semibold py-1 px-3 rounded-md shadow-md">Excluir</button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
                adicionarEventosTransacoes();
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Erro',
                    text: 'Erro ao carregar transações registradas.',
                    confirmButtonText: 'Ok'
                });
            }
        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: 'Erro de conexão ao carregar transações registradas.',
                confirmButtonText: 'Ok'
            });
            console.error('Erro ao carregar transações registradas:', error);
        }
    }

    // Função para capitalizar a primeira letra de uma string
    function capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }

    // Função para carregar Gráfico de Evolução
    let chartEvolucaoInstance;
    async function carregarGraficoEvolucao() {
        try {
            const response = await fetch('/get_evolucao');
            if (response.ok) {
                const evolucao = await response.json();
                const labels = evolucao.map(item => item.data);
                const bancaData = evolucao.map(item => parseFloat(item.banca.replace(/\./g, '').replace(',', '.')));
                const lucroData = evolucao.map(item => parseFloat(item.lucro.replace(/\./g, '').replace(',', '.')));
                const depositosData = evolucao.map(item => parseFloat(item.depositos.replace(/\./g, '').replace(',', '.')));
                const saquesData = evolucao.map(item => parseFloat(item.saques.replace(/\./g, '').replace(',', '.')));

                const ctx = document.getElementById('evolucao-chart').getContext('2d');
                if (chartEvolucaoInstance) {
                    chartEvolucaoInstance.destroy();
                }

                chartEvolucaoInstance = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: 'Banca',
                                data: bancaData,
                                borderColor: '#67b588', // color3
                                backgroundColor: 'rgba(103, 181, 136, 0.2)',
                                fill: true
                            },
                            {
                                label: 'Lucro',
                                data: lucroData,
                                borderColor: '#22c55e', // success
                                backgroundColor: 'rgba(34, 197, 94, 0.2)',
                                fill: true
                            },
                            {
                                label: 'Depósitos',
                                data: depositosData,
                                borderColor: '#65a675', // color4
                                backgroundColor: 'rgba(101, 166, 117, 0.2)',
                                fill: true
                            },
                            {
                                label: 'Saques',
                                data: saquesData,
                                borderColor: '#EF4444', // danger
                                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                                fill: true
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            tooltip: {
                                mode: 'index',
                                intersect: false,
                            },
                            legend: {
                                display: true,
                                position: 'top',
                            },
                            title: {
                                display: true,
                                text: 'Evolução da Banca'
                            }
                        },
                        interaction: {
                            mode: 'nearest',
                            axis: 'x',
                            intersect: false
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Valor (R$)'
                                }
                            },
                            x: {
                                title: {
                                    display: true,
                                    text: 'Data'
                                }
                            }
                        }
                    }
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Erro',
                    text: 'Erro ao carregar evolução dos dados.',
                    confirmButtonText: 'Ok'
                });
            }
        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: 'Erro de conexão ao carregar evolução dos dados.',
                confirmButtonText: 'Ok'
            });
            console.error('Erro ao carregar evolução dos dados:', error);
        }
    }

    // Função para carregar Previsão da IA
    async function carregarPrevisaoIA() {
        try {
            const response = await fetch('/get_previsao_ia');
            if (response.ok) {
                const data = await response.json();
                const previsaoHTML = `
                    <p><strong>Previsão para o próximo mês:</strong> R$ ${data.previsao.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                `;
                document.getElementById('previsao-ia').innerHTML = previsaoHTML;
            } else {
                document.getElementById('previsao-ia').innerHTML = `<p class="text-color5">Erro ao carregar previsão da IA.</p>`;
            }
        } catch (error) {
            document.getElementById('previsao-ia').innerHTML = `<p class="text-color5">Erro de conexão ao carregar previsão da IA.</p>`;
            console.error('Erro ao carregar previsão da IA:', error);
        }
    }

    // Carregar dados ao iniciar
    carregarDadosGerais();
    carregarSaldos();
    carregarTransacoes();
    carregarGraficoEvolucao();
    carregarPrevisaoIA();

    // Formulário para adicionar Saldo
    const addSaldoForm = document.getElementById('add-saldo-form');
    if (addSaldoForm) {
        addSaldoForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const saldoInput = document.getElementById('saldo');
            const dataSaldoInput = document.getElementById('data_saldo');
            const saldo = unformatNumberBR(saldoInput.value);
            const data_saldo = dataSaldoInput.value;

            if (isNaN(saldo) || saldo < 0) {
                Swal.fire({
                    icon: 'error',
                    title: 'Erro',
                    text: 'Por favor, insira um valor válido para o saldo.',
                    confirmButtonText: 'Ok'
                });
                return;
            }

            if (!data_saldo) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Data Ausente',
                    text: 'Por favor, selecione uma data para o saldo.',
                    confirmButtonText: 'Ok'
                });
                return;
            }

            try {
                const response = await fetch('/add_saldo', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content'),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ saldo, data_saldo })
                });
                const data = await response.json();

                if (response.ok) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Sucesso',
                        text: data.message,
                        confirmButtonText: 'Ok'
                    });
                    carregarDadosGerais();
                    carregarSaldos();
                    carregarTransacoes();
                    carregarGraficoEvolucao();
                    carregarPrevisaoIA();
                    saldoInput.value = '';
                    dataSaldoInput.value = '';
                } else {
                    let errorMsg = data.message || 'Erro ao adicionar saldo.';
                    if (data.errors) {
                        for (const [field, errors] of Object.entries(data.errors)) {
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
                Swal.fire({
                    icon: 'error',
                    title: 'Erro',
                    text: 'Erro ao adicionar saldo.',
                    confirmButtonText: 'Ok'
                });
                console.error('Erro ao adicionar saldo:', error);
            }
        });
    }

    // Formulário para adicionar Transação
    const addTransacaoForm = document.getElementById('add-transacao-form');
    if (addTransacaoForm) {
        addTransacaoForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const tipo = document.getElementById('tipo').value;
            const valorInput = document.getElementById('valor');
            const dataTransacaoInput = document.getElementById('data_transacao');
            const valor = unformatNumberBR(valorInput.value);
            const data_transacao = dataTransacaoInput.value;

            if (!tipo) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Tipo não selecionado',
                    text: 'Por favor, selecione o tipo da transação.',
                    confirmButtonText: 'Ok'
                });
                return;
            }

            if (isNaN(valor) || valor <= 0) {
                Swal.fire({
                    icon: 'error',
                    title: 'Erro',
                    text: 'Por favor, insira um valor válido para a transação.',
                    confirmButtonText: 'Ok'
                });
                return;
            }

            if (!data_transacao) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Data Ausente',
                    text: 'Por favor, selecione uma data para a transação.',
                    confirmButtonText: 'Ok'
                });
                return;
            }

            try {
                const response = await fetch('/add_transacao', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content'),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ tipo, valor, data_transacao })
                });
                const data = await response.json();

                if (response.ok) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Sucesso',
                        text: data.message,
                        confirmButtonText: 'Ok'
                    });
                    carregarDadosGerais();
                    carregarSaldos();
                    carregarTransacoes();
                    carregarGraficoEvolucao();
                    carregarPrevisaoIA();
                    valorInput.value = '';
                    dataTransacaoInput.value = '';
                    document.getElementById('tipo').selectedIndex = 0;
                } else {
                    let errorMsg = data.message || 'Erro ao adicionar transação.';
                    if (data.errors) {
                        for (const [field, errors] of Object.entries(data.errors)) {
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
                Swal.fire({
                    icon: 'error',
                    title: 'Erro',
                    text: 'Erro ao adicionar transação.',
                    confirmButtonText: 'Ok'
                });
                console.error('Erro ao adicionar transação:', error);
            }
        });
    }

    // Formulário para atualizar Meta
    const updateMetaForm = document.getElementById('update-meta-form');
    if (updateMetaForm) {
        updateMetaForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const novaMetaInput = document.getElementById('nova_meta');
            const nova_meta = unformatNumberBR(novaMetaInput.value);

            if (isNaN(nova_meta) || nova_meta <= 0) {
                Swal.fire({
                    icon: 'error',
                    title: 'Erro',
                    text: 'Por favor, insira um valor válido para a meta.',
                    confirmButtonText: 'Ok'
                });
                return;
            }

            try {
                const response = await fetch('/update_meta', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content'),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ nova_meta })
                });
                const data = await response.json();

                if (response.ok) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Sucesso',
                        text: data.message,
                        confirmButtonText: 'Ok'
                    });
                    carregarDadosGerais();
                    carregarGraficoEvolucao();
                    carregarPrevisaoIA();
                    novaMetaInput.value = '';
                } else {
                    let errorMsg = data.message || 'Erro ao atualizar meta.';
                    if (data.errors) {
                        for (const [field, errors] of Object.entries(data.errors)) {
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
                Swal.fire({
                    icon: 'error',
                    title: 'Erro',
                    text: 'Erro ao atualizar meta.',
                    confirmButtonText: 'Ok'
                });
                console.error('Erro ao atualizar meta:', error);
            }
        });
    }

    // Botão para zerar banca
    const zerarBancaButton = document.getElementById('zerar-banca-button');
    if (zerarBancaButton) {
        zerarBancaButton.addEventListener('click', async function () {
            const result = await Swal.fire({
                title: 'Tem certeza?',
                text: "Isso excluirá todos os saldos e transações.",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#e72313', // color1
                cancelButtonColor: '#3b82f6', // info
                confirmButtonText: 'Sim, zerar!',
                cancelButtonText: 'Cancelar'
            });

            if (result.isConfirmed) {
                try {
                    const response = await fetch('/delete_all_saldos', {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content'),
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({})
                    });
                    const data = await response.json();

                    if (response.ok) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Sucesso',
                            text: data.message,
                            confirmButtonText: 'Ok'
                        });
                        carregarDadosGerais();
                        carregarSaldos();
                        carregarTransacoes();
                        carregarGraficoEvolucao();
                        carregarPrevisaoIA();
                    } else {
                        Swal.fire({
                            icon: 'error',
                            title: 'Erro',
                            text: data.message || 'Erro ao zerar a banca.',
                            confirmButtonText: 'Ok'
                        });
                    }
                } catch (error) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Erro',
                        text: 'Erro ao zerar a banca. Tente novamente.',
                        confirmButtonText: 'Ok'
                    });
                    console.error('Erro ao zerar a banca:', error);
                }
            }
        });
    }

    // Funções para adicionar eventos aos botões de editar e deletar Saldo
    function adicionarEventosSaldos() {
        // Botões de editar saldo
        document.querySelectorAll('.edit-saldo-button').forEach(button => {
            button.addEventListener('click', async function () {
                const row = this.closest('tr');
                const saldoId = row.children[0].textContent;
                const saldoValor = row.children[2].textContent.replace('R$ ', '').replace(/\./g, '').replace(',', '.');
                const saldoData = row.children[1].textContent.split('/').reverse().join('-'); // Convertendo para YYYY-MM-DD

                const { value: novaTransacao } = await Swal.fire({
                    title: 'Editar Saldo',
                    html: `
                        <input type="text" id="swal-novo-valor" class="swal2-input" placeholder="Valor (Ex: 1.500,00)" value="${parseFloat(saldoValor).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}">
                        <input type="date" id="swal-nova-data" class="swal2-input" value="${saldoData}">
                    `,
                    focusConfirm: false,
                    showCancelButton: true,
                    preConfirm: () => {
                        const novoValor = document.getElementById('swal-novo-valor').value;
                        const novaData = document.getElementById('swal-nova-data').value;
                        if (!novoValor || !novaData) {
                            Swal.showValidationMessage('Por favor, preencha todos os campos.');
                            return false;
                        }
                        return { novo_valor: novoValor, nova_data: novaData };
                    }
                });

                if (novaTransacao) {
                    const valorDesformatado = unformatNumberBR(novaTransacao.novo_valor);
                    const nova_data = novaTransacao.nova_data;
                    try {
                        const response = await fetch(`/update_saldo/${saldoId}`, {
                            method: 'POST',
                            headers: {
                                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content'),
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ novo_valor: valorDesformatado, nova_data })
                        });
                        const data = await response.json();

                        if (response.ok) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Sucesso',
                                text: data.message,
                                confirmButtonText: 'Ok'
                            });
                            carregarDadosGerais();
                            carregarSaldos();
                            carregarTransacoes();
                            carregarGraficoEvolucao();
                            carregarPrevisaoIA();
                        } else {
                            Swal.fire({
                                icon: 'error',
                                title: 'Erro',
                                text: data.message || 'Erro ao atualizar saldo.',
                                confirmButtonText: 'Ok'
                            });
                        }
                    } catch (error) {
                        Swal.fire({
                            icon: 'error',
                            title: 'Erro',
                            text: 'Erro ao atualizar saldo. Tente novamente.',
                            confirmButtonText: 'Ok'
                        });
                        console.error('Erro ao atualizar saldo:', error);
                    }
                }
            });
        });

        // Botões de excluir saldo
        document.querySelectorAll('.delete-saldo-button').forEach(button => {
            button.addEventListener('click', async function () {
                const row = this.closest('tr');
                const saldoId = row.children[0].textContent;

                const result = await Swal.fire({
                    title: 'Tem certeza?',
                    text: "Deseja excluir este saldo?",
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#e72313', // color1
                    cancelButtonColor: '#3b82f6', // info
                    confirmButtonText: 'Sim, excluir!',
                    cancelButtonText: 'Cancelar'
                });

                if (result.isConfirmed) {
                    try {
                        const response = await fetch(`/delete_saldo/${saldoId}`, {
                            method: 'DELETE',
                            headers: {
                                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content'),
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({})
                        });
                        const data = await response.json();

                        if (response.ok) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Sucesso',
                                text: data.message,
                                confirmButtonText: 'Ok'
                            });
                            carregarDadosGerais();
                            carregarSaldos();
                            carregarTransacoes();
                            carregarGraficoEvolucao();
                            carregarPrevisaoIA();
                        } else {
                            Swal.fire({
                                icon: 'error',
                                title: 'Erro',
                                text: data.message || 'Erro ao excluir saldo.',
                                confirmButtonText: 'Ok'
                            });
                        }
                    } catch (error) {
                        Swal.fire({
                            icon: 'error',
                            title: 'Erro',
                            text: 'Erro ao excluir saldo. Tente novamente.',
                            confirmButtonText: 'Ok'
                        });
                        console.error('Erro ao excluir saldo:', error);
                    }
                }
            });
        });
    }

    // Funções para adicionar eventos aos botões de editar e deletar Transação
    function adicionarEventosTransacoes() {
        // Botões de editar transação
        document.querySelectorAll('.edit-transacao-button').forEach(button => {
            button.addEventListener('click', async function () {
                const row = this.closest('tr');
                const transacaoId = row.children[0].textContent;
                const transacaoValor = row.children[2].textContent.replace('R$ ', '').replace(/\./g, '').replace(',', '.');
                const transacaoTipo = row.children[1].textContent.toLowerCase();
                const transacaoData = row.children[3].textContent.split('/').reverse().join('-'); // Convertendo para YYYY-MM-DD

                const { value: novaTransacao } = await Swal.fire({
                    title: 'Editar Transação',
                    html: `
                        <input type="text" id="swal-novo-valor" class="swal2-input" placeholder="Valor (Ex: 300,00)" value="${parseFloat(transacaoValor).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}">
                        <select id="swal-novo-tipo" class="swal2-input">
                            <option value="deposito" ${transacaoTipo === 'deposito' ? 'selected' : ''}>Depósito</option>
                            <option value="saque" ${transacaoTipo === 'saque' ? 'selected' : ''}>Saque</option>
                        </select>
                        <input type="date" id="swal-nova-data" class="swal2-input" value="${transacaoData}">
                    `,
                    focusConfirm: false,
                    showCancelButton: true,
                    preConfirm: () => {
                        const novoValor = document.getElementById('swal-novo-valor').value;
                        const novoTipo = document.getElementById('swal-novo-tipo').value;
                        const novaData = document.getElementById('swal-nova-data').value;
                        if (!novoValor || !novoTipo || !novaData) {
                            Swal.showValidationMessage('Por favor, preencha todos os campos.');
                            return false;
                        }
                        return { novo_valor: novoValor, novo_tipo: novoTipo, nova_data: novaData };
                    }
                });

                if (novaTransacao) {
                    const valorDesformatado = unformatNumberBR(novaTransacao.novo_valor);
                    const novo_tipo = novaTransacao.novo_tipo;
                    const nova_data = novaTransacao.nova_data;
                    try {
                        const response = await fetch(`/update_transacao/${transacaoId}`, {
                            method: 'POST',
                            headers: {
                                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content'),
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ novo_valor: valorDesformatado, novo_tipo, nova_data })
                        });
                        const data = await response.json();

                        if (response.ok) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Sucesso',
                                text: data.message,
                                confirmButtonText: 'Ok'
                            });
                            carregarDadosGerais();
                            carregarSaldos();
                            carregarTransacoes();
                            carregarGraficoEvolucao();
                            carregarPrevisaoIA();
                        } else {
                            Swal.fire({
                                icon: 'error',
                                title: 'Erro',
                                text: data.message || 'Erro ao atualizar transação.',
                                confirmButtonText: 'Ok'
                            });
                        }
                    } catch (error) {
                        Swal.fire({
                            icon: 'error',
                            title: 'Erro',
                            text: 'Erro ao atualizar transação. Tente novamente.',
                            confirmButtonText: 'Ok'
                        });
                        console.error('Erro ao atualizar transação:', error);
                    }
                }
            });
        });

        // Botões de excluir transação
        document.querySelectorAll('.delete-transacao-button').forEach(button => {
            button.addEventListener('click', async function () {
                const row = this.closest('tr');
                const transacaoId = row.children[0].textContent;

                const result = await Swal.fire({
                    title: 'Tem certeza?',
                    text: "Deseja excluir esta transação?",
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#e72313', // color1
                    cancelButtonColor: '#3b82f6', // info
                    confirmButtonText: 'Sim, excluir!',
                    cancelButtonText: 'Cancelar'
                });

                if (result.isConfirmed) {
                    try {
                        const response = await fetch(`/delete_transacao/${transacaoId}`, {
                            method: 'DELETE',
                            headers: {
                                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content'),
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({})
                        });
                        const data = await response.json();

                        if (response.ok) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Sucesso',
                                text: data.message,
                                confirmButtonText: 'Ok'
                            });
                            carregarDadosGerais();
                            carregarSaldos();
                            carregarTransacoes();
                            carregarGraficoEvolucao();
                            carregarPrevisaoIA();
                        } else {
                            Swal.fire({
                                icon: 'error',
                                title: 'Erro',
                                text: data.message || 'Erro ao excluir transação.',
                                confirmButtonText: 'Ok'
                            });
                        }
                    } catch (error) {
                        Swal.fire({
                            icon: 'error',
                            title: 'Erro',
                            text: 'Erro ao excluir transação. Tente novamente.',
                            confirmButtonText: 'Ok'
                        });
                        console.error('Erro ao excluir transação:', error);
                    }
                }
            });
        });
    }

    // Capitaliza a primeira letra de uma string
    function capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }
});
