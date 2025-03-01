// theme.js - Gerenciamento de tema claro/escuro
document.addEventListener('DOMContentLoaded', function() {
  // Verificar tema salvo
  const savedTheme = localStorage.getItem('theme');
  
  // Aplicar tema salvo ou padrão
  if (savedTheme) {
      document.documentElement.setAttribute('data-theme', savedTheme);
  } else {
      // Verificar preferência do sistema
      const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const defaultTheme = prefersDarkScheme ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', defaultTheme);
      localStorage.setItem('theme', defaultTheme);
  }
  
  // Configurar alternador de tema
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
      themeToggle.addEventListener('click', function() {
          const currentTheme = document.documentElement.getAttribute('data-theme');
          const newTheme = currentTheme === 'light' ? 'dark' : 'light';
          
          document.documentElement.setAttribute('data-theme', newTheme);
          localStorage.setItem('theme', newTheme);
      });
  }
});