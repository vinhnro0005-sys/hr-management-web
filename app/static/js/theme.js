// Run before the stylesheet to avoid flashing the wrong theme.
(() => {
  const root = document.documentElement;
  const systemTheme = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  let theme = systemTheme;
  try {
    const saved = localStorage.getItem('hr_theme');
    if (saved === 'light' || saved === 'dark') theme = saved;
  } catch { /* The system preference still works when storage is blocked. */ }
  root.dataset.theme = theme;

  // Back/Forward visits and same-page reloads (a filter, a form shown again with a server error) show the page
  // as it is, without replaying the entrance.
  let samePage = false;
  try {
    const from = new URL(document.referrer);
    samePage = from.origin === location.origin && from.pathname === location.pathname;
  } catch { /* No referrer. */ }
  if (performance.getEntriesByType?.('navigation')[0]?.type === 'back_forward' || samePage) root.classList.add('no-entrance');

  // A skipped view transition (hidden tab, slow page) is harmless; keep it out of the console.
  const quiet = transition => {
    [transition?.ready, transition?.updateCallbackDone, transition?.finished].forEach(promise => promise?.catch(() => {}));
  };
  // A cross-document view transition already animates the page in; skip the CSS entrance then.
  window.addEventListener('pagereveal', event => {
    const transition = event.viewTransition;
    root.classList.toggle('has-vt', Boolean(transition));
    quiet(transition);
    transition?.ready.catch(() => root.classList.remove('has-vt'));
  });
  window.addEventListener('pageswap', event => {
    const transition = event.viewTransition;
    if (!transition) return;
    quiet(transition);
    // Chrome creates the incoming transition before checking the next page's opt-in; when that page refuses
    // snapshots (login, credential hand-off) it rejects a promise no script on either page can reach.
    // Skipping here, on the outgoing side, avoids that. Same-page and Back/Forward visits get no transition either.
    const next = event.activation?.entry?.url ? new URL(event.activation.entry.url) : null;
    const refusesSnapshot = next?.pathname === '/login' || document.querySelector('form[data-submitting][data-no-transition]');
    if (refusesSnapshot || next?.pathname === location.pathname || event.activation?.navigationType === 'traverse') transition.skipTransition();
  });
})();
