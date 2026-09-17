/**
 * SatQuery AI - Main Dashboard Controller & UI Orchestrator
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize i18n
  window.SatQueryI18n.applyTranslations();
  
  // Initialize Auth state
  window.SatQueryAuth.updateAuthUI();
  
  // Initialize App Modules
  initHealthCheck();
  initAuthEvents();
  initNavigation();
  initModeSelection();
  initFileUploads();
  initSampleLoaders();
  initQuerySuggestions();
  initLocationModule();
  initEvidenceToggle();
  initAnalysisExecution();
});

let currentMode = 'single'; // 'single' | 'optical_sar' | 'multitemporal' | 'location'
let currentFiles = {
  single: null,
  optical: null,
  sar: null,
  before: null,
  after: null
};
let lastAnalysisResult = null;
let leafletMap = null;
let locationMarker = null;
let isLocationPreviewLoading = false;
let locationDebounceTimer = null;

// 1. Health Check
async function initHealthCheck() {
  const statusPill = document.getElementById('system-status-pill');
  const statusText = document.getElementById('system-status-text');
  
  try {
    const data = await window.SatQueryAPI.checkHealth();
    if (data && data.status === 'online') {
      if (statusPill) statusPill.classList.remove('offline');
      if (statusText) statusText.textContent = window.SatQueryI18n.t('system_online');
    } else {
      throw new Error('Offline');
    }
  } catch (e) {
    if (statusPill) statusPill.classList.add('offline');
    if (statusText) statusText.textContent = window.SatQueryI18n.t('system_offline');
  }
}

// 2. Auth Events
function initAuthEvents() {
  const loginForm = document.getElementById('login-form');
  const authToggleLink = document.getElementById('auth-toggle-link');
  const authTitle = document.getElementById('auth-title');
  const authSubmitBtn = document.getElementById('auth-submit-btn');
  const authAlert = document.getElementById('auth-alert');
  const logoutBtn = document.getElementById('btn-logout');
  
  let isRegistering = false;

  if (authToggleLink) {
    authToggleLink.addEventListener('click', (e) => {
      e.preventDefault();
      isRegistering = !isRegistering;
      if (isRegistering) {
        authTitle.textContent = window.SatQueryI18n.t('register_btn');
        authSubmitBtn.textContent = window.SatQueryI18n.t('register_btn');
        authToggleLink.textContent = window.SatQueryI18n.t('switch_to_login');
      } else {
        authTitle.textContent = window.SatQueryI18n.t('login_title');
        authSubmitBtn.textContent = window.SatQueryI18n.t('login_btn');
        authToggleLink.textContent = window.SatQueryI18n.t('switch_to_register');
      }
      if (authAlert) authAlert.classList.add('hidden');
    });
  }

  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('auth-email').value.trim();
      const password = document.getElementById('auth-password').value;
      const lang = window.SatQueryI18n.getCurrentLanguage();

      if (!email || !password) {
        showAuthAlert(window.SatQueryI18n.t('error_fill_fields'), 'error');
        return;
      }

      authSubmitBtn.disabled = true;
      authSubmitBtn.textContent = "Verifying...";

      try {
        let res;
        if (isRegistering) {
          res = await window.SatQueryAPI.register(email, password, lang);
        } else {
          res = await window.SatQueryAPI.login(email, password);
        }

        if (res.success && res.user) {
          window.SatQueryAuth.setCurrentUser(res.user);
          showAuthAlert("Success! Entering portal...", "success");
          setTimeout(() => {
            window.SatQueryAuth.updateAuthUI();
          }, 600);
        } else {
          showAuthAlert(res.error || window.SatQueryI18n.t('error_invalid_login'), 'error');
        }
      } catch (err) {
        showAuthAlert("Network connection error. Check backend server.", 'error');
      } finally {
        authSubmitBtn.disabled = false;
        authSubmitBtn.textContent = isRegistering ? window.SatQueryI18n.t('register_btn') : window.SatQueryI18n.t('login_btn');
      }
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      window.SatQueryAuth.logout();
    });
  }

  // Language Selectors
  document.querySelectorAll('.lang-selector').forEach(sel => {
    sel.addEventListener('change', (e) => {
      const chosenLang = e.target.value;
      window.SatQueryI18n.setLanguage(chosenLang);
      const user = window.SatQueryAuth.getCurrentUser();
      if (user) {
        window.SatQueryAPI.updateLanguage(user.email, chosenLang);
      }
    });
  });
}

function showAuthAlert(msg, type = 'error') {
  const alertEl = document.getElementById('auth-alert');
  if (!alertEl) return;
  alertEl.textContent = msg;
  alertEl.className = `alert-box alert-${type}`;
  alertEl.classList.remove('hidden');
}

// 3. Navigation View Switching
function initNavigation() {
  const navBtns = document.querySelectorAll('[data-view-target]');
  const views = document.querySelectorAll('.app-view');

  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetViewId = btn.getAttribute('data-view-target');
      
      navBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      views.forEach(v => v.classList.add('hidden'));
      const targetView = document.getElementById(targetViewId);
      if (targetView) targetView.classList.remove('hidden');

      if (targetViewId === 'view-history') {
        loadHistory();
      }
    });
  });
}

// 4. Mode Selection
function initModeSelection() {
  const modeCards = document.querySelectorAll('.mode-card');
  const latlonBanner = document.getElementById('latlon-mode-banner');

  modeCards.forEach(card => {
    card.addEventListener('click', () => {
      const mode = card.getAttribute('data-mode');
      setAnalysisMode(mode);
    });
  });

  if (latlonBanner) {
    latlonBanner.addEventListener('click', () => {
      setAnalysisMode('location');
    });
  }
}

function setAnalysisMode(mode) {
  currentMode = mode;
  
  // Highlight mode cards
  document.querySelectorAll('.mode-card').forEach(c => {
    if (c.getAttribute('data-mode') === mode) {
      c.classList.add('active');
    } else {
      c.classList.remove('active');
    }
  });

  const latlonBanner = document.getElementById('latlon-mode-banner');
  if (latlonBanner) {
    if (mode === 'location') latlonBanner.classList.add('active');
    else latlonBanner.classList.remove('active');
  }

  // Toggle upload container sections
  const singleSection = document.getElementById('upload-section-single');
  const optSarSection = document.getElementById('upload-section-optical-sar');
  const multiSection = document.getElementById('upload-section-multitemporal');
  const locationSection = document.getElementById('upload-section-location');

  if (singleSection) singleSection.classList.toggle('hidden', mode !== 'single');
  if (optSarSection) optSarSection.classList.toggle('hidden', mode !== 'optical_sar');
  if (multiSection) multiSection.classList.toggle('hidden', mode !== 'multitemporal');
  if (locationSection) {
    locationSection.classList.toggle('hidden', mode !== 'location');
    if (mode === 'location') {
      setTimeout(() => {
        ensureMapInitialized();
      }, 100);
    }
  }
}

// 5. File Uploads & Previews
function initFileUploads() {
  setupDropzone('single-image-input', 'single-dropzone', 'single-preview', 'single');
  setupDropzone('optical-image-input', 'optical-dropzone', 'optical-preview', 'optical');
  setupDropzone('sar-image-input', 'sar-dropzone', 'sar-preview', 'sar');
  setupDropzone('before-image-input', 'before-dropzone', 'before-preview', 'before');
  setupDropzone('after-image-input', 'after-dropzone', 'after-preview', 'after');
}

function setupDropzone(inputId, dropzoneId, previewId, fileKey) {
  const input = document.getElementById(inputId);
  const dropzone = document.getElementById(dropzoneId);
  const preview = document.getElementById(previewId);

  if (!input || !dropzone || !preview) return;

  // File input change
  input.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleFileSelected(file, fileKey, dropzone, preview);
  });

  // Drag and Drop
  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const file = dt.files[0];
    if (file) handleFileSelected(file, fileKey, dropzone, preview);
  });
}

function handleFileSelected(file, fileKey, dropzone, preview) {
  currentFiles[fileKey] = file;
  
  const reader = new FileReader();
  reader.onload = (e) => {
    const imgEl = preview.querySelector('img');
    const metaEl = preview.querySelector('.preview-meta');
    
    if (imgEl) imgEl.src = e.target.result;
    if (metaEl) {
      const sizeKb = Math.round(file.size / 1024);
      metaEl.textContent = `${file.name} (${sizeKb} KB)`;
    }

    dropzone.classList.add('hidden');
    preview.classList.remove('hidden');
  };
  reader.readAsDataURL(file);
}

function removeFile(fileKey, inputId, dropzoneId, previewId) {
  currentFiles[fileKey] = null;
  const input = document.getElementById(inputId);
  const dropzone = document.getElementById(dropzoneId);
  const preview = document.getElementById(previewId);

  if (input) input.value = '';
  if (preview) preview.classList.add('hidden');
  if (dropzone) dropzone.classList.remove('hidden');
}

window.removeUploadedFile = removeFile;

// 6. Sample Quick-Loaders
function initSampleLoaders() {
  document.querySelectorAll('[data-load-sample]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const sampleType = btn.getAttribute('data-load-sample');
      btn.disabled = true;
      btn.textContent = "Loading sample...";

      try {
        if (sampleType === 'single') {
          await loadSampleFile('/samples/single_sample.jpg', 'single_satellite_scene.jpg', 'single', 'single-dropzone', 'single-preview');
        } else if (sampleType === 'optical_sar') {
          await loadSampleFile('/samples/optical_sample.jpg', 'sentinel2_optical_tile.jpg', 'optical', 'optical-dropzone', 'optical-preview');
          await loadSampleFile('/samples/sar_sample.jpg', 'sentinel1_sar_intensity.jpg', 'sar', 'sar-dropzone', 'sar-preview');
        } else if (sampleType === 'multitemporal') {
          await loadSampleFile('/samples/before_sample.jpg', 't1_before_flood_development.jpg', 'before', 'before-dropzone', 'before-preview');
          await loadSampleFile('/samples/after_sample.jpg', 't2_after_flood_development.jpg', 'after', 'after-dropzone', 'after-preview');
        }
      } catch (e) {
        alert("Failed to load sample image: " + e.message);
      } finally {
        btn.disabled = false;
        btn.textContent = window.SatQueryI18n.t('load_sample_btn');
      }
    });
  });
}

async function loadSampleFile(url, filename, fileKey, dropzoneId, previewId) {
  const resp = await fetch(url);
  const blob = await resp.blob();
  const file = new File([blob], filename, { type: 'image/jpeg' });
  const dropzone = document.getElementById(dropzoneId);
  const preview = document.getElementById(previewId);
  handleFileSelected(file, fileKey, dropzone, preview);
}

// 7. Query Suggestions
function initQuerySuggestions() {
  document.querySelectorAll('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const queryInput = document.getElementById('nl-query-input');
      if (queryInput) {
        queryInput.value = chip.textContent.trim();
        queryInput.focus();
      }
    });
  });
}

// 8. Location Module: Leaflet Map, Live Area Geocoding & Satellite Scene Preview
function initLocationModule() {
  const latInput = document.getElementById('lat-input');
  const lonInput = document.getElementById('lon-input');
  const previewBtn = document.getElementById('btn-preview-location');
  const presetChips = document.querySelectorAll('.location-chip');

  // 1. Preset chips
  presetChips.forEach(chip => {
    chip.addEventListener('click', () => {
      presetChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');

      const lat = parseFloat(chip.getAttribute('data-lat'));
      const lon = parseFloat(chip.getAttribute('data-lon'));

      if (latInput) latInput.value = lat;
      if (lonInput) lonInput.value = lon;

      updateMapAndPreview(lat, lon);
    });
  });

  // 2. Preview button click
  if (previewBtn) {
    previewBtn.addEventListener('click', () => {
      const lat = parseFloat(latInput.value.trim());
      const lon = parseFloat(lonInput.value.trim());
      if (isNaN(lat) || isNaN(lon)) {
        alert("Please enter valid numeric coordinates for Latitude and Longitude.");
        return;
      }
      updateMapAndPreview(lat, lon);
    });
  }

  // 3. Input change with debounce
  [latInput, lonInput].forEach(inp => {
    if (!inp) return;
    inp.addEventListener('input', () => {
      clearTimeout(locationDebounceTimer);
      locationDebounceTimer = setTimeout(() => {
        const lat = parseFloat(latInput.value.trim());
        const lon = parseFloat(lonInput.value.trim());
        if (!isNaN(lat) && !isNaN(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
          updateMapAndPreview(lat, lon, false);
        }
      }, 700);
    });
  });

  // Initial fetch for default location (Coimbatore)
  fetchLocationAreaPreview(10.9601, 76.9500);
}

function ensureMapInitialized() {
  const mapContainer = document.getElementById('location-map');
  if (!mapContainer || typeof L === 'undefined') return;

  const latInput = document.getElementById('lat-input');
  const lonInput = document.getElementById('lon-input');
  const initLat = parseFloat(latInput ? latInput.value : 10.9601) || 10.9601;
  const initLon = parseFloat(lonInput ? lonInput.value : 76.9500) || 76.9500;

  if (!leafletMap) {
    leafletMap = L.map('location-map', {
      center: [initLat, initLon],
      zoom: 15,
      zoomControl: true
    });

    // Satellite base tile layer (Esri World Imagery)
    const esriSatellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
      maxZoom: 19
    }).addTo(leafletMap);

    // OpenStreetMap alternative
    const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19
    });

    L.control.layers({
      "Satellite Imagery": esriSatellite,
      "Street Map": osmLayer
    }, null, { position: 'topright' }).addTo(leafletMap);

    // Custom Draggable Marker
    locationMarker = L.marker([initLat, initLon], {
      draggable: true
    }).addTo(leafletMap);

    locationMarker.on('dragend', function (e) {
      const position = locationMarker.getLatLng();
      if (latInput) latInput.value = position.lat.toFixed(4);
      if (lonInput) lonInput.value = position.lng.toFixed(4);
      fetchLocationAreaPreview(position.lat, position.lng);
    });

    leafletMap.on('click', function (e) {
      const { lat, lng } = e.latlng;
      locationMarker.setLatLng([lat, lng]);
      if (latInput) latInput.value = lat.toFixed(4);
      if (lonInput) lonInput.value = lng.toFixed(4);
      fetchLocationAreaPreview(lat, lng);
    });
  } else {
    leafletMap.invalidateSize();
    leafletMap.setView([initLat, initLon], 15);
    if (locationMarker) locationMarker.setLatLng([initLat, initLon]);
  }
}

function updateMapAndPreview(lat, lon, moveMap = true) {
  if (leafletMap && moveMap) {
    leafletMap.setView([lat, lon], 15);
    if (locationMarker) locationMarker.setLatLng([lat, lon]);
  }
  fetchLocationAreaPreview(lat, lon);
}

async function fetchLocationAreaPreview(lat, lon) {
  if (isLocationPreviewLoading) return;
  isLocationPreviewLoading = true;

  const spinner = document.getElementById('scene-loading-spinner');
  const tileImg = document.getElementById('location-scene-tile-img');
  const locNameEl = document.getElementById('loc-display-name');
  const locCoordsEl = document.getElementById('loc-coords-badge');
  const locProviderEl = document.getElementById('loc-provider-badge');
  const locStatusPill = document.getElementById('loc-preview-status');
  const locStatusText = document.getElementById('loc-preview-status-text');

  if (spinner) spinner.classList.remove('hidden');
  if (locStatusText) locStatusText.textContent = "Retrieving Area Data...";

  try {
    const data = await window.SatQueryAPI.previewLocation(lat, lon);
    if (data && data.success) {
      const loc = data.location || {};
      const tile = data.tile || {};

      if (locNameEl) locNameEl.textContent = loc.display_name || `Area (${lat.toFixed(4)}, ${lon.toFixed(4)})`;
      if (locCoordsEl) locCoordsEl.textContent = `${lat.toFixed(4)}° N, ${lon.toFixed(4)}° E`;
      if (locProviderEl) locProviderEl.textContent = `🛰️ ${tile.provider || 'Esri World Imagery'} (${tile.resolution || '~1.2m/px'})`;
      
      if (tileImg) {
        if (tile.data_uri) {
          tileImg.src = tile.data_uri;
        } else if (tile.tile_url) {
          tileImg.src = tile.tile_url;
        }
      }

      if (locStatusText) locStatusText.textContent = "Satellite Scene Ready";
      if (locStatusPill) locStatusPill.classList.remove('offline');
    }
  } catch (err) {
    if (locStatusText) locStatusText.textContent = "Preview Fetch Error";
    if (locStatusPill) locStatusPill.classList.add('offline');
  } finally {
    if (spinner) spinner.classList.add('hidden');
    isLocationPreviewLoading = false;
  }
}

// 9. Visual Evidence Comparison Toggle
function initEvidenceToggle() {
  const btnOverlay = document.getElementById('toggle-view-overlay');
  const btnRaw = document.getElementById('toggle-view-raw');
  const btnSplit = document.getElementById('toggle-view-split');
  const wrapper = document.getElementById('evidence-images-wrapper');
  const rawFrame = document.getElementById('evidence-raw-frame');

  if (!btnOverlay || !btnRaw || !btnSplit || !wrapper) return;

  const setActiveBtn = (activeBtn) => {
    [btnOverlay, btnRaw, btnSplit].forEach(b => b.classList.remove('active'));
    activeBtn.classList.add('active');
  };

  btnOverlay.addEventListener('click', () => {
    setActiveBtn(btnOverlay);
    wrapper.className = 'evidence-image-container view-single';
    const overlayFrame = wrapper.querySelector('.evidence-frame-overlay');
    if (overlayFrame) overlayFrame.classList.remove('hidden');
    if (rawFrame) rawFrame.classList.add('hidden');
  });

  btnRaw.addEventListener('click', () => {
    setActiveBtn(btnRaw);
    wrapper.className = 'evidence-image-container view-single';
    const overlayFrame = wrapper.querySelector('.evidence-frame-overlay');
    if (overlayFrame) overlayFrame.classList.add('hidden');
    if (rawFrame) rawFrame.classList.remove('hidden');
  });

  btnSplit.addEventListener('click', () => {
    setActiveBtn(btnSplit);
    wrapper.className = 'evidence-image-container view-split';
    const overlayFrame = wrapper.querySelector('.evidence-frame-overlay');
    if (overlayFrame) overlayFrame.classList.remove('hidden');
    if (rawFrame) rawFrame.classList.remove('hidden');
  });
}

// 10. Main Agentic AI Analysis Execution
function initAnalysisExecution() {
  const analyzeBtn = document.getElementById('btn-analyze-main');
  if (!analyzeBtn) return;

  analyzeBtn.addEventListener('click', async () => {
    const query = (document.getElementById('nl-query-input').value || '').trim() || 'Identify buildings, water bodies and agricultural areas.';
    const user = window.SatQueryAuth.getCurrentUser();
    const userEmail = user ? user.email : 'scientist@isro.gov.in';

    // Validation
    if (currentMode === 'single' && !currentFiles.single) {
      alert(window.SatQueryI18n.t('error_upload_required'));
      return;
    }
    if (currentMode === 'optical_sar' && (!currentFiles.optical || !currentFiles.sar)) {
      alert("Please upload both Optical and SAR satellite images.");
      return;
    }
    if (currentMode === 'multitemporal' && (!currentFiles.before || !currentFiles.after)) {
      alert("Please upload both Before and After satellite scenes.");
      return;
    }

    // UI Loading state
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = `<span>⏳</span> ${window.SatQueryI18n.t('analyzing_text')}`;

    const progressCard = document.getElementById('agent-progress-card');
    const stepsList = document.getElementById('agent-steps-list');
    const resultsContainer = document.getElementById('results-section');

    if (resultsContainer) resultsContainer.classList.add('hidden');
    if (progressCard) progressCard.classList.remove('hidden');
    if (stepsList) stepsList.innerHTML = '';

    // Agentic task progression animation
    const liveSteps = [
      "Query intent parsed & decomposed into specialist sub-tasks",
      "Selecting specialist models (Vision-Language, Land-cover, Building detector)",
      "Preprocessing satellite radiometry and geospatial channels",
      "Running multi-spectral feature inference & spatial orientation",
      "Generating high-resolution visual evidence overlays",
      "Evaluating multi-factor confidence and synthesizing response"
    ];

    let stepIdx = 0;
    const stepInterval = setInterval(() => {
      if (stepIdx < liveSteps.length && stepsList) {
        const li = document.createElement('li');
        li.className = 'step-item active';
        li.innerHTML = `<span class="step-icon">⚡</span> <span>${liveSteps[stepIdx]}</span>`;
        stepsList.appendChild(li);
        stepIdx++;
      }
    }, 450);

    try {
      let res;
      if (currentMode === 'location') {
        const lat = document.getElementById('lat-input').value.trim();
        const lon = document.getElementById('lon-input').value.trim();
        if (!lat || !lon) {
          clearInterval(stepInterval);
          alert("Please enter valid Latitude and Longitude.");
          analyzeBtn.disabled = false;
          analyzeBtn.textContent = window.SatQueryI18n.t('analyze_btn');
          if (progressCard) progressCard.classList.add('hidden');
          return;
        }
        res = await window.SatQueryAPI.analyzeLocation(lat, lon, query, userEmail);
      } else {
        const formData = new FormData();
        formData.append('mode', currentMode);
        formData.append('query', query);
        formData.append('user_email', userEmail);

        if (currentMode === 'single') {
          formData.append('image', currentFiles.single);
        } else if (currentMode === 'optical_sar') {
          formData.append('optical', currentFiles.optical);
          formData.append('sar', currentFiles.sar);
        } else if (currentMode === 'multitemporal') {
          formData.append('before', currentFiles.before);
          formData.append('after', currentFiles.after);
        }

        res = await window.SatQueryAPI.analyze(formData);
      }

      clearInterval(stepInterval);

      if (res && res.success) {
        lastAnalysisResult = res;
        renderResults(res);
      } else {
        alert("Analysis Error: " + (res.error || "Unknown server error."));
      }

    } catch (err) {
      clearInterval(stepInterval);
      alert("Network or Server error during analysis: " + err.message);
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtn.innerHTML = `<span>🚀</span> ${window.SatQueryI18n.t('analyze_btn')}`;
      if (progressCard) progressCard.classList.add('hidden');
    }
  });
}

// 11. Render Analysis Results
function renderResults(data) {
  const resultsContainer = document.getElementById('results-section');
  if (!resultsContainer) return;

  const res = data.result || {};
  const conf = res.confidence || {};
  const bldg = res.buildings || {};
  const water = res.water_bodies || {};
  const agri = res.agriculture || {};
  const lc = res.land_cover || {};
  const agent = data.agent || {};
  const locMeta = data.location_metadata;

  // 1. Location Banner (if location mode)
  const locBanner = document.getElementById('res-location-banner');
  if (locBanner) {
    if (data.mode === 'location' && locMeta) {
      locBanner.classList.remove('hidden');
      const locNameEl = document.getElementById('res-location-name');
      const locCoordsEl = document.getElementById('res-location-coords');
      const locProviderEl = document.getElementById('res-location-provider');

      if (locNameEl) locNameEl.textContent = locMeta.display_name || `Area (${locMeta.latitude}, ${locMeta.longitude})`;
      if (locCoordsEl) locCoordsEl.textContent = `${parseFloat(locMeta.latitude).toFixed(4)}° N, ${parseFloat(locMeta.longitude).toFixed(4)}° E`;
      if (locProviderEl) locProviderEl.textContent = `🛰️ ${locMeta.provider || 'Esri World Imagery'} (${locMeta.resolution || '~1.2m/px'})`;
    } else {
      locBanner.classList.add('hidden');
    }
  }

  // 2. Metrics Cards
  const confScoreEl = document.getElementById('res-conf-score');
  const confLevelEl = document.getElementById('res-conf-level');
  const bldgCountEl = document.getElementById('res-bldg-count');
  const waterCountEl = document.getElementById('res-water-count');
  const waterPctEl = document.getElementById('res-water-pct');
  const agriPctEl = document.getElementById('res-agri-pct');

  if (confScoreEl) {
    confScoreEl.textContent = `${conf.score || 0}/100`;
    confScoreEl.className = `metric-val ${conf.score >= 80 ? 'confidence-high' : conf.score >= 65 ? 'confidence-mod' : 'confidence-low'}`;
  }
  if (confLevelEl) confLevelEl.textContent = `${conf.level || 'N/A'} Confidence`;
  if (bldgCountEl) bldgCountEl.textContent = bldg.count !== undefined ? bldg.count : 0;
  if (waterCountEl) waterCountEl.textContent = water.count !== undefined ? water.count : 0;
  if (waterPctEl) waterPctEl.textContent = `${water.coverage_percentage || 0}%`;
  if (agriPctEl) agriPctEl.textContent = `${agri.coverage_percentage || 0}%`;

  // 3. AI Interpretation
  const answerEl = document.getElementById('res-ai-answer');
  if (answerEl) answerEl.textContent = res.answer || "No interpretation generated.";

  // 4. Visual Evidence Overlay & Raw Image
  const evidenceImg = document.getElementById('res-evidence-img');
  const rawImg = document.getElementById('res-raw-img');
  const evidenceDownloadBtn = document.getElementById('btn-download-evidence');

  if (evidenceImg && res.evidence && res.evidence.data_uri) {
    evidenceImg.src = res.evidence.data_uri;
    if (evidenceDownloadBtn) {
      evidenceDownloadBtn.onclick = () => {
        const a = document.createElement('a');
        a.href = res.evidence.data_uri;
        a.download = `SatQuery_Evidence_${data.analysis_id}.jpg`;
        a.click();
      };
    }
  }

  if (rawImg) {
    if (res.evidence && res.evidence.raw_data_uri) {
      rawImg.src = res.evidence.raw_data_uri;
    } else if (res.evidence && res.evidence.raw_image_url) {
      rawImg.src = res.evidence.raw_image_url;
    } else {
      // Fallback to location tile preview image if available
      const locTileImg = document.getElementById('location-scene-tile-img');
      if (locTileImg && locTileImg.src) {
        rawImg.src = locTileImg.src;
      }
    }
  }

  // 5. Land Cover Bars
  renderLandCoverBars(lc);

  // 6. Directions Matrix
  renderDirections(bldg, water, agri);

  // 7. Multitemporal Change Box (if applicable)
  const changeCard = document.getElementById('res-change-card');
  if (changeCard) {
    if (data.mode === 'multitemporal' && res.change_detection) {
      changeCard.classList.remove('hidden');
      const chg = res.change_detection;
      document.getElementById('res-chg-total').textContent = `${chg.change_percentage || 0}%`;
      document.getElementById('res-chg-urban').textContent = `${chg.breakdown?.urban_expansion_pct || 0}%`;
      document.getElementById('res-chg-water').textContent = `${chg.breakdown?.water_expansion_pct || 0}%`;
      document.getElementById('res-chg-veg').textContent = `${chg.breakdown?.vegetation_land_alteration_pct || 0}%`;
    } else {
      changeCard.classList.add('hidden');
    }
  }

  // 8. Optical-SAR Fusion Box (if applicable)
  const fusionCard = document.getElementById('res-fusion-card');
  if (fusionCard) {
    if (data.mode === 'optical_sar' && res.fusion) {
      fusionCard.classList.remove('hidden');
      const f = res.fusion;
      document.getElementById('res-fusion-agree').textContent = `${f.cross_modal_agreement_pct || 0}%`;
      document.getElementById('res-fusion-water').textContent = `${f.fused_water_coverage_pct || 0}%`;
      const insightsList = document.getElementById('res-fusion-insights');
      if (insightsList) {
        insightsList.innerHTML = (f.fusion_insights || []).map(i => `<li>${i}</li>`).join('');
      }
    } else {
      fusionCard.classList.add('hidden');
    }
  }

  // 9. Agent Execution Steps
  const stepsList = document.getElementById('res-agent-steps');
  if (stepsList && agent.execution_steps) {
    stepsList.innerHTML = agent.execution_steps.map(s => `<li class="step-item done"><span class="step-icon">✓</span> <span>${s}</span></li>`).join('');
  }

  // 10. Download Report Button
  const downloadPdfBtn = document.getElementById('btn-download-pdf');
  if (downloadPdfBtn) {
    downloadPdfBtn.onclick = () => {
      window.open(window.SatQueryAPI.getPdfUrl(data.analysis_id), '_blank');
    };
  }

  resultsContainer.classList.remove('hidden');
  resultsContainer.scrollIntoView({ behavior: 'smooth' });
}

function renderLandCoverBars(lc) {
  const container = document.getElementById('res-lc-bars');
  if (!container) return;

  const categories = [
    { key: 'agriculture', label: 'Agriculture / Vegetation', color: '#22c55e', val: lc.agriculture || 0 },
    { key: 'built_up', label: 'Built-up / Urban', color: '#ef4444', val: lc.built_up || 0 },
    { key: 'water', label: 'Water Bodies', color: '#3b82f6', val: lc.water || 0 },
    { key: 'bare_land', label: 'Bare Soil / Barren', color: '#eab308', val: lc.bare_land || 0 },
    { key: 'other', label: 'Other / Infrastructure', color: '#94a3b8', val: lc.other || 0 }
  ];

  container.innerHTML = categories.map(c => `
    <div class="lc-row">
      <div class="lc-info">
        <span>${c.label}</span>
        <strong>${c.val}%</strong>
      </div>
      <div class="lc-progress-track">
        <div class="lc-progress-fill" style="width: ${c.val}%; background: ${c.color};"></div>
      </div>
    </div>
  `).join('');
}

function renderDirections(bldg, water, agri) {
  const dirBody = document.getElementById('res-directions-body');
  if (!dirBody) return;

  const dirs = ["North", "North-East", "East", "South-East", "South", "South-West", "West", "North-West", "Center"];
  const bldgDist = bldg.spatial_distribution || {};
  const waterDist = water.spatial_distribution || {};
  const dominantAgri = (agri.dominant_regions || []).join(', ');

  dirBody.innerHTML = dirs.map(d => {
    const bCount = bldgDist[d] || 0;
    const wCount = waterDist[d] || 0;
    const isAgriDom = dominantAgri.includes(d);

    return `
      <tr>
        <td><strong>${d}</strong></td>
        <td>${bCount > 0 ? `${bCount} building(s)` : '<span style="color:#64748b;">-</span>'}</td>
        <td>${wCount > 0 ? `${wCount} water body` : '<span style="color:#64748b;">-</span>'}</td>
        <td>${isAgriDom ? '<span style="color:#22c55e;">Dominant Canopy</span>' : '<span style="color:#64748b;">-</span>'}</td>
      </tr>
    `;
  }).join('');
}

// 12. Load History View
async function loadHistory() {
  const user = window.SatQueryAuth.getCurrentUser();
  const email = user ? user.email : 'scientist@isro.gov.in';
  const tableBody = document.getElementById('history-table-body');
  const emptyNotice = document.getElementById('history-empty-notice');

  if (!tableBody) return;
  tableBody.innerHTML = '<tr><td colspan="6" style="text-align:center;">Loading history records...</td></tr>';

  try {
    const res = await window.SatQueryAPI.getHistory(email);
    if (res.success && res.history && res.history.length > 0) {
      if (emptyNotice) emptyNotice.classList.add('hidden');
      tableBody.innerHTML = res.history.map(item => `
        <tr>
          <td><strong>${item.id}</strong></td>
          <td><span class="mode-select-btn" style="text-transform:uppercase;">${item.mode}</span></td>
          <td>${item.query.length > 40 ? item.query.substring(0, 40) + '...' : item.query}</td>
          <td><span class="status-badge" style="background:rgba(0,242,254,0.1); border-color:var(--primary-cyan); color:var(--primary-cyan);">${item.confidence_score}/100</span></td>
          <td>${item.created_at}</td>
          <td>
            <a href="${window.SatQueryAPI.getPdfUrl(item.id)}" target="_blank" class="btn-secondary" style="padding:0.25rem 0.6rem; font-size:0.75rem; text-decoration:none;">📄 PDF</a>
          </td>
        </tr>
      `).join('');
    } else {
      tableBody.innerHTML = '';
      if (emptyNotice) emptyNotice.classList.remove('hidden');
    }
  } catch (e) {
    tableBody.innerHTML = `<tr><td colspan="6" style="color:#f87171;">Failed to load history: ${e.message}</td></tr>`;
  }
}
