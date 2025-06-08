// static/script.js

console.log("Script carregado.");

document.addEventListener('DOMContentLoaded', () => {
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
});
