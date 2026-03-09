/* ============================================================
   Al-Minār — Main JavaScript
   API integration, search, map, animations, auth, reporting
   ============================================================ */

const API = '/api';

// ============================================================
// Auth — JWT Token Management
// ============================================================
const Auth = {
  getAccess()   { return localStorage.getItem('al_access'); },
  getRefresh()  { return localStorage.getItem('al_refresh'); },
  getUser()     { return JSON.parse(localStorage.getItem('al_user') || 'null'); },

  save(access, refresh, user) {
    localStorage.setItem('al_access', access);
    localStorage.setItem('al_refresh', refresh);
    localStorage.setItem('al_user', JSON.stringify(user));
  },

  clear() {
    localStorage.removeItem('al_access');
    localStorage.removeItem('al_refresh');
    localStorage.removeItem('al_user');
  },

  isLoggedIn() {
    return !!this.getAccess();
  },

  async refreshToken() {
    const refresh = this.getRefresh();
    if (!refresh) return false;
    try {
      const res = await fetch('/api/token/refresh/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      });
      if (!res.ok) { this.clear(); return false; }
      const data = await res.json();
      localStorage.setItem('al_access', data.access);
      if (data.refresh) localStorage.setItem('al_refresh', data.refresh);
      return true;
    } catch { this.clear(); return false; }
  },
};

// ---- Authenticated fetch wrapper ----
async function authFetch(url, options = {}) {
  if (!options.headers) options.headers = {};
  const token = Auth.getAccess();
  if (token) options.headers['Authorization'] = `Bearer ${token}`;
  let res = await fetch(url, options);
  if (res.status === 401 && Auth.getRefresh()) {
    const refreshed = await Auth.refreshToken();
    if (refreshed) {
      options.headers['Authorization'] = `Bearer ${Auth.getAccess()}`;
      res = await fetch(url, options);
    }
  }
  return res;
}

// ---- Helpers ----
async function apiFetch(endpoint, params = {}) {
  const url = new URL(endpoint, window.location.origin);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v);
  });
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

function confidenceBadgeHTML(level) {
  const map = {
    0: { cls: 'c0', icon: 'fas fa-circle', label: 'Community Reported' },
    1: { cls: 'c1', icon: 'fas fa-users', label: 'Community Confirmed' },
    2: { cls: 'c2', icon: 'fas fa-check-circle', label: 'Verified' },
    3: { cls: 'c3', icon: 'fas fa-shield-alt', label: 'Actively Maintained' },
  };
  const info = map[level] || map[0];
  return `<span class="confidence-badge ${info.cls}"><i class="${info.icon}"></i> ${info.label}</span>`;
}

function masjidCardHTML(m) {
  const loc = m.location_record;
  const cr = m.confidence_record;
  const city = loc ? `${loc.city || ''}, ${loc.country || ''}`.replace(/(^,\s*|,\s*$)/g, '') : 'Location unknown';
  const level = cr ? cr.confidenceLevel : 0;
  const desc = m.description || 'No description available.';
  return `
    <div class="col-md-6 col-lg-4 mb-4 fade-up">
      <div class="masjid-card">
        <div class="card-header-band"></div>
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-start mb-2">
            <h5 class="mb-0">${escHTML(m.name)}</h5>
            ${confidenceBadgeHTML(level)}
          </div>
          <div class="card-location">
            <i class="fas fa-map-marker-alt"></i>
            <span>${escHTML(city)}</span>
          </div>
          <p class="card-desc">${escHTML(desc)}</p>
        </div>
        <div class="card-footer-area">
          <small class="text-muted">${m.isActive ? '<i class="fas fa-circle text-success" style="font-size:.5rem"></i> Active' : '<i class="fas fa-circle text-danger" style="font-size:.5rem"></i> Inactive'}</small>
          <a href="/masjid/${m.masjidID}/" class="btn-view">View Details <i class="fas fa-arrow-right"></i></a>
        </div>
      </div>
    </div>`;
}

function escHTML(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}

// ---- Scroll animations ----
function initScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        observer.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.fade-up').forEach(el => observer.observe(el));
}

// ---- Navbar scroll effect ----
function initNavbar() {
  const nav = document.querySelector('.al-navbar');
  if (!nav) return;
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 50);
  });
}

// ---- Hero search ----
function initHeroSearch() {
  const form = document.getElementById('hero-search-form');
  if (!form) return;
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const q = form.querySelector('input').value.trim();
    window.location.href = `/explore/?search=${encodeURIComponent(q)}`;
  });
}

