// ============================================================
//  1. GESTION DES ONGLETS DE SERVICES
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
//  2. ANIMATION DES COMPTEURS NUMÉRIQUES
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

// Observateur pour déclencher l'animation au défilement
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
//  3. DÉFILEMENT FLUIDE POUR LES ANCRES (#)
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
//  4. OBSERVATEUR POUR LES ANIMATIONS D'APPARITION (data-anim)
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
//  5. INITIALISATION DES NOUVELLES APPS (Menu & Chatbot)
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
  // Activation des animations d'apparition au scroll
  document.querySelectorAll('[data-anim]').forEach(el => {
    animObserver.observe(el);
  });

  // Gestion du Menu Burger Mobile
  const burgerBtn = document.querySelector('.burger-btn');
  const mainNav = document.querySelector('.main-nav');

  if (burgerBtn && mainNav) {
    burgerBtn.addEventListener('click', () => {
      burgerBtn.classList.toggle('active');
      mainNav.classList.toggle('open');
    });
  }

  // Gestion de l'ouverture/fermeture du Chatbot
  const chatFab = document.querySelector('.chatbot-fab');
  const chatWidget = document.querySelector('.chatbot-widget');
  const chatMinimize = document.querySelector('.cw-minimize');
  const chatNotif = document.querySelector('.chatbot-notif');

  if (chatFab && chatWidget) {
    // Ouvrir / Fermer au clic sur le bouton flottant
    chatFab.addEventListener('click', () => {
      const isOpen = chatWidget.classList.toggle('is-open');
      chatFab.classList.toggle('is-open', isOpen);
      
      // Masquer la petite pastille de notification dès la première ouverture
      if (isOpen && chatNotif) {
        chatNotif.classList.add('hide');
      }
    });

    // Fermer via la flèche de réduction interne
    if (chatMinimize) {
      chatMinimize.addEventListener('click', () => {
        chatWidget.classList.remove('is-open');
        chatFab.classList.remove('is-open');
      });
    }
  }
});