(() => {
  'use strict';
  const root = document.documentElement;
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const EASE = 'cubic-bezier(.2, 0, 0, 1)';
  const ALERT_ICON = '<svg class="icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7.5v5m0 3.5h.01"/></svg>';
  const SPINNER = '<svg class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/></svg>';

  const storage = {
    take(key) {
      try { const value = sessionStorage.getItem(key); sessionStorage.removeItem(key); return value; }
      catch { return null; }
    },
    put(key, value) {
      try { sessionStorage.setItem(key, value); } catch { /* Feedback is optional when storage is blocked. */ }
    },
  };

  // Remove an element after its exit animation (or at once when motion is reduced).
  function leave(element, onDone) {
    const finish = () => { element.remove(); onDone?.(); };
    if (reduceMotion.matches) { finish(); return; }
    element.classList.add('is-leaving');
    element.addEventListener('animationend', finish, { once: true });
  }

  /* Theme */
  const themeButton = document.querySelector('.theme-toggle');
  function updateThemeButton() {
    const dark = root.dataset.theme === 'dark';
    themeButton.setAttribute('aria-pressed', String(dark));
    themeButton.setAttribute('aria-label', `Chuyển sang chế độ ${dark ? 'sáng' : 'tối'}`);
    themeButton.querySelector('.theme-label').textContent = dark ? 'Chế độ sáng' : 'Chế độ tối';
  }
  function applyTheme(theme) {
    root.dataset.theme = theme;
    try { localStorage.setItem('hr_theme', theme); }
    catch { /* Keep the selected theme for this page when storage is blocked. */ }
    updateThemeButton();
  }
  themeButton.hidden = false;
  updateThemeButton();
  const toggleTheme = () => applyTheme(root.dataset.theme === 'dark' ? 'light' : 'dark');
  themeButton.addEventListener('click', () => {
    if (reduceMotion.matches) { toggleTheme(); return; }
    if (document.startViewTransition && document.visibilityState === 'visible') {
      root.classList.add('theme-switching');
      const transition = document.startViewTransition(toggleTheme);
      transition.ready.catch(() => {});
      transition.finished.finally(() => root.classList.remove('theme-switching'));
      return;
    }
    root.classList.add('theme-fallback');
    toggleTheme();
    setTimeout(() => root.classList.remove('theme-fallback'), 320);
  });

  /* Sidebar */
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

    // Active indicator: browsers with cross-document view transitions morph the pill between pages;
    // elsewhere it starts sliding toward the chosen item while the next page loads.
    const crossDocumentTransitions = 'onpagereveal' in window && !mobile.matches;
    const current = sidebar.querySelector('.nav-item[aria-current]');
    if (current && storage.take('hr_nav_arrive') === current.getAttribute('href')) current.classList.add('nav-arrived');
    sidebar.querySelector('nav').addEventListener('click', event => {
      const link = event.target.closest('.nav-item');
      if (!link || link.hasAttribute('aria-current') || event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      storage.put('hr_nav_arrive', link.getAttribute('href'));
      link.classList.add('is-target');
      current?.classList.add('is-leaving-nav');
      const pill = sidebar.querySelector('.nav-pill');
      if (!pill || crossDocumentTransitions || reduceMotion.matches) return;
      const distance = link.getBoundingClientRect().top - pill.getBoundingClientRect().top;
      pill.animate([{ transform: 'none' }, { transform: `translateY(${distance}px)` }], { duration: 260, easing: EASE, fill: 'forwards' });
    });
  }

  /* Inline validation */
  const labelOf = control => (control.labels?.[0]?.textContent || 'trường này').replace('*', '').trim();
  const lowerFirst = text => (/^[A-ZÀ-Ỹ][a-zà-ỹ]/.test(text) ? text[0].toLowerCase() + text.slice(1) : text);
  function messageFor(control) {
    const validity = control.validity;
    const label = labelOf(control);
    if (validity.valueMissing) return `${control.tagName === 'SELECT' ? 'Vui lòng chọn' : 'Vui lòng nhập'} ${lowerFirst(label)}.`;
    if (validity.typeMismatch && control.type === 'email') return 'Email chưa đúng định dạng, ví dụ: ten@congty.vn.';
    if (validity.tooLong) return `${label} tối đa ${control.maxLength} ký tự.`;
    if (validity.badInput) return `${label} chưa hợp lệ.`;
    return control.validationMessage;
  }
  function describedBy(control, id, add) {
    const ids = (control.getAttribute('aria-describedby') || '').split(' ').filter(item => item && item !== id);
    if (add) ids.push(id);
    if (ids.length) control.setAttribute('aria-describedby', ids.join(' '));
    else control.removeAttribute('aria-describedby');
  }
  function showFieldError(control) {
    const field = control.closest('.field');
    if (!field || !control.id) return;
    let error = field.querySelector('.field-error');
    if (!error) {
      error = document.createElement('small');
      error.className = 'field-error';
      error.id = `${control.id}-error`;
      error.innerHTML = ALERT_ICON;
      error.append(document.createElement('span'));
      field.append(error);
    }
    error.classList.remove('is-leaving');
    error.lastChild.textContent = messageFor(control);
    control.setAttribute('aria-invalid', 'true');
    describedBy(control, error.id, true);
  }
  function clearFieldError(control) {
    control.removeAttribute('aria-invalid');
    const error = control.closest('.field')?.querySelector('.field-error');
    if (!error || error.classList.contains('is-leaving')) return;
    describedBy(control, error.id, false);
    leave(error);
  }
  let focusQueued = false;
  document.addEventListener('invalid', event => {
    const control = event.target;
    if (!control.closest('.field')) return;
    event.preventDefault();
    showFieldError(control);
    if (focusQueued) return;
    focusQueued = true;
    setTimeout(() => { focusQueued = false; control.form?.querySelector('[aria-invalid="true"]')?.focus(); });
  }, true);
  const recheck = event => {
    const control = event.target;
    if (control.getAttribute('aria-invalid') !== 'true') return;
    if (control.checkValidity()) clearFieldError(control);
    else showFieldError(control);
  };
  document.addEventListener('input', recheck);
  document.addEventListener('change', recheck);

  /* Confirmation dialog */
  function confirmSubmit(form) {
    const dialog = document.createElement('dialog');
    if (typeof dialog.showModal !== 'function') {
      if (window.confirm(form.dataset.confirm)) { form.dataset.confirmed = 'true'; form.requestSubmit(); }
      return;
    }
    dialog.className = 'confirm-dialog';
    dialog.setAttribute('aria-labelledby', 'confirm-title');
    dialog.setAttribute('aria-describedby', 'confirm-message');
    dialog.innerHTML = `<div class="confirm-body"><span class="section-marker" aria-hidden="true">${ALERT_ICON}</span><div><h2 id="confirm-title"></h2><p id="confirm-message"></p></div></div>
      <div class="confirm-actions"><button type="button" class="button" data-choice="cancel">Hủy</button><button type="button" class="button button-danger" data-choice="ok"></button></div>`;
    dialog.querySelector('h2').textContent = form.dataset.confirmTitle || 'Xác nhận thao tác';
    dialog.querySelector('p').textContent = form.dataset.confirm;
    dialog.querySelector('[data-choice="ok"]').textContent = form.querySelector('button[type="submit"]')?.textContent.trim() || 'Xác nhận';
    const trigger = document.activeElement;
    let closing = false;
    function close(confirmed) {
      if (closing) return;
      closing = true;
      leave(dialog, () => {
        if (confirmed) { form.dataset.confirmed = 'true'; form.requestSubmit(); }
        else trigger?.focus?.();
      });
    }
    dialog.addEventListener('cancel', event => { event.preventDefault(); close(false); });
    dialog.addEventListener('click', event => {
      if (event.target === dialog) close(false);
      const choice = event.target.closest('[data-choice]')?.dataset.choice;
      if (choice) close(choice === 'ok');
    });
    document.body.append(dialog);
    dialog.showModal();
    dialog.querySelector('[data-choice="cancel"]').focus();
  }

  /* Submit feedback */
  const pendingButtons = new Map();
  function setButtonLoading(button, text) {
    pendingButtons.set(button, [...button.childNodes]);
    button.style.minWidth = `${button.offsetWidth}px`;
    button.disabled = true;
    button.classList.add('is-loading');
    button.innerHTML = SPINNER;
    button.append(text);
  }
  document.querySelectorAll('form[method="post"]').forEach(form => {
    form.addEventListener('submit', event => {
      if (form.dataset.submitting === 'true') { event.preventDefault(); return; }
      if (form.dataset.confirm && form.dataset.confirmed !== 'true') { event.preventDefault(); confirmSubmit(form); return; }
      delete form.dataset.confirmed;
      form.dataset.submitting = 'true';
      form.setAttribute('aria-busy', 'true');
      form.querySelectorAll('button[type="submit"]').forEach(button => setButtonLoading(button, form.dataset.loadingText || 'Đang gửi…'));
      if (form.dataset.success) {
        const highlight = form.dataset.highlightField ? form.elements.namedItem(form.dataset.highlightField)?.value.trim() : '';
        storage.put('hr_pending_toast', JSON.stringify({
          message: form.dataset.success,
          action: new URL(form.getAttribute('action'), location.href).pathname,
          highlight,
          at: Date.now(),
        }));
      }
    });
  });
  document.querySelectorAll('form[method="get"][data-loading-target]').forEach(form => {
    form.addEventListener('submit', () => {
      const target = document.querySelector(form.dataset.loadingTarget);
      target?.classList.add('is-loading');
      target?.setAttribute('aria-busy', 'true');
      form.querySelectorAll('button[type="submit"]').forEach(button => setButtonLoading(button, 'Đang tìm…'));
    });
  });
  // Restore controls when a page returns from the browser's back/forward cache.
  window.addEventListener('pageshow', () => {
    document.querySelectorAll('form[data-submitting]').forEach(form => {
      delete form.dataset.submitting;
      form.removeAttribute('aria-busy');
    });
    document.querySelectorAll('.is-loading[aria-busy]').forEach(target => {
      target.classList.remove('is-loading');
      target.removeAttribute('aria-busy');
    });
    pendingButtons.forEach((children, button) => {
      button.disabled = false;
      button.classList.remove('is-loading');
      button.style.minWidth = '';
      button.replaceChildren(...children);
    });
    pendingButtons.clear();
    document.querySelectorAll('.nav-item.is-target, .nav-item.is-leaving-nav').forEach(item => item.classList.remove('is-target', 'is-leaving-nav'));
    document.querySelector('.nav-pill')?.getAnimations().forEach(animation => animation.cancel());
  });

  /* Success toast: the server redirects to another page only when a save succeeded. */
  function showToast(message) {
    let region = document.querySelector('.toast-region');
    if (!region) {
      region = document.createElement('div');
      region.className = 'toast-region';
      region.setAttribute('role', 'status');
      region.setAttribute('aria-live', 'polite');
      document.body.append(region);
    }
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `<svg class="toast-check" viewBox="0 0 26 26" aria-hidden="true"><circle cx="13" cy="13" r="13"/><path d="m8 13.5 3.2 3.2L18 10" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg><span></span>
      <button type="button" class="toast-close" aria-label="Đóng thông báo"><svg class="icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="m6 6 12 12M6 18 18 6"/></svg></button>`;
    toast.querySelector('span').textContent = message;
    let timer;
    const dismiss = () => { clearTimeout(timer); if (!toast.classList.contains('is-leaving')) leave(toast); };
    const schedule = delay => { clearTimeout(timer); timer = setTimeout(dismiss, delay); };
    toast.querySelector('.toast-close').addEventListener('click', dismiss);
    toast.addEventListener('mouseenter', () => clearTimeout(timer));
    toast.addEventListener('mouseleave', () => schedule(2000));
    // Append after the live region exists so screen readers announce the message.
    setTimeout(() => { region.append(toast); schedule(4500); }, 60);
  }
  const pending = storage.take('hr_pending_toast');
  if (pending) {
    try {
      const { message, action, highlight, at } = JSON.parse(pending);
      const succeeded = location.pathname !== action && location.pathname !== '/login' && !document.getElementById('form-error');
      if (succeeded && Date.now() - at < 30000) {
        showToast(message);
        const row = highlight && document.querySelector(`tr[data-row-key="${CSS.escape(highlight)}"]`);
        if (row) {
          row.classList.add('row-highlight');
          row.scrollIntoView({ block: 'nearest', behavior: reduceMotion.matches ? 'auto' : 'smooth' });
        }
      }
    } catch { /* Ignore malformed feedback state. */ }
  }

  /* Login: a soft light and the illustration follow the pointer. */
  const loginShell = document.querySelector('.login-shell');
  if (loginShell && !reduceMotion.matches && matchMedia('(pointer: fine)').matches) {
    const glow = loginShell.querySelector('.login-glow');
    const art = loginShell.querySelector('.login-art');
    let frame = 0;
    let x = 0;
    let y = 0;
    loginShell.addEventListener('pointermove', event => {
      x = event.clientX;
      y = event.clientY;
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        glow?.style.setProperty('--glow-x', `${x}px`);
        glow?.style.setProperty('--glow-y', `${y}px`);
        if (!art) return;
        const box = art.getBoundingClientRect();
        art.style.setProperty('--art-x', `${((x - box.left - box.width / 2) / innerWidth * 12).toFixed(2)}px`);
        art.style.setProperty('--art-y', `${((y - box.top - box.height / 2) / innerHeight * 10).toFixed(2)}px`);
      });
    }, { passive: true });
  }

  document.getElementById('form-error')?.focus();
})();