// ---- Featured Masjids (home page) ----
async function loadFeatured() {
  const container = document.getElementById('featured-grid');
  if (!container) return;
  try {
    const data = await apiFetch(`${API}/masjids/`, { page_size: 6, ordering: '-created_at' });
    const masjids = data.results || data;
    container.innerHTML = masjids.map(masjidCardHTML).join('');
    initScrollAnimations();
  } catch (err) {
    container.innerHTML = '<di
// --------------- Explore Page ---------------

var exploreMap = null;
var exploreMarkers = [];

async function initExplore() {
  var grid = document.getElementById('explore-grid');
  if (!grid) return;
  var params = new URLSearchParams(window.location.search);
  var searchInput = document.getElementById('explore-search');
  if (searchInput && params.get('search')) searchInput.value = params.get('search');
  initExploreMap();
  await searchMasjids();
  var searchForm = document.getElementById('explore-search-form');
  if (searchForm) { searchForm.addEventListener('submit', function(e) { e.preventDefault(); searchMasjids(); }); }
  document.querySelectorAll('.filter-chip[data-country]').forEach(function(chip) {
    chip.addEventListener('click', function() {
      document.querySelectorAll('.filter-chip[data-country]').forEach(function(c) { c.classList.remove('active'); });
      chip.classList.add('active'); searchMasjids();
    });
  });
  document.querySelectorAll('.filter-chip[data-confidence]').forEach(function(chip) {
    chip.addEventListener('click', function() { chip.classList.toggle('active'); searchMasjids(); });
  });
}

function initExploreMap() {
  var mapEl = document.getElementById('map-container');
  if (!mapEl || typeof L === 'undefined') return;
  exploreMap = L.map('map-container', { zoomControl: false }).setView([25, 45], 3);
  L.control.zoom({ position: 'topright' }).addTo(exploreMap);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap', maxZoom: 18 }).addTo(exploreMap);
}

function clearMapMarkers() {
  exploreMarkers.forEach(function(m) { exploreMap.removeLayer(m); });
  exploreMarkers = [];
}

async function searchMasjids() {
  var grid = document.getElementById('explore-grid');
  var countEl = document.getElementById('result-count');
  if (!grid) return;
  var search = ''; var searchEl = document.getElementById('explore-search');
  if (searchEl) search = searchEl.value.trim();
  var activeCountry = document.querySelector('.filter-chip[data-country].active');
  var country = activeCountry ? (activeCountry.dataset.country || '') : '';
  var confidenceChips = document.querySelectorAll('.filter-chip[data-confidence].active');
  var confidenceLevels = Array.from(confidenceChips).map(function(c) { return c.dataset.confidence; });
  grid.innerHTML = '<div class="col-12 text-center py-5"><div class="al-spinner"></div></div>';
  try {
    var data = await apiFetch(API + '/masjids/', { search: search, ordering: '-created_at' });
    var masjids = data.results || data;
    var locData = await apiFetch(API + '/location-records/', { country: country || undefined });
    var locations = locData.results || locData;
    var locByMasjid = {};
    locations.forEach(function(l) { locByMasjid[l.masjid] = l; });
    if (country) { masjids = masjids.filter(function(m) { return !!locByMasjid[m.masjidID]; }); }
    masjids.forEach(function(m) { if (!m.location_record && locByMasjid[m.masjidID]) m.location_record = locByMasjid[m.masjidID]; });
    if (confidenceLevels.length > 0) {
      masjids = masjids.filter(function(m) {
        var level = (m.confidence_record && m.confidence_record.confidenceLevel != null) ? m.confidence_record.confidenceLevel : 0;
        return confidenceLevels.indexOf(String(level)) !== -1;
      });
    }
    if (masjids.length === 0) {
      grid.innerHTML = '<div class="col-12 text-center py-5"><i class="fas fa-mosque text-muted" style="font-size:3rem;opacity:.3"></i><p class="text-muted mt-3">No masjids found. Try adjusting your filters.</p></div>';
    } else {
      grid.innerHTML = masjids.map(masjidCardHTML).join('');
    }
    if (countEl) countEl.textContent = masjids.length + ' masjid' + (masjids.length !== 1 ? 's' : '') + ' found';
    if (exploreMap) {
      clearMapMarkers();
      var bounds = [];
      masjids.forEach(function(m) {
        var loc = m.location_record || locByMasjid[m.masjidID];
        if (loc && loc.latitude && loc.longitude) {
          var marker = L.marker([loc.latitude, loc.longitude], {
            icon: L.divIcon({ className: 'al-map-pin', html: '<div style="background:#D4AF37;width:12px;height:12px;border-radius:50%;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,.3)"></div>', iconSize: [12, 12], iconAnchor: [6, 6] })
          }).addTo(exploreMap);
          var level = (m.confidence_record && m.confidence_record.confidenceLevel != null) ? m.confidence_record.confidenceLevel : 0;
          marker.bindPopup('<div style="min-width:180px"><strong>' + escHTML(m.name) + '</strong><br><small>' + escHTML(loc.city || '') + ' ' + escHTML(loc.country || '') + '</small><br>' + confidenceBadgeHTML(level) + '<br><a href="/masjid/' + m.masjidID + '/" style="font-size:.82rem;font-weight:600">View Details &rarr;</a></div>');
          exploreMarkers.push(marker);
          bounds.push([loc.latitude, loc.longitude]);
        }
      });
      if (bounds.length > 0) exploreMap.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
    }
   
// --------------- Detail Page ---------------

async function initDetail() {
  var container = document.getElementById('masjid-detail');
  if (!container) return;
  var id = container.dataset.id;
  if (!id) return;
  try {
    var m = await apiFetch(API + '/masjids/' + id + '/');
    var locData = await apiFetch(API + '/location-records/', { masjid: id });
    var loc = (locData.results || locData)[0] || {};
    document.getElementById('detail-name').textContent = m.name;
    var subParts = [loc.city, loc.country].filter(Boolean);
    var subEl = document.getElementById('detail-sub');
    if (subEl) subEl.textContent = subParts.join(', ') || 'Location not set';
    var imgEl = document.getElementById('detail-img');
    if (imgEl) {
      if (m.imageURL) { imgEl.src = m.imageURL; imgEl.alt = m.name; }
      else { imgEl.src = '/static/img/1.png'; imgEl.alt = 'Default'; }
    }
    var level = (m.confidence_record && m.confidence_record.confidenceLevel != null) ? m.confidence_record.confidenceLevel : 0;
    var badgeEl = document.getElementById('detail-confidence');
    if (badgeEl) badgeEl.innerHTML = confidenceBadgeHTML(level);
    var tbody = document.getElementById('detail-info');
    if (tbody) {
      tbody.innerHTML = '';
      var rows = [
        ['Masjid ID', m.masjidID],
        ['Name', m.name],
        ['Type', m.masjid_type || 'N/A'],
        ['Country', loc.country || 'N/A'],
        ['City', loc.city || 'N/A'],
        ['Address', loc.address || 'N/A'],
        ['Madhab', m.madhab || 'N/A'],
        ['Contact', m.contactInfo || 'N/A'],
        ['Website', m.websiteURL ? '<a href="' + escHTML(m.websiteURL) + '" target="_blank">' + escHTML(m.websiteURL) + '</a>' : 'N/A'],
        ['Added', m.created_at ? new Date(m.created_at).toLocaleDateString() : 'N/A']
      ];
      rows.forEach(function(r) { tbody.innerHTML += '<tr><th>' + r[0] + '</th><td>' + r[1] + '</td></tr>'; });
    }
    var mapEl = document.getElementById('detail-map');
    if (mapEl && typeof L !== 'undefined' && loc.latitude && loc.longitude) {
      var dm = L.map('detail-map', { zoomControl: false }).setView([loc.latitude, loc.longitude], 15);
      L.control.zoom({ position: 'topright' }).addTo(dm);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap', maxZoom: 18 }).addTo(dm);
      L.marker([loc.latitude, loc.longitude], { icon: L.divIcon({ className: 'al-map-pin', html: '<div style="background:#D4AF37;width:16px;height:16px;border-radius:50%;border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,.3)"></div>', iconSize: [16, 16], iconAnchor: [8, 8] }) }).addTo(dm);
    } else if (mapEl) {
      mapEl.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100 text-muted"><div class="text-center"><i class="fas fa-map-marker-alt mb-2" style="font-size:2rem;opacity:.3"></
// --------------- Verify Page ---------------

async function initVerify() {
  var container = document.getElementById('verify-container');
  if (!container) return;
  try {
    var data = await apiFetch(API + '/masjids/', { ordering: '-created_at' });
    var masjids = data.results || data;
    var grid = document.getElementById('verify-grid');
    if (!grid) return;
    if (masjids.length === 0) {
      grid.innerHTML = '<div class="col-12 text-center py-5"><p class="text-muted">No masjids to verify.</p></div>';
      return;
    }
    grid.innerHTML = masjids.map(function(m) {
      var level = (m.confidence_record && m.confidence_record.confidenceLevel != null) ? m.confidence_record.confidenceLevel : 0;
      return '<div class="col-md-6 col-lg-4 mb-4 scroll-reveal">' +
        '<div class="al-card h-100">' +
        '<div class="al-card-body p-4">' +
        '<h5 class="fw-bold mb-2">' + escHTML(m.name) + '</h5>' +
        '<p class="text-muted small mb-3">' + escHTML(m.masjidID) + '</p>' +
        confidenceBadgeHTML(level) +
        '<a href="/masjid/' + m.masjidID + '/" class="btn btn-sm al-btn-primary mt-3">Review &rarr;</a>' +
        '</div></div></div>';
    }).join('');
    initScrollAnimations();
  } catch (err) {
    console.error('verify error', err);
  }
}

// --------------- Report Map ---------------

var reportMap = null;
var reportMarker = null;

function initReportMap() {
  var mapEl = document.getElementById('report-map');
  if (!mapEl || typeof L === 'undefined') return;
  reportMap = L.map('report-map', { zoomControl: false }).setView([25, 45], 3);
  L.control.zoom({ position: 'topright' }).addTo(reportMap);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap', maxZoom: 18 }).addTo(reportMap);
  reportMap.on('click', function(e) {
    var lat = e.latlng.lat.toFixed(6);
    var lng = e.latlng.lng.toFixed(6);
    var latInput = document.getElementById('id_latitude') || document.getElementById('latitude');
    var lngInput = document.getElementById('id_longitude') || document.getElementById('longitude');
    if (latInput) latInput.value = lat;
    if (lngInput) lngInput.value = lng;
    if (reportMarker) { reportMarker.setLatLng(e.latlng); }
    else {
      reportMarker = L.marker(e.latlng, {
        icon: L.divIcon({ className: 'al-map-pin', html: '<div style="background:#D4AF37;width:16px;height:16px;border-radius:50%;border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,.3)"></div>', iconSize: [16, 16], iconAnchor: [8, 8] })
      }).addTo(reportMap);
    }
  });
  setTimeout(function() { reportMap.invalidateSize(); }, 250);
}

// --------------- Init ---------------

document.addEventListener('DOMContentLoaded', function() {
  initNavbar();
  initHeroSearch();
  initScrollAnimations();
  loadFeatured();
  initExplore();
  initDetail();
  initVerify();
  initReportMap();
});
i><p class="mb-0 small">No location data</p></div></div>';
    }
  } catch (err) {
    container.innerHTML = '<div class="text-center text-danger py-5">Error loading masjid details.</div>';
    console.error(err);
  }
}
 initScrollAnimations();
  } catch (err) {
    grid.innerHTML = '<div class="col-12 text-center text-danger py-5">Error loading data.</div>';
    console.error(err);
  }
}
v class="col-12 text-center text-muted py-5">Could not load masjids.</div>';
  }
}

