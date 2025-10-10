(function () {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const apply = () => {
        const theme = mq.matches ? 'dark' : 'light';
        document.documentElement.setAttribute('data-bs-theme', theme);
        // Hint to the browser for built-ins like scrollbars/form controls
        document.documentElement.style.colorScheme = theme;
    };
    apply();
    mq.addEventListener('change', apply);
})();