// MediBook - Main JavaScript

document.addEventListener('DOMContentLoaded', function () {
  // ---- Navbar scroll effect ----
  const navbar = document.getElementById('navbar');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 20) {
      navbar?.classList.add('scrolled');
    } else {
      navbar?.classList.remove('scrolled');
    }
  });

  // ---- Mobile hamburger ----
  const hamburger = document.getElementById('hamburger');
  const navLinks = document.querySelector('.nav-links');
  hamburger?.addEventListener('click', () => {
    navLinks?.classList.toggle('open');
  });

  // ---- Auto-dismiss alerts ----
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateX(100%)';
      setTimeout(() => alert.remove(), 300);
    }, 5000);
  });

  // ---- Notification count polling ----
  function updateNotifCount() {
    fetch('/notifications/count/')
      .then(r => r.json())
      .then(data => {
        const badge = document.getElementById('notifCount');
        if (badge) {
          if (data.count > 0) {
            badge.textContent = data.count;
            badge.style.display = 'inline';
          } else {
            badge.style.display = 'none';
          }
        }
      })
      .catch(() => {});
  }

  // Messaging count polling
  function updateMsgCount() {
    fetch('/messaging/unread/')
      .then(r => r.json())
      .then(data => {
        const badge = document.getElementById('msgCount');
        if (badge) {
          if (data.count > 0) {
            badge.textContent = data.count;
            badge.style.display = 'inline';
          } else {
            badge.style.display = 'none';
          }
        }
      })
      .catch(() => {});
  }

  if (document.getElementById('msgBell')) {
    updateMsgCount();
    setInterval(updateMsgCount, 30000);
  }

  if (document.getElementById('notifBell')) {
    updateNotifCount();
    setInterval(updateNotifCount, 30000);
  }

  // ---- Hero search redirect ----
  const heroSearch = document.getElementById('heroSearch');
  const heroSearchBtn = document.getElementById('heroSearchBtn');
  if (heroSearchBtn && heroSearch) {
    heroSearchBtn.addEventListener('click', () => {
      const val = heroSearch.value.trim();
      if (val) {
        window.location.href = `/doctors/?search=${encodeURIComponent(val)}`;
      }
    });
    heroSearch.addEventListener('keydown', e => {
      if (e.key === 'Enter') heroSearchBtn.click();
    });
  }

  // ---- Slot selection for booking ----
  document.querySelectorAll('.slot-btn:not(.booked)').forEach(btn => {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('selected'));
      this.classList.add('selected');
      const slotInput = document.getElementById('slotInput');
      if (slotInput) slotInput.value = this.dataset.slotId;
      const slotDisplay = document.getElementById('selectedSlot');
      if (slotDisplay) slotDisplay.textContent = this.dataset.display || this.textContent;
    });
  });

  // ---- Dynamic slots by date ----
  const dateSelect = document.getElementById('dateSelect');
  if (dateSelect) {
    dateSelect.addEventListener('change', function () {
      const doctorId = this.dataset.doctorId;
      const date = this.value;
      if (!doctorId || !date) return;

      const slotsContainer = document.getElementById('slotsContainer');
      slotsContainer.innerHTML = '<div class="spinner"></div>';

      fetch(`/schedules/slots/${doctorId}/?date=${date}`)
        .then(r => r.json())
        .then(data => {
          if (!data.slots.length) {
            slotsContainer.innerHTML = '<p class="text-muted text-center" style="padding:1rem">Aucun créneau disponible pour cette date.</p>';
            return;
          }
          slotsContainer.innerHTML = '<div class="slots-grid">' +
            data.slots.map(s => `
              <button type="button" class="slot-btn"
                data-slot-id="${s.id}"
                data-display="${date} à ${s.start}"
                onclick="selectSlot(this)">
                ${s.start}
              </button>
            `).join('') + '</div>';
        })
        .catch(() => {
          slotsContainer.innerHTML = '<p class="text-muted">Erreur de chargement.</p>';
        });
    });
  }

  // ---- Smooth scroll ----
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // ---- Star rating visual ----
  initStarRating();
});

function selectSlot(btn) {
  document.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  const slotInput = document.getElementById('slotInput');
  if (slotInput) slotInput.value = btn.dataset.slotId;
  const slotDisplay = document.getElementById('selectedSlot');
  if (slotDisplay) slotDisplay.textContent = btn.dataset.display;
}

