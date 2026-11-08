(() => {
  const config = window.MARGINPULSE_CONFIG || {};
  const navToggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('.main-nav');
  if (navToggle && nav) {
    navToggle.addEventListener('click', () => {
      const opened = nav.classList.toggle('is-open');
      navToggle.setAttribute('aria-expanded', String(opened));
    });
    nav.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
      nav.classList.remove('is-open');
      navToggle.setAttribute('aria-expanded', 'false');
    }));
  }
  document.querySelectorAll('#year, .current-year').forEach(el => el.textContent = new Date().getFullYear());

  const form = document.getElementById('leadForm');
  const message = document.getElementById('formMessage');
  if (form && message) {
    form.addEventListener('submit', async event => {
      event.preventDefault();
      message.className = 'form-message';
      message.textContent = '';
      if (!form.reportValidity()) return;
      const data = Object.fromEntries(new FormData(form).entries());
      if (!form.querySelector('[name="consent"]').checked) {
        message.textContent = 'Please confirm the enquiry consent before submitting.';
        message.classList.add('error');
        return;
      }
      const payload = {
        ...data,
        consent: true,
        formName: 'MarginPulse Managed Intelligence Enquiry',
        submittedAt: new Date().toISOString(),
        source: window.location.href
      };
      const submitButton = form.querySelector('button[type="submit"]');
      submitButton.disabled = true;
      submitButton.innerHTML = 'Submitting <span>…</span>';
      try {
        if (config.formEndpoint) {
          const response = await fetch(config.formEndpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
            body: JSON.stringify(payload)
          });
          if (!response.ok) throw new Error(`The enquiry service returned ${response.status}.`);
          form.reset();
          message.textContent = 'Thank you. Your enquiry has been submitted. We will review the details and respond using the contact information provided.';
          message.classList.add('success');
        } else if (config.contactEmail) {
          const subject = encodeURIComponent(`MarginPulse enquiry — ${data.company}`);
          const body = encodeURIComponent(Object.entries(payload).map(([key, value]) => `${key}: ${value}`).join('\n'));
          window.location.href = `mailto:${config.contactEmail}?subject=${subject}&body=${body}`;
          message.textContent = 'Your email application should open with the enquiry details. Please send the email to complete submission.';
          message.classList.add('success');
        } else {
          message.textContent = 'The enquiry form is working in preview mode, but lead delivery is not connected yet. The site owner must add a verified contact email or form endpoint in js/config.js before publishing.';
          message.classList.add('warning');
          const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url; a.download = `marginpulse-enquiry-${new Date().toISOString().slice(0,10)}.json`;
          document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
        }
      } catch (error) {
        message.textContent = `We could not send the enquiry. Please try again later or contact the service operator. (${error.message})`;
        message.classList.add('error');
      } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = 'Submit enquiry <span>→</span>';
      }
    });
  }
})();