// ---- Explore Page ----
let exploreMap = null;
let exploreMarkers = [];

async function initExplore() {
  const grid = document.getElementById('explore-grid');
  if (!grid) return;

  // Parse URL params
  const params = new URLSearchParams(window.location.search);
  const searchInput = document.getElementById('explore-search');
  if (searchInput && params.get('search')) searchInput.value = params.get('search');

  // Init map
  initExploreMap();

  // Load data
  await searchMasjids();

  // Bind events
  document.getElementById('explore-search-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    searchMasjids();
  });
  document.querySelectorAll('.filter-chip[data-country]').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.filter-chip[data-country]').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      searchMasjids();
    });
  });
  document.querySelectorAll('.filter-chip[data-confidence]').forEach(chip => {
    chip.addEventListener('click', () => {
      chip.classList.toggle('active');
      searchMasjids();
    });
  });
}

function initExploreMap() {
  const mapEl = document.getElementById('map-container');
  if (!mapEl || typeof L === 'undefined') return;
  exploreMap = L.map('map-container', { zoomControl: false }).setView([25, 45], 3);
  L.control.zoom({ position: 'topright' }).addTo(exploreMap);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap',
    maxZoom: 18,
  }).addTo(exploreMap);
}

function clearMapMarkers() {
  exploreMarkers.forEach(m => exploreMap.removeLayer(m));
  exploreMarkers = [];
}

