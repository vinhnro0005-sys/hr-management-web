(() => {
  'use strict';
  const root = document.documentElement;
  const themeButton = document.querySelector('.theme-toggle');
  function updateThemeButton() {
    const dark = root.dataset.theme === 'dark';
    themeButton.setAttribute('aria-pressed', String(dark));
    themeButton.setAttribute('aria-label', `Chuyển sang chế độ ${dark ? 'sáng' : 'tối'}`);
    themeButton.querySelector('.theme-label').textContent = dark ? 'Chế độ sáng' : 'Chế độ tối';
  }
  themeButton.hidden = false;
  updateThemeButton();
  themeButton.addEventListener('click', () => {
    root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('hr_theme', root.dataset.theme); }
    catch { /* Keep the selected theme for this page when storage is blocked. */ }
    updateThemeButton();
  });

  const sidebar = document.querySelector('.sidebar');
  if (sidebar) {
    const openButton = document.querySelector('.sidebar-open');
    const closeButton = document.querySelector('.sidebar-close');
    const backdrop = document.querySelector('.sidebar-backdrop');
    const workspace = document.querySelector('.workspace');
    const mobile = matchMedia('(max-width: 767px)');
    let returnFocus;
    function setSidebar(open, restoreFocus = true) {
      root.classList.toggle('sidebar-is-open', open);
      openButton.setAttribute('aria-expanded', String(open));
      backdrop.hidden = !open;
      workspace.inert = open;
      sidebar.inert = mobile.matches && !open;
      if (open) {
        returnFocus = document.activeElement;
        sidebar.setAttribute('role', 'dialog');
        sidebar.setAttribute('aria-modal', 'true');
        closeButton.focus();
      } else {
        sidebar.removeAttribute('role');
        sidebar.removeAttribute('aria-modal');
        if (restoreFocus && returnFocus) returnFocus.focus();
      }
    }
    openButton.hidden = false;
    closeButton.hidden = false;
    root.dataset.uiReady = 'true';
    setSidebar(false, false);
    openButton.addEventListener('click', () => setSidebar(true));
    closeButton.addEventListener('click', () => setSidebar(false));
    backdrop.addEventListener('click', () => setSidebar(false));
    mobile.addEventListener('change', () => setSidebar(false));
    sidebar.addEventListener('keydown', event => {
      if (!root.classList.contains('sidebar-is-open')) return;
      if (event.key === 'Escape') setSidebar(false);
      if (event.key !== 'Tab') return;
      const items = [...sidebar.querySelectorAll('a, button:not(:disabled)')].filter(item => item.getClientRects().length);
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    });
  }

  const pendingButtons = new Map();
  document.querySelectorAll('form[method="post"]').forEach(form => {
    form.addEventListener('submit', event => {
      if (form.dataset.submitting === 'true') { event.preventDefault(); return; }
      if (form.dataset.confirm && !window.confirm(form.dataset.confirm)) { event.preventDefault(); return; }
      form.dataset.submitting = 'true';
      form.setAttribute('aria-busy', 'true');
      form.querySelectorAll('button[type="submit"]').forEach(button => {
        button.disabled = true;
        pendingButtons.set(button, [...button.childNodes]);
        button.replaceChildren('Đang gửi…');
      });
    });
  });
  // Restore controls when a page returns from the browser's back/forward cache.
  window.addEventListener('pageshow', () => {
    document.querySelectorAll('form[data-submitting]').forEach(form => {
      delete form.dataset.submitting;
      form.removeAttribute('aria-busy');
    });
    pendingButtons.forEach((children, button) => {
      button.disabled = false;
      button.replaceChildren(...children);
    });
    pendingButtons.clear();
  });
  document.getElementById('form-error')?.focus();
})();
