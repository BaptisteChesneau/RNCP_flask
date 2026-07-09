// Gestion du changement des onglets de services
document.querySelectorAll('.svc-tab').forEach(tab => {
  tab.addEventListener('click', function() {
    document.querySelectorAll('.svc-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.svc-panel').forEach(p => p.classList.remove('active'));
    
    this.classList.add('active');
    document.getElementById('svc-' + this.dataset.target).classList.add('active');
  });
});

// Animation des compteurs numériques
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

// Défilement fluide pour les ancres (#)
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
//  OBSERVATEUR POUR LES ANIMATIONS D'APPARITION (data-anim)
// ============================================================
const animObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    // Dès que l'élément visible entre à 10% dans l'écran, on joue l'animation
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      // Optionnel : on arrête d'observer pour que l'animation ne se joue qu'une seule fois
      animObserver.unobserve(entry.target);
    }
  });
}, {
  root: null, // Par rapport au viewport (fenêtre d'affichage)
  threshold: 0.1, // Se déclenche dès que 10% de l'élément est visible
  rootMargin: "0px 0px -40px 0px" // Petit décalage vers le bas pour un effet plus naturel
});

// On cible tous les éléments qui ont l'attribut [data-anim] et on les observe
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('[data-anim]').forEach(el => {
    animObserver.observe(el);
  });
});