async function searchMasjids() {
  const grid = document.getElementById('explore-grid');
  const countEl = document.getElementById('result-count');
  if (!grid) return;

  // Gather params
  const search = document.getElementById('explore-search')?.value.trim() || '';
  const activeCountry = document.querySelector('.filter-chip[data-country].active');
  const country = activeCountry?.dataset.country || '';
  const confidenceChips = document.querySelectorAll('.filter-chip[data-confidence].active');
  const confidenceLevels = Array.from(confidenceChips).map(c => c.dataset.confidence);

  grid.innerHTML = '<div class="col-12 text-center py-5"><div class="al-spinner"></div></div>';

  try {
    // Fetch masjids
    const data = await apiFetch(`${API}/masjids/`, { search, ordering: '-created_at' });
    let masjids = data.results || data;

    // Fetch locations for map + filtering
    const locData = await apiFetch(`${API}/location-records/`, { country: country || undefined });
    const locations = locData.results || locData;
    const locByMasjid = {};
    locations.forEach(l => { locByMasjid[l.masjid] = l; });

    // Filter by country if set
    if (country) {
      masjids = masjids.filter(m => locByMasjid[m.masjidID]);
    }

    // Attach location data
    masjids.forEach(m => {
      if (!m.location_record && locByMasjid[m.masjidID]) {
        m.location_record = locByMasjid[m.masjidID];
      }
    });

    // Filter by confidence
    if (confidenceLevels.length > 0) {
      masjids = masjids.filter(m => {
        const level = m.confidence_record?.confidenceLevel ?? 0;
        return confidenceLevels.includes(String(level));
      });
    }

    // Render
    if (masjids.length === 0) {
      grid.innerHTML = `
        <div class="col-12 text-center py-5">
          <i class="fas fa-mosque text-muted" style="font-size:3rem;opacity:.3"></i>
          <p class="text-muted mt-3">No masjids found. Try adjusting your filters.</p>
        </div>`;
    } else {
      grid.innerHTML = masjids.map(masjidCardHTML).join('');
    }
    if (countEl) countEl.textContent = `${masjids.length} masjid${masjids.length !== 1 ? 's' : ''} found`;

    // Map pins
    if (exploreMap) {
      clearMapMarkers();
      const bounds = [];
      masjids.forEach(m => {
        const loc = m.location_record || locByMasjid[m.masjidID];
        if (loc && loc.latitude && loc.longitude) {
          const marker = L.marker([loc.latitude, loc.longitude], {
            icon: L.divIcon({
              className: 'al-map-pin',
              html: `<div style="background:#D4AF37;width:12px;height:12px;border-radius:50%;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,.3)"></div>`,
              iconSize: [12, 12],
              iconAnchor: [6, 6],
            })
          }).addTo(exploreMap);
          const level = m.confidence_record?.confidenceLevel ?? 0;
          marker.bindPopup(`
            <div style="min-width:180px">
              <strong>${escHTML(m.name)}</strong><br>
              <small>${escHTML(loc.city || '')} ${escHTML(loc.country || '')}</small><br>
              ${confidenceBadgeHTML(level)}
              <br><a href="/masjid/${m.masjidID}/" style="font-size:.82rem;font-weight:600">View Details →</a>
            </div>
          `);
          exploreMarkers.push(marker);
          bounds.push([loc.latitude, loc.longitude]);
        }
      });
      if (bounds.length > 0) {
        exploreMap.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
      }
    }

    initScrollAnimations();
  } catch (err) {
    grid.innerHTML = '<div class="col-12 text-center text-danger py-5">Error loading data.</div>';
    console.error(err);
  }
}

