// ============================================================
//  1. SERVICES TABS MANAGEMENT
// ============================================================
document.querySelectorAll('.svc-tab').forEach(tab => {
  tab.addEventListener('click', function() {
    document.querySelectorAll('.svc-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.svc-panel').forEach(p => p.classList.remove('active'));
    
    this.classList.add('active');
    const targetPanel = document.getElementById('svc-' + this.dataset.target);
    if (targetPanel) targetPanel.classList.add('active');
  });
});

// ============================================================
//  2. NUMERICAL COUNTERS ANIMATION
// ============================================================
function animateCounters() {
  document.querySelectorAll('.stat-num[data-target]').forEach(el => {
    const target = +el.dataset.target;
    const step = target / (1800 / 16);
    let current = 0;
    
    const timer = setInterval(() => {
      current += step;
      if (current >= target) {
        el.textContent = target;
        clearInterval(timer);
      } else {
        el.textContent = Math.floor(current);
      }
    }, 16);
  });
}

// Observer to trigger animation on scroll
const statsObs = new IntersectionObserver(entries => {
  if (entries[0].isIntersecting) {
    animateCounters();
    statsObs.disconnect();
  }
}, { threshold: 0.3 });

if (document.querySelector('.stats-bar')) {
  statsObs.observe(document.querySelector('.stats-bar'));
}

// ============================================================
//  3. SMOOTH SCROLL FOR ANCHORS (#)
// ============================================================
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', function(e) {
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      e.preventDefault();
      const headerH = document.querySelector('.main-header')?.offsetHeight || 80;
      window.scrollTo({
        top: target.offsetTop - headerH - 16,
        behavior: 'smooth'
      });
    }
  });
});

// ============================================================
//  4. OBSERVER FOR ENTRANCE ANIMATIONS (data-anim)
// ============================================================
const animObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      animObserver.unobserve(entry.target);
    }
  });
}, {
  root: null,
  threshold: 0.1,
  rootMargin: "0px 0px -40px 0px"
});

// ============================================================
//  5. INITIALIZATION FOR NEW APPS (Menu & Chatbot)
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
  // Activate entrance animations on scroll
  document.querySelectorAll('[data-anim]').forEach(el => {
    animObserver.observe(el);
  });

  // Mobile Burger Menu Handling
  const burgerBtn = document.querySelector('.burger-btn');
  const mainNav = document.querySelector('.main-nav');

  if (burgerBtn && mainNav) {
    burgerBtn.addEventListener('click', () => {
      burgerBtn.classList.toggle('active');
      mainNav.classList.toggle('open');
    });
  }

  // Chatbot Open/Close Handling
  const chatFab = document.querySelector('.chatbot-fab');
  const chatWidget = document.querySelector('.chatbot-widget');
  const chatMinimize = document.querySelector('.cw-minimize');
  const chatNotif = document.querySelector('.chatbot-notif');

  if (chatFab && chatWidget) {
    // Open / Close on floating button click
    chatFab.addEventListener('click', () => {
      const isOpen = chatWidget.classList.toggle('is-open');
      chatFab.classList.toggle('is-open', isOpen);
      
      // Hide notification badge on first open
      if (isOpen && chatNotif) {
        chatNotif.classList.add('hide');
      }
    });

    // Close via internal minimize arrow
    if (chatMinimize) {
      chatMinimize.addEventListener('click', () => {
        chatWidget.classList.remove('is-open');
        chatFab.classList.remove('is-open');
      });
    }
  }
});