// Gestion de l'effet scrolled sur le header
const hdr = document.getElementById('mainHeader');
if (hdr) {
  window.addEventListener('scroll', () => {
    hdr.classList.toggle('scrolled', window.scrollY > 60);
  });
}

// Gestion du menu burger
const burger = document.getElementById('burgerBtn');
const nav = document.getElementById('mainNav');
if (burger && nav) {
  burger.addEventListener('click', function() {
    nav.classList.toggle('open');
    this.classList.toggle('active');
  });
}

// Gestion des animations au scroll (Intersection Observer)
const obs = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('[data-anim]').forEach(el => obs.observe(el));