// ---- Masjid Detail Page ----
async function initDetail() {
  const el = document.getElementById('detail-data');
  if (!el) return;
  const masjidID = el.dataset.masjidId;
  if (!masjidID) return;

  try {
    // Load prayer times
    const ptData = await apiFetch(`${API}/masjids/${masjidID}/prayer_times/`);
    const prayerContainer = document.getElementById('prayer-times-list');
    if (prayerContainer && ptData.length > 0) {
      const latest = ptData[0]; // most recent record
      const prayers = latest.prayers || [];
      if (prayers.length > 0) {
        const prayerIcons = { fajr: 'fa-sun', dhuhr: 'fa-sun', asr: 'fa-cloud-sun', maghrib: 'fa-moon', isha: 'fa-star' };
        prayerContainer.innerHTML = prayers.map(p => {
          const name = p.prayer?.name || 'Unknown';
          const icon = prayerIcons[name] || 'fa-clock';
          return `
            <div class="prayer-time-row">
              <span class="prayer-name"><i class="fas ${icon} text-accent"></i> ${name.charAt(0).toUpperCase() + name.slice(1)}</span>
              <div class="prayer-times">
                ${p.adhan_time ? `<span class="time-chip"><i class="fas fa-volume-up"></i> ${p.adhan_time}</span>` : ''}
                ${p.iqama_time ? `<span class="time-chip iqama"><i class="fas fa-users"></i> ${p.iqama_time}</span>` : ''}
              </div>
            </div>`;
        }).join('');
        document.getElementById('prayer-record-date').textContent = `Date: ${latest.date || 'N/A'} · Model: ${latest.modelType || 'N/A'}`;
      } else {
        prayerContainer.innerHTML = '<p class="text-muted text-center py-3">No prayer times recorded yet.</p>';
      }
    } else if (prayerContainer) {
      prayerContainer.innerHTML = '<p class="text-muted text-center py-3">No prayer times recorded yet.</p>';
    }

    // Load signals
    const sigData = await apiFetch(`${API}/masjids/${masjidID}/signals/`);
    const sigContainer = document.getElementById('signals-list');
    if (sigContainer) {
      if (sigData.length > 0) {
        sigContainer.innerHTML = sigData.slice(0, 10).map(s => `
          <div class="d-flex align-items-center gap-3 py-2 border-bottom">
            <div style="width:36px;height:36px;border-radius:10px;background:rgba(184,134,11,.1);display:flex;align-items:center;justify-content:center">
              <i class="fas fa-broadcast-tower text-primary-brand" style="font-size:.8rem"></i>
            </div>
            <div class="flex-fill">
              <div class="fw-semibold" style="font-size:.85rem">${escHTML(s.signalType)}</div>
              <small class="text-muted">${escHTML(s.sourceType)} · ${new Date(s.created_at).toLocaleDateString()}</small>
            </div>
          </div>
        `).join('');
      } else {
        sigContainer.innerHTML = '<p class="text-muted text-center py-3">No signals yet.</p>';
      }
    }

    // Load badges
    const badgeData = await apiFetch(`${API}/masjids/${masjidID}/badges/`);
    const badgeContainer = document.getElementById('badges-list');
    if (badgeContainer) {
      if (badgeData.length > 0) {
        badgeContainer.innerHTML = badgeData.map(b => `
          <div class="d-flex align-items-center gap-3 py-2 border-bottom">
            <div class="verified-shield ${b.isActive && !b.isRevoked ? 'gold' : ''}" style="width:50px;height:56px;font-size:.8rem">
              <i class="fas ${b.isActive && !b.isRevoked ? 'fa-certificate' : 'fa-times-circle'}"></i>
              <span class="shield-label" style="font-size:.45rem">${b.isActive && !b.isRevoked ? 'Valid' : 'Revoked'}</span>
            </div>
            <div class="flex-fill">
              <div class="fw-semibold" style="font-size:.85rem">Badge #${String(b.badgeID).slice(0,8)}</div>
              <small class="text-muted">Issued: ${new Date(b.issueDate).toLocaleDateString()}</small>
              ${b.expiryDate ? `<br><small class="text-muted">Expires: ${new Date(b.expiryDate).toLocaleDateString()}</small>` : ''}
            </div>
          </div>
        `).join('');
      } else {
        badgeContainer.innerHTML = '<p class="text-muted text-center py-3">No badges issued.</p>';
      }
    }

    // Detail map
    const mapEl = document.getElementById('detail-map');
    const latEl = document.getElementById('detail-lat');
    const lngEl = document.getElementById('detail-lng');
    if (mapEl && latEl && lngEl && typeof L !== 'undefined') {
      const lat = parseFloat(latEl.value);
      const lng = parseFloat(lngEl.value);
      if (!isNaN(lat) && !isNaN(lng)) {
        const map = L.map('detail-map', { zoomControl: false, scrollWheelZoom: false }).setView([lat, lng], 14);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© OpenStreetMap',
        }).addTo(map);
        L.marker([lat, lng]).addTo(map);
      }
    }

  } catch (err) {
    console.error('Detail load error:', err);
  }
}

// ---- Verify Page ----
async function initVerify() {
  const card = document.getElementById('verify-card');
  if (!card) return;
  const token = card.dataset.token;
  if (!token) return;

  try {
    const data = await apiFetch(`${API}/verify/${token}/`);
    const iconEl = card.querySelector('.verify-icon');
    const titleEl = card.querySelector('.verify-title');
    const bodyEl = card.querySelector('.verify-body');

    if (data.valid) {
      iconEl.className = 'verify-icon valid';
      iconEl.innerHTML = '<i class="fas fa-check"></i>';
      titleEl.textContent = 'Badge Verified';
      titleEl.className = 'verify-title text-success fw-bold fs-4';
      bodyEl.innerHTML = `
        <p class="mb-2">This badge is <strong>active and valid</strong>.</p>
        <hr>
        <p class="mb-1"><strong>Masjid:</strong> ${escHTML(data.masjid)}</p>
        <p class="mb-1"><strong>Issued:</strong> ${data.issuedAt ? new Date(data.issuedAt).toLocaleDateString() : 'N/A'}</p>
        <p class="mb-0"><strong>Expires:</strong> ${data.expiresAt ? new Date(data.expiresAt).toLocaleDateString() : 'No expiry'}</p>
        <a href="/masjid/${data.masjidID}/" class="btn btn-al-primary mt-3">View Masjid</a>
      `;
    } else {
      iconEl.className = 'verify-icon invalid';
      iconEl.innerHTML = '<i class="fas fa-times"></i>';
      titleEl.textContent = 'Badge Invalid';
      titleEl.className = 'verify-title text-danger fw-bold fs-4';
      bodyEl.innerHTML = `<p>This badge is <strong>no longer valid</strong>. It may have been revoked or expired.</p>`;
    }
  } catch (err) {
    const iconEl = card.querySelector('.verify-icon');
    const titleEl = card.querySelector('.verify-title');
    const bodyEl = card.querySelector('.verify-body');
    iconEl.className = 'verify-icon invalid';
    iconEl.innerHTML = '<i class="fas fa-question"></i>';
    titleEl.textContent = 'Badge Not Found';
    titleEl.className = 'verify-title text-danger fw-bold fs-4';
    bodyEl.innerHTML = '<p>No badge was found with this token.</p>';
  }
}

