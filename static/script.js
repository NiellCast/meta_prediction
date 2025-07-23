// static/script.js

console.log("Script carregado.");

document.addEventListener('DOMContentLoaded', () => {
  // Funcionalidade de validação de data para saldo diário
  const dateInput = document.getElementById('add-balance-date');
  const addForm  = document.getElementById('form-add-balance');
  const addBtn   = addForm && addForm.querySelector('button[type="submit"]');
  const msgDiv   = document.getElementById('daily-exists-msg');

  if (dateInput && addBtn && msgDiv) {
    dateInput.addEventListener('change', () => {
      fetch(`/check_daily?date=${dateInput.value}`)
        .then(res => res.json())
        .then(data => {
          if (data.exists) {
            addBtn.disabled = true;
            msgDiv.style.display = 'block';
            msgDiv.textContent = 'Já existe saldo para esta data.';
          } else {
            addBtn.disabled = false;
            msgDiv.style.display = 'none';
            msgDiv.textContent = '';
          }
        })
        .catch(() => {
          addBtn.disabled = false;
          msgDiv.style.display = 'none';
        });
    });
  }

  // Confirmação para ações destrutivas
  const deleteButtons = document.querySelectorAll('button[type="submit"]');
  deleteButtons.forEach(button => {
    if (button.textContent.includes('Excluir') || button.textContent.includes('Zerar')) {
      button.addEventListener('click', (e) => {
        const action = button.textContent.includes('Zerar') ? 'zerar toda a banca' : 'excluir este item';
        if (!confirm(`Tem certeza que deseja ${action}? Esta ação não pode ser desfeita.`)) {
          e.preventDefault();
        }
      });
    }
  });

  // Validação de formulários
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', (e) => {
      const numberInputs = form.querySelectorAll('input[type="number"]');
      let hasError = false;
      
      numberInputs.forEach(input => {
        const value = parseFloat(input.value);
        if (input.hasAttribute('required') && (isNaN(value) || value <= 0)) {
          input.classList.add('is-invalid');
          hasError = true;
        } else {
          input.classList.remove('is-invalid');
        }
      });
      
      if (hasError) {
        e.preventDefault();
        alert('Por favor, preencha todos os campos obrigatórios com valores válidos (maiores que zero).');
      }
    });
  });

  // Auto-formatação de valores monetários
  const moneyInputs = document.querySelectorAll('input[step="0.01"]');
  moneyInputs.forEach(input => {
    input.addEventListener('blur', () => {
      const value = parseFloat(input.value);
      if (!isNaN(value)) {
        input.value = value.toFixed(2);
      }
    });
  });
});
