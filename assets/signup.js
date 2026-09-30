(() => {
  const form = document.getElementById('email-signup');
  if (!form) return;
  const status = document.getElementById('signup-status');
  const button = form.querySelector('button[type=submit]');
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const endpoint = form.dataset.endpoint;
    if (!endpoint) { status.textContent = 'Signups are not open yet. Please check back soon.'; return; }
    button.disabled = true;
    status.textContent = 'Saving your signup…';
    try {
      const response = await fetch(endpoint, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({email:form.elements.email.value, consent:form.elements.consent.checked,
          website:form.elements.website.value, token:form.elements['cf-turnstile-response']?.value || ''})
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Could not save your signup. Please try again.');
      status.textContent = result.message;
      form.reset();
    } catch (error) {
      status.textContent = error.message || 'Could not connect. Please try again later.';
    } finally {
      button.disabled = false;
      if (window.turnstile) window.turnstile.reset();
    }
  });
})();
