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