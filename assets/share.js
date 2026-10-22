// Sharing happens only after a visitor clicks; no tracking or third-party requests.
document.querySelectorAll('[data-share-url]').forEach(button => {
  if (typeof navigator.share === 'function') button.hidden = false;
});
document.querySelectorAll('[data-copy-url]').forEach(button => {
  if (navigator.clipboard && window.isSecureContext) button.hidden = false;
});
document.addEventListener('click', async event => {
  const button = event.target.closest('[data-share-url], [data-copy-url]');
  if (!button) return;
  const status = button.parentElement.querySelector('[data-share-status]');
  status.textContent = '';
  try {
    if (button.dataset.shareUrl) {
      await navigator.share({ title: button.dataset.shareTitle, url: button.dataset.shareUrl });
    } else {
      await navigator.clipboard.writeText(button.dataset.copyUrl);
      status.textContent = 'Link copied. Ready to paste into a message or post.';
    }
  } catch (error) {
    if (error.name !== 'AbortError') status.textContent = 'Sharing is unavailable here. Copy the address from your browser instead.';
  }
});