// ============================================================
// Auth UI — Update navbar based on login state
// ============================================================
function updateAuthUI() {
  const loggedOut = document.querySelectorAll('.auth-logged-out');
  const loggedIn  = document.querySelectorAll('.auth-logged-in');
  const nameEl    = document.querySelector('.user-display-name');
  const roleEl    = document.getElementById('nav-user-role');

  if (Auth.isLoggedIn()) {
    loggedOut.forEach(el => el.classList.add('d-none'));
    loggedIn.forEach(el => el.classList.remove('d-none'));
    const user = Auth.getUser();
    if (nameEl && user) nameEl.textContent = user.username;
    if (roleEl && user) roleEl.textContent = user.accountType === 'masjid_admin' ? 'Masjid Admin' : 'Regular User';
  } else {
    loggedOut.forEach(el => el.classList.remove('d-none'));
    loggedIn.forEach(el => el.classList.add('d-none'));
  }
}

function initLogout() {
  const btn = document.getElementById('nav-logout-btn');
  if (!btn) return;
  btn.addEventListener('click', (e) => {
    e.preventDefault();
    Auth.clear();
    window.location.href = '/';
  });
}

// ============================================================
// Login Page
// ============================================================
function initLogin() {
  const form = document.getElementById('login-form');
  if (!form) return;

  // If already logged in, redirect
  if (Auth.isLoggedIn()) {
    window.location.href = '/';
    return;
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const alert = document.getElementById('login-alert');
    const btn = document.getElementById('login-btn');
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;

    // Show loading
    btn.querySelector('.btn-text').classList.add('d-none');
    btn.querySelector('.btn-loading').classList.remove('d-none');
    btn.disabled = true;
    alert.classList.add('d-none');

    try {
      const res = await fetch('/api/token/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Invalid username or password.');
      }

      const data = await res.json();

      // Try to get user info
      let userInfo = { username, accountType: 'user' };
      try {
        const userRes = await fetch(`${API}/users/${username}/`, {
          headers: { 'Authorization': `Bearer ${data.access}` },
        });
        if (userRes.ok) {
          const uData = await userRes.json();
          userInfo = { ...userInfo, ...uData };
        }
      } catch {}

      // Check if user is a masjid admin
      try {
        const adminRes = await fetch(`${API}/masjid-admins/?user=${username}`, {
          headers: { 'Authorization': `Bearer ${data.access}` },
        });
        if (adminRes.ok) {
          const adminData = await adminRes.json();
          const results = adminData.results || adminData;
          if (results.length > 0) {
            userInfo.accountType = 'masjid_admin';
          }
        }
      } catch {}

      Auth.save(data.access, data.refresh, userInfo);
      window.location.href = '/';

    } catch (err) {
      alert.className = 'auth-alert alert-danger';
      alert.innerHTML = `<i class="fas fa-exclamation-circle me-2"></i>${escHTML(err.message)}`;
      alert.classList.remove('d-none');
    } finally {
      btn.querySelector('.btn-text').classList.remove('d-none');
      btn.querySelector('.btn-loading').classList.add('d-none');
      btn.disabled = false;
    }
  });
}

