// app/static/js/theme.js
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    
    // Verificar preferência salva
    const savedTheme = localStorage.getItem('theme');
    
    // Verificar preferência do sistema
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Aplicar tema inicial
    if (savedTheme === 'dark' || (!savedTheme && prefersDarkScheme.matches)) {
      document.documentElement.setAttribute('data-theme', 'dark');
    }
    
    // Alternar tema ao clicar no botão
    if (themeToggle) {
      themeToggle.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        
        if (currentTheme === 'dark') {
          document.documentElement.removeAttribute('data-theme');
          localStorage.setItem('theme', 'light');
        } else {
          document.documentElement.setAttribute('data-theme', 'dark');
          localStorage.setItem('theme', 'dark');
        }
      });
    }
  });