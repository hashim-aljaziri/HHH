/**
 * QURRA Boutique - Main JavaScript Entry Point
 * Handles frontend interactivity, cart management, and UI enhancements
 */

// Import CSS (processed by webpack)
import '../css/main.css';

// Global utilities
const QurraApp = {
  version: '1.0.0',
  init() {
    console.log('🎀 QURRA Boutique App Initialized');
    this.setupEventListeners();
    this.setupThemeToggle();
  },
  
  setupEventListeners() {
    // Add any global event listeners here
    document.addEventListener('DOMContentLoaded', () => {
      console.log('DOM ready');
    });
  },
  
  setupThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;
    
    themeToggle.addEventListener('change', (e) => {
      const theme = e.target.checked ? 'dark' : 'light';
      document.documentElement.classList.toggle('dark', e.target.checked);
      localStorage.setItem('qurra-theme', theme);
    });
  },
};

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => QurraApp.init());
} else {
  QurraApp.init();
}

// Export for use in other scripts
export default QurraApp;