function initStarRating() {
  const ratingInputs = document.querySelectorAll('.star-rating-input input[type="radio"]');
  ratingInputs.forEach(input => {
    input.addEventListener('change', function () {
      const stars = this.closest('.star-rating-input').querySelectorAll('label');
      const val = parseInt(this.value);
      stars.forEach((s, i) => {
        s.style.color = (stars.length - i) <= val ? 'var(--accent-orange)' : 'var(--gray-200)';
      });
    });
  });
}

// ---- AI Chat ----
const aiChat = {
  container: null,
  input: null,

  init() {
    this.container = document.getElementById('chatWindow');
    this.input = document.getElementById('chatInput');
    const sendBtn = document.getElementById('chatSend');
    if (sendBtn) {
      sendBtn.addEventListener('click', () => this.send());
    }
    if (this.input) {
      this.input.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.send();
        }
      });
    }
  },

  addMessage(text, type = 'bot') {
    if (!this.container) return;
    const div = document.createElement('div');
    div.className = `chat-message chat-message-${type}`;
    div.innerHTML = text;
    this.container.appendChild(div);
    this.container.scrollTop = this.container.scrollHeight;
  },

  send() {
    if (!this.input) return;
    const text = this.input.value.trim();
    if (!text) return;

    this.addMessage(text, 'user');
    this.input.value = '';

    // Loading indicator
    const loadingId = 'loading-' + Date.now();
    this.container.insertAdjacentHTML('beforeend',
      `<div class="chat-message chat-message-bot" id="${loadingId}">
        <div class="spinner" style="margin:0;width:20px;height:20px;border-width:2px;"></div>
      </div>`
    );
    this.container.scrollTop = this.container.scrollHeight;

    fetch('/ai/api/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ symptoms: text })
    })
      .then(r => r.json())
      .then(data => {
        document.getElementById(loadingId)?.remove();
        this.renderResult(data);
      })
      .catch(() => {
        document.getElementById(loadingId)?.remove();
        this.addMessage('Une erreur est survenue. Veuillez réessayer.', 'bot');
      });
  },

  renderResult(data) {
    const urgencyClass = `urgency-${data.urgency}`;
    const urgencyIcon = data.urgency === 'high' ? '🚨' : data.urgency === 'medium' ? '⚠️' : '✅';

    let html = `
      <div class="chat-result">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem">
          <span style="font-size:2rem">${data.specialty_icon || '🏥'}</span>
          <div>
            <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:800">
              ${data.specialty}
            </div>
            <div style="color:rgba(255,255,255,0.6);font-size:0.8rem">
              Confiance: ${data.confidence}%
            </div>
          </div>
        </div>
        <p style="color:rgba(255,255,255,0.8);font-size:0.875rem;margin-bottom:1rem">
          ${data.message}
        </p>
    `;

    if (data.alternatives && data.alternatives.length) {
      html += `<div style="font-size:0.8rem;color:rgba(255,255,255,0.5);margin-bottom:0.75rem">
        Alternatives: ${data.alternatives.map(a => `${a.name} (${a.score}%)`).join(', ')}
      </div>`;
    }

    html += `<div class="urgency-indicator ${urgencyClass}">
      ${urgencyIcon} Niveau d'urgence: <strong>${data.urgency_label}</strong>
    </div>`;

    if (data.recommended_doctors && data.recommended_doctors.length) {
      html += `<div style="margin-top:1rem">
        <div style="font-size:0.8rem;color:rgba(255,255,255,0.5);margin-bottom:0.5rem;text-transform:uppercase;letter-spacing:0.05em">Médecins recommandés</div>
        ${data.recommended_doctors.map(d => `
          <a href="/doctors/${d.id}/" style="display:flex;align-items:center;gap:10px;padding:0.6rem;background:rgba(255,255,255,0.05);border-radius:8px;margin-bottom:4px;text-decoration:none;color:white;transition:background 0.2s;">
            <span>👨‍⚕️</span>
            <div>
              <div style="font-size:0.875rem;font-weight:600">${d.name}</div>
              <div style="font-size:0.75rem;color:rgba(255,255,255,0.5)">⭐ ${d.rating} · ${d.experience} ans d'expérience</div>
            </div>
          </a>
        `).join('')}
      </div>`;
    }

    html += `</div>`;
    this.addMessage(html, 'bot');
  }
};

function getCookie(name) {
  const val = document.cookie.split(';').map(c => c.trim())
    .find(c => c.startsWith(name + '='));
  return val ? decodeURIComponent(val.split('=')[1]) : '';
}

// Init AI chat if on AI page
if (document.getElementById('chatWindow')) {
  aiChat.init();
}
