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
  window.addEventListener('pageswap', event => quiet(event.viewTransition));
})();
