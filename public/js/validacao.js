const DOMINIOS = ['@senai.br', '@fiesc.com.br', '@estudante.senai.br', '@aluno.senai.br', '@professor.senai.br', '@docente.senai.br'];
function validarEmail(email) { return DOMINIOS.some(d => email.toLowerCase().endsWith(d)); }
document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form');
  const email = document.getElementById('email');
  const nome = document.getElementById('nome');
  const hint = document.getElementById('email-hint');
  if (!form) return;
  email?.addEventListener('input', () => {
    if (!email.value) { if (hint) hint.textContent = ''; return; }
    if (validarEmail(email.value)) {
      email.style.borderColor = '#2E7D52';
      if (hint) { hint.textContent = '✓ Domínio permitido'; hint.style.color = '#2E7D52'; }
    } else {
      email.style.borderColor = '#C0603A';
      if (hint) { hint.textContent = 'Use @senai.br, @fiesc.com.br ou @estudante.senai.br'; hint.style.color = '#C0603A'; }
    }
  });
  form.addEventListener('submit', e => {
    if (!nome?.value.trim()) { e.preventDefault(); nome.style.borderColor = '#C0603A'; nome.focus(); return; }
    if (!validarEmail(email?.value || '')) { e.preventDefault(); email.focus(); }
  });
});
