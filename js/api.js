/**
 * SatQuery AI - Centralized REST API Service
 */

const API_BASE ='http://satquery-ai-backend-5mg2.onrender.com/api';

const SatQueryAPI = {
  // 1. Health Check
  async checkHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`, { method: 'GET' });
      return await res.json();
    } catch (e) {
      return { status: 'offline', error: e.message };
    }
  },

  // 2. Auth: Register
  async register(email, password, preferred_language = 'en') {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, preferred_language })
    });
    return await res.json();
  },

  // 3. Auth: Login
  async login(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    return await res.json();
  },

  // 4. Auth: Update Language
  async updateLanguage(email, language) {
    try {
      await fetch(`${API_BASE}/auth/update-language`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, language })
      });
    } catch (e) {}
  },

  // 5. Main Multimodal Analysis
  async analyze(formData) {
    const res = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      body: formData
    });
    return await res.json();
  },

  // 6. Preview Location Area & Satellite Scene
  async previewLocation(latitude, longitude) {
    const res = await fetch(`${API_BASE}/preview-location`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ latitude, longitude })
    });
    return await res.json();
  },

  // 7. Coordinate / Location Analysis
  async analyzeLocation(latitude, longitude, query, user_email) {
    const res = await fetch(`${API_BASE}/analyze-location`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ latitude, longitude, query, user_email })
    });
    return await res.json();
  },

  // 7. Get History
  async getHistory(email) {
    const res = await fetch(`${API_BASE}/history?email=${encodeURIComponent(email)}`);
    return await res.json();
  },

  // 8. Get Report JSON
  async getReport(analysisId) {
    const res = await fetch(`${API_BASE}/reports/${analysisId}`);
    return await res.json();
  },

  // 9. Get PDF Download URL
  getPdfUrl(analysisId) {
    return `${API_BASE}/reports/${analysisId}/pdf`;
  }
};

window.SatQueryAPI = SatQueryAPI;
