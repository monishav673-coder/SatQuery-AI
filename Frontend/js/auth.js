/**
 * SatQuery AI - Authentication & Session Handler
 */

const SatQueryAuth = {
  getCurrentUser() {
    try {
      const userStr = localStorage.getItem('satquery_user');
      return userStr ? JSON.parse(userStr) : null;
    } catch (e) {
      return null;
    }
  },

  setCurrentUser(user) {
    if (user) {
      localStorage.setItem('satquery_user', JSON.stringify(user));
      if (user.preferred_language) {
        window.SatQueryI18n.setLanguage(user.preferred_language);
      }
    } else {
      localStorage.removeItem('satquery_user');
    }
    this.updateAuthUI();
  },

  isLoggedIn() {
    return !!this.getCurrentUser();
  },

  logout() {
    localStorage.removeItem('satquery_user');
    this.updateAuthUI();
    window.location.reload();
  },

  updateAuthUI() {
    const user = this.getCurrentUser();
    const loginSection = document.getElementById('login-section');
    const mainApp = document.getElementById('main-app');
    const userEmailBadge = document.getElementById('user-email-badge');

    if (user) {
      if (loginSection) loginSection.classList.add('hidden');
      if (mainApp) mainApp.classList.remove('hidden');
      if (userEmailBadge) userEmailBadge.textContent = user.email;
    } else {
      if (loginSection) loginSection.classList.remove('hidden');
      if (mainApp) mainApp.classList.add('hidden');
    }
  }
};

window.SatQueryAuth = SatQueryAuth;
