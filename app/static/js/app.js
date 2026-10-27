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
  // Removing `is-leaving` before then cancels the exit.
  function leave(element, onDone) {
    let done = false;
    const finish = () => {
      if (done || !element.classList.contains('is-leaving')) return;
      done = true;
      element.remove();
      onDone?.();
    };
    element.classList.add('is-leaving');
    if (reduceMotion.matches) { finish(); return; }
    element.addEventListener('animationend', event => { if (event.target === element) finish(); });
    // A hidden or force-closed element never fires animationend.
    setTimeout(finish, 400);
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
  // Pages with passwords or hand-off credentials are never captured into a view-transition snapshot.
  const noSnapshot = Boolean(document.querySelector('meta[name="hr-no-snapshot"]'));
  themeButton.addEventListener('click', () => {
    if (reduceMotion.matches) { toggleTheme(); return; }
    if (document.startViewTransition && document.visibilityState === 'visible' && !noSnapshot) {
      root.classList.add('theme-switching');
      const transition = document.startViewTransition(toggleTheme);
      const done = () => root.classList.remove('theme-switching');
      // A skipped transition (hidden tab, navigation started) rejects `ready`; the theme is already applied then.
      transition.ready.catch(() => {});
      // then(done, done) rather than finally(): finally() returns a new promise that would re-reject unhandled.
      transition.finished.then(done, done);
      return;
    }
    root.classList.add('theme-fallback');
    toggleTheme();
    setTimeout(() => root.classList.remove('theme-fallback'), 280);
  });

  /* Press feedback: Enter/Space get the same short press as a pointer (:active). */
  document.addEventListener('keydown', event => {
    if (event.repeat || (event.key !== 'Enter' && event.key !== ' ')) return;
    const target = event.target.closest?.('.button, .theme-toggle, .icon-button, .kpi');
    if (!target || (event.key === ' ' && target.tagName === 'A')) return;
    target.classList.add('is-pressed');
    setTimeout(() => target.classList.remove('is-pressed'), 120);
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
      pill.animate([{ transform: 'none' }, { transform: `translateY(${distance}px)` }], { duration: 220, easing: EASE, fill: 'forwards' });
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
  function confirmSubmit(form, submitter) {
    const dialog = document.createElement('dialog');
    // Re-submit with the original button so its name/value still reach the server.
    const submit = () => { form.dataset.confirmed = 'true'; form.requestSubmit(submitter?.form === form ? submitter : null); };
    if (typeof dialog.showModal !== 'function') {
      if (window.confirm(form.dataset.confirm)) submit();
      return;
    }
    dialog.className = 'confirm-dialog';
    dialog.setAttribute('aria-labelledby', 'confirm-title');
    dialog.setAttribute('aria-describedby', 'confirm-message');
    dialog.innerHTML = `<div class="confirm-body"><span class="section-marker" aria-hidden="true">${ALERT_ICON}</span><div><h2 id="confirm-title"></h2><p id="confirm-message"></p></div></div>
      <div class="confirm-actions"><button type="button" class="button" data-choice="cancel">Hủy</button><button type="button" class="button button-danger-solid" data-choice="ok"></button></div>`;
    dialog.querySelector('h2').textContent = form.dataset.confirmTitle || 'Xác nhận thao tác';
    dialog.querySelector('p').textContent = form.dataset.confirm;
    dialog.querySelector('[data-choice="ok"]').textContent = buttonLabel(form.querySelector('button[type="submit"]')) || 'Xác nhận';
    const trigger = submitter || document.activeElement;
    let closing = false;
    function close(confirmed) {
      if (closing) return;
      closing = true;
      // The request starts at once; the exit animation plays while the next page loads.
      if (confirmed) submit();
      leave(dialog, confirmed ? null : () => trigger?.focus?.());
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
  // Each submit button stacks its label and its pending label in one grid cell (see .button-stack), so it is as
  // wide as the longer one from the start: showing the spinner never resizes it or replaces its content.
  function preparePending(button, text) {
    const label = document.createElement('span');
    label.className = 'button-face';
    label.append(...button.childNodes);
    const pendingLabel = document.createElement('span');
    pendingLabel.className = 'button-face';
    pendingLabel.innerHTML = SPINNER;
    pendingLabel.append(text);
    button.classList.add('button-stack');
    button.replaceChildren(label, pendingLabel);
  }
  function buttonLabel(button) {
    return (button?.querySelector('.button-face') || button)?.textContent.trim();
  }
  function setPending(form, pending, lock) {
    form.querySelectorAll('button[type="submit"]').forEach(button => {
      button.classList.toggle('is-loading', pending);
      // aria-disabled, not disabled: a disabled submitter would drop its name/value from the request.
      // The form's submitting flag blocks repeat submissions instead.
      if (pending && lock) button.setAttribute('aria-disabled', 'true');
      else button.removeAttribute('aria-disabled');
    });
    const target = form.dataset.loadingTarget ? document.querySelector(form.dataset.loadingTarget) : form;
    target?.classList.toggle('is-loading', pending && target !== form);
    if (pending) target?.setAttribute('aria-busy', 'true');
    else target?.removeAttribute('aria-busy');
  }
  const postForms = [...document.querySelectorAll('form[method="post"]')];
  const getForms = [...document.querySelectorAll('form[method="get"][data-loading-target]')];
  postForms.forEach(form => {
    form.querySelectorAll('button[type="submit"]').forEach(button => preparePending(button, form.dataset.loadingText || 'Đang gửi…'));
    form.addEventListener('submit', event => {
      if (form.dataset.submitting === 'true') { event.preventDefault(); return; }
      if (form.dataset.confirm && form.dataset.confirmed !== 'true') { event.preventDefault(); confirmSubmit(form, event.submitter); return; }
      delete form.dataset.confirmed;
      form.dataset.submitting = 'true';
      setPending(form, true, true);
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
  // Searches are never locked: submitting again simply replaces the pending request.
  getForms.forEach(form => {
    form.querySelectorAll('button[type="submit"]').forEach(button => preparePending(button, 'Đang tìm…'));
    form.addEventListener('submit', () => setPending(form, true, false));
  });
  function resetPending(forms) {
    forms.forEach(form => {
      delete form.dataset.submitting;
      setPending(form, false);
    });
  }
  // Restore controls when a page returns from the browser's back/forward cache.
  window.addEventListener('pageshow', () => {
    resetPending([...postForms, ...getForms]);
    document.querySelectorAll('.nav-item.is-target, .nav-item.is-leaving-nav').forEach(item => item.classList.remove('is-target', 'is-leaving-nav'));
    document.querySelector('.nav-pill')?.getAnimations().forEach(animation => animation.cancel());
  });
  // A stopped or failed load keeps this page: searches look idle again. POST forms stay locked, because an
  // aborted response does not prove the server did not act on the request; reloading the page unlocks them.
  window.navigation?.addEventListener('navigateerror', () => resetPending(getForms));

  /* Success toast: shown only on the page a successful POST redirected to (Post/Redirect/Get).
     An error response, a Back/Forward visit or a later link click must never announce success. */
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
      const navigation = performance.getEntriesByType?.('navigation')[0];
      const redirected = navigation?.type === 'navigate' && navigation.redirectCount > 0;
      const succeeded = redirected && location.pathname !== action && location.pathname !== '/login' && !document.getElementById('form-error');
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

  /* Hand-off: copy one credential on an explicit click. Its value never goes to a toast, log or storage. */
  const copyStatus = document.querySelector('.copy-status');
  document.querySelectorAll('[data-copy]').forEach(button => {
    const source = document.getElementById(button.dataset.copy);
    if (!source || !copyStatus) return;
    const name = source.closest('div')?.querySelector('dt')?.textContent.trim().toLowerCase() || 'giá trị';
    let timer;
    button.hidden = false;
    button.addEventListener('click', async () => {
      clearTimeout(timer);
      button.classList.remove('is-copied');
      copyStatus.classList.remove('is-error');
      try {
        if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
        await navigator.clipboard.writeText(source.textContent);
        button.classList.add('is-copied');
        copyStatus.textContent = `Đã sao chép ${name}.`;
        timer = setTimeout(() => button.classList.remove('is-copied'), 2000);
      } catch {
        // Blocked or unsupported: select the value so it can be copied by hand.
        getSelection()?.selectAllChildren(source);
        copyStatus.classList.add('is-error');
        copyStatus.textContent = `Không sao chép tự động được ${name}. Giá trị đã được chọn, nhấn Ctrl+C để sao chép.`;
      }
    });
  });

  /* "/" focuses the page's search field unless the user is typing somewhere. */
  const searchField = document.querySelector('[data-search-shortcut]');
  if (searchField) {
    document.addEventListener('keydown', event => {
      if (event.key !== '/' || event.ctrlKey || event.metaKey || event.altKey || event.defaultPrevented) return;
      if (event.target.closest?.('input, textarea, select, [contenteditable]')) return;
      event.preventDefault();
      searchField.focus();
      searchField.select();
    });
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

  /* Dashboard: the time these server-rendered numbers were read. */
  const timeFormat = new Intl.DateTimeFormat('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit', year: 'numeric' });
  document.querySelectorAll('[data-today]').forEach(element => {
    element.textContent = ` Cập nhật lúc ${timeFormat.format(new Date())}.`;
    element.hidden = false;
  });

  document.getElementById('form-error')?.focus();
})();