// ============================================================
// Register Page
// ============================================================
function initRegister() {
  const form = document.getElementById('register-form');
  if (!form) return;

  // If already logged in, redirect
  if (Auth.isLoggedIn()) {
    window.location.href = '/';
    return;
  }

  // Account type toggle
  document.querySelectorAll('.type-option').forEach(option => {
    option.addEventListener('click', () => {
      document.querySelectorAll('.type-option').forEach(o => o.classList.remove('active'));
      option.classList.add('active');
      const type = option.dataset.type;
      const adminFields = document.getElementById('admin-fields');
      if (type === 'masjid_admin') {
        adminFields.classList.remove('d-none');
      } else {
        adminFields.classList.add('d-none');
      }
    });
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const alert = document.getElementById('register-alert');
    const btn = document.getElementById('register-btn');
    const username = document.getElementById('reg-username').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    const confirm = document.getElementById('reg-confirm').value;
    const accountType = document.querySelector('input[name="accountType"]:checked')?.value || 'user';

    // Validate
    if (password !== confirm) {
      alert.className = 'auth-alert alert-danger';
      alert.innerHTML = '<i class="fas fa-exclamation-circle me-2"></i>Passwords do not match.';
      alert.classList.remove('d-none');
      return;
    }

    // Show loading
    btn.querySelector('.btn-text').classList.add('d-none');
    btn.querySelector('.btn-loading').classList.remove('d-none');
    btn.disabled = true;
    alert.classList.add('d-none');

    try {
      // Create user via API
      const res = await fetch(`${API}/users/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        const msg = Object.values(errData).flat().join(' ') || 'Registration failed.';
        throw new Error(msg);
      }

      // Auto-login after registration
      const tokenRes = await fetch('/api/token/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (tokenRes.ok) {
        const tokenData = await tokenRes.json();
        const userInfo = { username, email, accountType };
        Auth.save(tokenData.access, tokenData.refresh, userInfo);

        // Success message + redirect
        alert.className = 'auth-alert alert-success';
        alert.innerHTML = '<i class="fas fa-check-circle me-2"></i>Account created! Redirecting...';
        alert.classList.remove('d-none');

        setTimeout(() => {
          if (accountType === 'masjid_admin') {
            window.location.href = '/report/';
          } else {
            window.location.href = '/';
          }
        }, 1200);
      } else {
        // Registration succeeded but auto-login failed
        alert.className = 'auth-alert alert-success';
        alert.innerHTML = '<i class="fas fa-check-circle me-2"></i>Account created! Please log in.';
        alert.classList.remove('d-none');
        setTimeout(() => { window.location.href = '/login/'; }, 1500);
      }

    } catch (err) {
      alert.className = 'auth-alert alert-danger';
      alert.innerHTML = `<i class="fas fa-exclamation-circle me-2"></i>${escHTML(err.message)}`;
      alert.classList.remove('d-none');
    } finally {
      btn.querySelector('.btn-text').classList.remove('d-none');
      btn.querySelector('.btn-loading').classList.add('d-none');
      btn.disabled = false;
    }
  });
}

// ============================================================
// Report Page
// ============================================================

// Countries list (loaded from API or fallback)
const COUNTRIES = [
  "AF - Islamic Republic of Afghanistan","AL - Republic of Albania","DZ - People's Democratic Republic of Algeria",
  "EG - Arab Republic of Egypt","ID - Republic of Indonesia","IN - Republic of India",
  "IQ - Republic of Iraq","IR - Islamic Republic of Iran","JO - Hashemite Kingdom of Jordan",
  "KW - State of Kuwait","LB - Lebanese Republic","MY - Malaysia",
  "MA - Kingdom of Morocco","NG - Federal Republic of Nigeria","OM - Sultanate of Oman",
  "PK - Islamic Republic of Pakistan","QA - State of Qatar","SA - Kingdom of Saudi Arabia",
  "SG - Republic of Singapore","TR - Republic of Türkiye","AE - United Arab Emirates",
  "UK - United Kingdom of Great Britain and Northern Ireland","US - United States of America",
  "YE - Republic of Yemen","BD - People's Republic of Bangladesh","BH - Kingdom of Bahrain",
  "CA - Canada","DE - Federal Republic of Germany","FR - French Republic",
  "AU - Commonwealth of Australia","NZ - New Zealand","ZA - Republic of South Africa",
];

let reportMap = null;

function initReport() {
  const wrapper = document.getElementById('report-form-wrapper');
  const authWall = document.getElementById('report-auth-wall');
  if (!wrapper || !authWall) return;

  const user = Auth.getUser();

  if (!Auth.isLoggedIn()) {
    authWall.classList.remove('d-none');
    wrapper.classList.add('d-none');
    return;
  }

  // User is logged in
  authWall.classList.add('d-none');
  wrapper.classList.remove('d-none');

  const isAdmin = user?.accountType === 'masjid_admin';

  // Show role-specific info
  if (isAdmin) {
    document.getElementById('report-admin-info')?.classList.remove('d-none');
    document.getElementById('pdf-upload-section')?.classList.remove('d-none');
  } else {
    document.getElementById('report-user-info')?.classList.remove('d-none');
  }

  // Populate country dropdown
  const countrySelect = document.getElementById('report-country');
  if (countrySelect && countrySelect.options.length <= 1) {
    COUNTRIES.sort().forEach(c => {
      const opt = document.createElement('option');
      opt.value = c;
      opt.textContent = c;
      countrySelect.appendChild(opt);
    });
  }

  // Init map
  initReportMap();

  // PDF drop zone
  initPDFUpload();

  // Load pending masjids
  if (!isAdmin) {
    loadPendingMasjids();
  }

  // Form submit
  const form = document.getElementById('report-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    await submitMasjidReport(isAdmin);
  });
}

function initReportMap() {
  const mapEl = document.getElementById('report-map');
  if (!mapEl || typeof L === 'undefined') return;

  reportMap = L.map('report-map', { zoomControl: true }).setView([25, 45], 3);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap',
    maxZoom: 18,
  }).addTo(reportMap);

  let marker = null;
  reportMap.on('click', (e) => {
    const { lat, lng } = e.latlng;
    document.getElementById('report-lat').value = lat.toFixed(6);
    document.getElementById('report-lng').value = lng.toFixed(6);
    if (marker) reportMap.removeLayer(marker);
    marker = L.marker([lat, lng]).addTo(reportMap);
  });
}

function initPDFUpload() {
  const dropZone = document.getElementById('pdf-drop-zone');
  const fileInput = document.getElementById('report-pdf');
  if (!dropZone || !fileInput) return;

  dropZone.addEventListener('click', () => fileInput.click());
  dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.borderColor = 'var(--accent)'; });
  dropZone.addEventListener('dragleave', () => { dropZone.style.borderColor = ''; });
  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = '';
    if (e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      showPDFName(e.dataTransfer.files[0].name);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      showPDFName(fileInput.files[0].name);
    }
  });
}

function showPDFName(name) {
  const el = document.getElementById('pdf-file-name');
  const text = document.getElementById('pdf-name-text');
  if (el && text) {
    text.textContent = name;
    el.classList.remove('d-none');
  }
}

async function submitMasjidReport(isAdmin) {
  const alert = document.getElementById('report-alert');
  const btn = document.getElementById('report-btn');
  const name = document.getElementById('report-name').value.trim();
  const desc = document.getElementById('report-desc').value.trim();
  const city = document.getElementById('report-city').value.trim();
  const country = document.getElementById('report-country').value;
  const region = document.getElementById('report-region').value.trim();
  const lat = parseFloat(document.getElementById('report-lat').value);
  const lng = parseFloat(document.getElementById('report-lng').value);

  if (!name || !city || !country || isNaN(lat) || isNaN(lng)) {
    alert.className = 'auth-alert alert-danger';
    alert.innerHTML = '<i class="fas fa-exclamation-circle me-2"></i>Please fill in all required fields.';
    alert.classList.remove('d-none');
    return;
  }

  // Show loading
  btn.querySelector('.btn-text').classList.add('d-none');
  btn.querySelector('.btn-loading').classList.remove('d-none');
  btn.disabled = true;
  alert.classList.add('d-none');

  try {
    // 1. Create the masjid
    // Regular users: isActive = false (needs 3 signals)
    // Masjid admins: isActive = true (direct add)
    const masjidRes = await authFetch(`${API}/masjids/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        description: desc || null,
        isActive: isAdmin,
      }),
    });

    if (!masjidRes.ok) {
      const errData = await masjidRes.json().catch(() => ({}));
      const msg = Object.values(errData).flat().join(' ') || 'Failed to create masjid.';
      throw new Error(msg);
    }

    const masjid = await masjidRes.json();

    // 2. Create location record
    const locRes = await authFetch(`${API}/location-records/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        masjid: masjid.masjidID,
        latitude: lat,
        longitude: lng,
        city,
        country,
        region: region || null,
      }),
    });

    if (!locRes.ok) {
      console.warn('Location record creation failed:', await locRes.text());
    }

    // 3. Create initial signal
    const user = Auth.getUser();
    const signalBody = {
      masjid: masjid.masjidID,
      signalType: isAdmin ? 'ADMIN_VERIFY' : 'ACTIVE',
      sourceType: isAdmin ? 'ADMIN' : 'USER',
      description: isAdmin ? 'Masjid admin direct submission' : 'Community report — initial signal',
    };
    if (user?.username) signalBody.user = user.username;

    await authFetch(`${API}/signals/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(signalBody),
    });

    // 4. If admin, create masjid-admin link
    if (isAdmin && user?.username) {
      await authFetch(`${API}/masjid-admins/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user: user.username,
          masjid: masjid.masjidID,
          verifiedIdentity: false,
        }),
      });
    }

    // Success
    alert.className = 'auth-alert alert-success';
    if (isAdmin) {
      alert.innerHTML = `<i class="fas fa-check-circle me-2"></i>Masjid "<strong>${escHTML(name)}</strong>" added successfully! It is now live on the site.`;
    } else {
      alert.innerHTML = `<i class="fas fa-check-circle me-2"></i>Masjid "<strong>${escHTML(name)}</strong>" reported! It will appear on the site once 3 community members verify it.`;
    }
    alert.classList.remove('d-none');
    document.getElementById('report-form').reset();

  } catch (err) {
    alert.className = 'auth-alert alert-danger';
    alert.innerHTML = `<i class="fas fa-exclamation-circle me-2"></i>${escHTML(err.message)}`;
    alert.classList.remove('d-none');
  } finally {
    btn.querySelector('.btn-text').classList.remove('d-none');
    btn.querySelector('.btn-loading').classList.add('d-none');
    btn.disabled = false;
  }
}

// ---- Pending Masjids (for community verification) ----
async function loadPendingMasjids() {
  const section = document.getElementById('pending-section');
  const grid = document.getElementById('pending-grid');
  if (!section || !grid) return;

  try {
    // Fetch inactive masjids (pending verification)
    const data = await apiFetch(`${API}/masjids/`, { isActive: false, ordering: '-created_at' });
    const masjids = data.results || data;

    if (masjids.length === 0) return;

    section.classList.remove('d-none');
    grid.innerHTML = masjids.slice(0, 6).map(m => {
      const loc = m.location_record;
      const city = loc ? `${loc.city || ''}, ${loc.country || ''}`.replace(/(^,\s*|,\s*$)/g, '') : 'Unknown';
      return `
        <div class="col-md-6 col-lg-4 mb-3">
          <div class="pending-card">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <h6 class="fw-bold mb-0">${escHTML(m.name)}</h6>
              <span class="confidence-badge c0"><i class="fas fa-clock"></i> Pending</span>
            </div>
            <div class="card-location mb-2">
              <i class="fas fa-map-marker-alt"></i>
              <span>${escHTML(city)}</span>
            </div>
            <p class="text-muted mb-2" style="font-size:.82rem">${escHTML(m.description || 'No description.')}</p>
            <button class="btn btn-al-primary btn-sm w-100 verify-pending-btn" data-masjid-id="${m.masjidID}">
              <i class="fas fa-check me-1"></i>I Can Verify This Masjid
            </button>
          </div>
        </div>`;
    }).join('');

    // Bind verify buttons
    grid.querySelectorAll('.verify-pending-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const masjidId = btn.dataset.masjidId;
        const user = Auth.getUser();
        btn.disabled = true;
        btn.innerHTML = '<div class="al-spinner" style="width:16px;height:16px;margin:0 auto;border-width:2px"></div>';

        try {
          await authFetch(`${API}/signals/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              masjid: masjidId,
              signalType: 'ACTIVE',
              sourceType: 'USER',
              description: 'Community verification signal',
              user: user?.username || null,
            }),
          });
          btn.className = 'btn btn-success btn-sm w-100';
          btn.innerHTML = '<i class="fas fa-check me-1"></i>Verified — Thank You!';
        } catch (err) {
          btn.className = 'btn btn-outline-danger btn-sm w-100';
          btn.innerHTML = '<i class="fas fa-times me-1"></i>Failed — Try Again';
          btn.disabled = false;
        }
      });
    });

    initScrollAnimations();
  } catch (err) {
    console.error('Failed to load pending masjids:', err);
  }
}

// ---- Init ----
document.addEventListener('DOMContentLoaded', () => {
  updateAuthUI();
  initLogout();
  initNavbar();
  initHeroSearch();
  initScrollAnimations();
  loadFeatured();
  initExplore();
  initDetail();
  initVerify();
  initLogin();
  initRegister();
  initReport();
});
