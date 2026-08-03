// Portfolio contact form
const form = document.getElementById('contact-form');
const status = document.getElementById('form-status');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  status.textContent = 'Sending...';
  status.className = 'form-status';

  const data = Object.fromEntries(new FormData(form));

  try {
    const res = await fetch('/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    const json = await res.json();

    if (res.ok) {
      status.textContent = json.message || 'Sent! I will reply within 24h.';
      status.className = 'form-status success';
      form.reset();
    } else {
      status.textContent = json.error || 'Something went wrong. Email me directly.';
      status.className = 'form-status error';
    }
  } catch (err) {
    status.textContent = 'Network error. Email me directly: salim.muhammad.work0@gmail.com';
    status.className = 'form-status error';
  }
});
