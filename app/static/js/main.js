/* ═══════════════════════════════════════════════════════════
   نجوم التعلم — main.js
   ═══════════════════════════════════════════════════════════ */

/* ── Auto-dismiss flash messages ─────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => el.style.opacity = '0', 4000);
    setTimeout(() => el.remove(), 4400);
  });
});

/* ── Mobile nav toggle ────────────────────────────────────── */
const navToggle = document.getElementById('navToggle');
const navLinks  = document.querySelector('.nav-links');
if (navToggle && navLinks) {
  navToggle.addEventListener('click', () => navLinks.classList.toggle('open'));
}

/* ── Password visibility toggle ──────────────────────────── */
function togglePw(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const isText = input.type === 'text';
  input.type = isText ? 'password' : 'text';
  const icon  = btn.querySelector('i');
  if (icon) { icon.className = isText ? 'fas fa-eye' : 'fas fa-eye-slash'; }
}

/* ── Animate progress bars on page load ──────────────────── */
function animateProgressBars() {
  document.querySelectorAll('.progress-fill, .xp-fill').forEach(el => {
    const width = el.style.width;
    el.style.width = '0%';
    requestAnimationFrame(() => {
      setTimeout(() => { el.style.width = width; }, 100);
    });
  });
}
document.addEventListener('DOMContentLoaded', animateProgressBars);

/* ── Admin: form confirm on delete ───────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('form[data-confirm]').forEach(form => {
    form.addEventListener('submit', e => {
      if (!confirm(form.dataset.confirm)) e.preventDefault();
    });
  });
});

/* ── XP bar animation ────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.xp-fill').forEach(el => {
    el.style.transition = 'width 1.2s cubic-bezier(.4,0,.2,1)';
  });
});

/* ── Score circle animation (SVG) ───────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const circles = document.querySelectorAll('.score-circle circle:last-child');
  circles.forEach(c => {
    const target = c.getAttribute('stroke-dasharray').split(',')[0];
    c.setAttribute('stroke-dasharray', '0, 339');
    requestAnimationFrame(() => {
      setTimeout(() => {
        c.style.transition = 'stroke-dasharray 1.4s ease';
        c.setAttribute('stroke-dasharray', `${target}, 339`);
      }, 200);
    });
  });
});

/* ── Lesson page: track reading time ────────────────────── */
(function () {
  if (!document.getElementById('lessonContent')) return;
  let seconds = 0;
  setInterval(() => seconds++, 1000);
  window.addEventListener('beforeunload', () => {
    if (seconds < 2) return;
    const lessonId = document.querySelector('[data-lesson-id]')?.dataset.lessonId;
    if (lessonId) {
      navigator.sendBeacon(`/lesson/${lessonId}/time`, JSON.stringify({ seconds }));
    }
  });
})();

/* ── Tooltip on hover ─────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[title]').forEach(el => {
    el.setAttribute('data-title', el.title);
  });
});

/* ── Image preview on file select ────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('input[type="file"][accept*="image"]').forEach(input => {
    input.addEventListener('change', function () {
      if (!this.files[0]) return;
      const reader = new FileReader();
      reader.onload = e => {
        let preview = this.parentElement.querySelector('.img-preview');
        if (!preview) {
          preview = document.createElement('img');
          preview.className = 'img-preview';
          preview.style.cssText = 'margin-top:.5rem;border-radius:10px;max-height:150px;border:2px solid #e5e7eb;object-fit:contain;';
          this.parentElement.appendChild(preview);
        }
        preview.src = e.target.result;
      };
      reader.readAsDataURL(this.files[0]);
    });
  });
});

/* ── Mobile responsive nav ───────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const style = document.createElement('style');
  style.textContent = `
    @media(max-width:900px){
      .nav-links { display:none; position:fixed; top:64px; right:0; left:0;
        background:#fff; flex-direction:column; padding:1rem; gap:.25rem;
        box-shadow:0 8px 24px rgba(0,0,0,.1); border-bottom:2px solid #e5e7eb; z-index:999; }
      .nav-links.open { display:flex; }
      .nav-toggle { display:flex; }
      .nav-user .nav-points { display:none; }
    }
  `;
  document.head.appendChild(style);
});
