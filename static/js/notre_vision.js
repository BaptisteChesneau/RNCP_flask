// Gestion du style du header au scroll
window.addEventListener('scroll', () => {
  document.getElementById('mainHeader').classList.toggle('scrolled', window.scrollY > 60);
});

// Gestion de l'ouverture du menu burger
document.getElementById('burgerBtn').addEventListener('click', function() {
  document.getElementById('mainNav').classList.toggle('open');
  this.classList.toggle('active');
});

// Animation d'apparition (Intersection Observer) pour les cartes et éléments
const observerOptions = {
  threshold: 0.08
};

const appearanceObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = '1';
      entry.target.style.transform = 'translateY(0)';
    }
  });
}, observerOptions);

// Initialisation des styles de base et observation des éléments de la page
document.querySelectorAll('.vis-pilier, .vis-ia-card, .vis-diff').forEach(el => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(16px)';
  el.style.transition = 'opacity .45s ease, transform .45s ease';
  appearanceObserver.observe(el);
});