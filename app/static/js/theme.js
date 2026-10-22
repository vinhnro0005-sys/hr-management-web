// Run before the stylesheet to avoid flashing the wrong theme.
(() => {
  const systemTheme = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  let theme = systemTheme;
  try {
    const saved = localStorage.getItem('hr_theme');
    if (saved === 'light' || saved === 'dark') theme = saved;
  } catch { /* The system preference still works when storage is blocked. */ }
  document.documentElement.dataset.theme = theme;
})();
