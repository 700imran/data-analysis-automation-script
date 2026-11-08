/* MarginPulse website interactions. Progressive enhancement: the page is fully readable without JavaScript. */
(() => {
  'use strict';
  const config = window.MARGINPULSE_CONFIG || {};
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Header, mobile menu, scroll progress, back-to-top ---------- */
  const header = $('.site-header');
  const navToggle = $('.nav-toggle');
  const nav = $('.main-nav');
  const progress = $('#scrollProgress');
  const toTop = $('#backToTop');

  const closeMenu = () => {
    if (!nav) return;
    nav.classList.remove('is-open');
    document.body.classList.remove('menu-open');
    if (navToggle) { navToggle.setAttribute('aria-expanded', 'false'); navToggle.setAttribute('aria-label', 'Open navigation'); }
  };
  if (navToggle && nav) {
    navToggle.addEventListener('click', () => {
      const opened = nav.classList.toggle('is-open');
      document.body.classList.toggle('menu-open', opened);
      navToggle.setAttribute('aria-expanded', String(opened));
      navToggle.setAttribute('aria-label', opened ? 'Close navigation' : 'Open navigation');
    });
    $$('a', nav).forEach(a => a.addEventListener('click', closeMenu));
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMenu(); });
    document.addEventListener('click', e => { if (nav.classList.contains('is-open') && !nav.contains(e.target) && !navToggle.contains(e.target)) closeMenu(); });
    window.matchMedia('(min-width: 1001px)').addEventListener('change', closeMenu);
  }

  let ticking = false;
  const onScroll = () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      const y = window.scrollY || 0;
      const max = document.documentElement.scrollHeight - window.innerHeight;
      if (header) header.classList.toggle('is-scrolled', y > 8);
      if (progress) progress.style.transform = `scaleX(${max > 0 ? Math.min(1, y / max) : 0})`;
      if (toTop) toTop.classList.toggle('is-visible', y > 700);
      ticking = false;
    });
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  if (toTop) toTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' }));

  /* ---------- Scroll-spy for the main navigation ---------- */
  if ('IntersectionObserver' in window && nav) {
    const links = $$('a[href^="#"]', nav).filter(a => a.getAttribute('href').length > 1 && !a.classList.contains('nav-cta'));
    const map = new Map(links.map(a => [a.getAttribute('href').slice(1), a]));
    const spy = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        links.forEach(l => { l.classList.remove('is-active'); l.removeAttribute('aria-current'); });
        const link = map.get(entry.target.id);
        if (link) { link.classList.add('is-active'); link.setAttribute('aria-current', 'true'); }
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    map.forEach((_, id) => { const el = document.getElementById(id); if (el) spy.observe(el); });
  }

  /* ---------- Reveal on scroll ---------- */
  if ('IntersectionObserver' in window && !reduceMotion) {
    const targets = $$('.section-heading, .coverage-item, .output-box, .process-grid article, .pilot-steps > div, .fit-checks > div, .enquiry-assurance, .lead-form, .faq-list details, .note-callout');
    targets.forEach((el, i) => { el.classList.add('reveal'); el.style.setProperty('--reveal-delay', `${(i % 4) * 70}ms`); });
    const io = new IntersectionObserver(entries => entries.forEach(en => { if (en.isIntersecting) { en.target.classList.add('is-visible'); io.unobserve(en.target); } }), { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    targets.forEach(el => io.observe(el));
  }

  /* ---------- Coverage explorer (click an area to see example questions and inputs) ---------- */
  const COVERAGE = [
    { q: ['Which customers and products drive revenue, and how concentrated is it?', 'What changed versus the previous period?', 'Are there unusual spikes or drops that need verifying?'], i: 'Sales register or invoice lines (date, customer, product, quantity, value).' },
    { q: ['Which products or categories earn the lowest margin?', 'Did margin move because of price, discount or cost?', 'Where is cost data missing, so margin cannot be relied on?'], i: 'Sales lines with cost, or purchase cost data.' },
    { q: ['Which expense categories moved most?', 'What is recurring and what looks one-off?', 'Does the expense period match the sales period being reviewed?'], i: 'Expense ledger or voucher export (date, category, amount).' },
    { q: ['Which items are below reorder level or have had no recent sales?', 'Does the stock ledger agree with closing stock?', 'Did supplier prices change from month to month?'], i: 'Stock summary, stock movements and purchase register.' },
    { q: ['How much is overdue, and for how long?', 'Which customers hold the largest overdue balances?', 'Do receipts agree with the invoices raised?'], i: 'Receivables or outstanding report and receipts register.' }
  ];
  $$('.coverage-item').forEach((item, idx) => {
    const data = COVERAGE[idx];
    if (!data) return;
    const id = `coverage-detail-${idx}`;
    const detail = document.createElement('div');
    detail.className = 'coverage-detail';
    detail.id = id;
    detail.hidden = true;
    detail.innerHTML = `<p class="cd-label">Example questions</p><ul>${data.q.map(q => `<li>${q}</li>`).join('')}</ul><p class="cd-label">Typical input</p><p class="cd-input">${data.i}</p>`;
    item.appendChild(detail);
    item.setAttribute('role', 'button');
    item.setAttribute('tabindex', '0');
    item.setAttribute('aria-expanded', 'false');
    item.setAttribute('aria-controls', id);
    const toggle = () => {
      const open = item.getAttribute('aria-expanded') !== 'true';
      $$('.coverage-item').forEach(o => { o.setAttribute('aria-expanded', 'false'); o.classList.remove('is-open'); const d = $('.coverage-detail', o); if (d) d.hidden = true; });
      item.setAttribute('aria-expanded', String(open));
      item.classList.toggle('is-open', open);
      detail.hidden = !open;
    };
    item.addEventListener('click', e => { if (e.target.closest('.coverage-detail a')) return; toggle(); });
    item.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
  });

  /* ---------- FAQ: one open at a time ---------- */
  const faqs = $$('.faq-list details');
  faqs.forEach(d => d.addEventListener('toggle', () => { if (d.open) faqs.forEach(o => { if (o !== d) o.open = false; }); }));

  /* ---------- CTA links jump to the form and focus the first field ---------- */
  $$('a[href="#enquiry"]').forEach(a => a.addEventListener('click', () => {
    setTimeout(() => { const f = $('#leadForm [name="name"]'); if (f && window.innerWidth > 760) f.focus({ preventScroll: true }); }, reduceMotion ? 0 : 600);
  }));
  document.querySelectorAll('#year, .current-year').forEach(el => el.textContent = new Date().getFullYear());

  /* ---------- Lead form ---------- */
  const form = $('#leadForm');
  if (!form) return;
  const message = $('#formMessage');
  const submitButton = $('button[type="submit"]', form);
  const REQUIRED = ['name', 'email', 'company', 'country', 'industry', 'objective', 'challenge'];
  const LABELS = { name: 'your name', email: 'a valid business email', company: 'your company name', country: 'your country', industry: 'your industry', objective: 'your main priority', challenge: 'a short description of your reporting process' };

  // Suggest country from the visitor's time zone (they can change it).
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
    const sel = form.elements.country;
    if (sel && !sel.value) {
      if (/^Asia\/(Kolkata|Calcutta)$/.test(tz)) sel.value = 'India';
      else if (/^Asia\/Dubai$/.test(tz)) sel.value = 'United Arab Emirates';
    }
  } catch (e) { /* ignore */ }

  const fieldOf = name => form.elements[name];
  const errorEl = name => {
    const f = fieldOf(name);
    if (!f) return null;
    const label = f.closest('label');
    let el = label && $('.field-error', label);
    if (!el && label) { el = document.createElement('small'); el.className = 'field-error'; el.id = `err-${name}`; el.setAttribute('role', 'alert'); label.appendChild(el); }
    return el;
  };
  const validateField = name => {
    const f = fieldOf(name);
    if (!f) return true;
    let ok = f.value.trim() !== '';
    if (ok && name === 'email') ok = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(f.value.trim());
    const el = errorEl(name);
    if (el) el.textContent = ok ? '' : `Please enter ${LABELS[name]}.`;
    f.classList.toggle('is-invalid', !ok);
    if (ok) f.removeAttribute('aria-invalid'); else { f.setAttribute('aria-invalid', 'true'); f.setAttribute('aria-describedby', `err-${name}`); }
    return ok;
  };

  const progressText = $('#formProgressText');
  const progressBar = $('#formProgressBar');
  const updateProgress = () => {
    const done = REQUIRED.filter(n => { const f = fieldOf(n); if (!f || f.value.trim() === '') return false; return n !== 'email' || /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(f.value.trim()); }).length;
    if (progressText) progressText.textContent = `${done} of ${REQUIRED.length} required fields complete`;
    if (progressBar) progressBar.style.width = `${(done / REQUIRED.length) * 100}%`;
  };
  const counter = $('.char-count');
  const challenge = fieldOf('challenge');
  const updateCounter = () => { if (counter && challenge) counter.textContent = `${challenge.value.length} / ${challenge.maxLength}`; };

  REQUIRED.forEach(n => {
    const f = fieldOf(n);
    if (!f) return;
    f.addEventListener('blur', () => validateField(n));
    f.addEventListener('input', () => { if (f.classList.contains('is-invalid')) validateField(n); updateProgress(); if (n === 'challenge') updateCounter(); });
    f.addEventListener('change', () => { if (f.classList.contains('is-invalid')) validateField(n); updateProgress(); });
  });
  updateProgress(); updateCounter();

  const params = new URLSearchParams(window.location.search);
  const utm = k => (params.get(k) || '').slice(0, 100);

  const setMessage = (text, kind) => { message.className = `form-message ${kind || ''}`; message.textContent = text; };
  const ERRORS = {
    too_many_requests: 'You have just sent an enquiry. Please wait a moment before sending another.',
    invalid_email: 'Please check the email address and try again.',
    missing_required_fields: 'Some required fields are missing. Please complete them and try again.',
    consent_required: 'Please confirm the enquiry consent before submitting.'
  };

  const showSuccess = (ref) => {
    const card = document.createElement('div');
    card.className = 'form-success';
    card.setAttribute('role', 'status');
    card.innerHTML = `<span class="success-icon" aria-hidden="true">✓</span><h3>Thank you. Your enquiry has been received.</h3><p>We will review the details and reply using the contact information you provided.${ref ? ` Your reference is <strong>${ref}</strong>.` : ''}</p><button type="button" class="btn btn-ghost" id="newEnquiry">Send another enquiry</button>`;
    form.hidden = true;
    form.parentNode.insertBefore(card, form);
    card.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'center' });
    $('#newEnquiry', card).addEventListener('click', () => { card.remove(); form.hidden = false; form.reset(); updateProgress(); updateCounter(); });
  };

  form.addEventListener('submit', async event => {
    event.preventDefault();
    setMessage('', '');
    const results = REQUIRED.map(n => [n, validateField(n)]);
    const firstBad = results.find(r => !r[1]);
    if (firstBad) { fieldOf(firstBad[0]).focus(); setMessage('Please complete the highlighted fields.', 'error'); return; }
    if (!form.elements.consent.checked) { setMessage(ERRORS.consent_required, 'error'); form.elements.consent.focus(); return; }

    const data = Object.fromEntries(new FormData(form).entries());
    const payload = { ...data, consent: true, formName: 'MarginPulse Managed Intelligence Enquiry', submittedAt: new Date().toISOString(),
      source: window.location.origin + window.location.pathname, utm_source: utm('utm_source'), utm_medium: utm('utm_medium'), utm_campaign: utm('utm_campaign') };

    submitButton.disabled = true;
    submitButton.setAttribute('aria-busy', 'true');
    submitButton.innerHTML = 'Submitting <span>…</span>';
    try {
      if (config.leadSheetEndpoint) {
        const ctrl = new AbortController();
        const timer = setTimeout(() => ctrl.abort(), 20000);
        let res;
        try {
          // text/plain keeps this a "simple" request, so the browser does not need a CORS preflight that Apps Script cannot answer.
          res = await fetch(config.leadSheetEndpoint, { method: 'POST', headers: { 'Content-Type': 'text/plain;charset=utf-8' }, body: JSON.stringify(payload), signal: ctrl.signal, redirect: 'follow' });
        } finally { clearTimeout(timer); }
        const out = await res.json().catch(() => null);
        if (!out || !out.ok) { const e = new Error(ERRORS[out && out.error] || 'The enquiry service could not save your details.'); e.friendly = true; throw e; }
        showSuccess(out.id && out.id !== 'ignored' ? out.id : '');
      } else if (config.formEndpoint) {
        const res = await fetch(config.formEndpoint, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(payload) });
        if (!res.ok) throw new Error(`The enquiry service returned ${res.status}.`);
        showSuccess('');
      } else if (config.contactEmail) {
        const subject = encodeURIComponent(`MarginPulse enquiry: ${data.company}`);
        const body = encodeURIComponent(Object.entries(payload).filter(([k]) => k !== 'website').map(([k, v]) => `${k}: ${v}`).join('\n'));
        window.location.href = `mailto:${config.contactEmail}?subject=${subject}&body=${body}`;
        setMessage('Your email app should open with the enquiry details. Please press send to complete your enquiry.', 'success');
      } else if (['localhost', '127.0.0.1', ''].includes(window.location.hostname)) {
        setMessage('Preview mode: lead delivery is not connected yet, so nothing was stored. Set leadSheetEndpoint in js/config.js.', 'warning');
        console.info('MarginPulse enquiry (preview, not sent):', payload);
      } else {
        // Never let a visitor believe an enquiry was sent when it was not.
        setMessage('Sorry, the enquiry form is not available right now and your details have not been sent. Please try again later.', 'error');
      }
    } catch (error) {
      const text = error.friendly ? error.message : (error.name === 'AbortError' ? 'The request timed out.' : 'We could not confirm that your enquiry was saved. Please check your connection and try again.');
      setMessage(text, 'error');
    } finally {
      submitButton.disabled = false;
      submitButton.removeAttribute('aria-busy');
      submitButton.innerHTML = 'Submit enquiry <span>→</span>';
    }
  });
})();
