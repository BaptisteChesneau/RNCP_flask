document.addEventListener("DOMContentLoaded", function () {
  // Gestion de l'en-tête au défilement
  const hdr = document.getElementById('mainHeader');
  if (hdr) {
    window.addEventListener('scroll', () => {
      hdr.classList.toggle('scrolled', window.scrollY > 60);
    });
  }

  // Menu Burger mobile
  const burger = document.getElementById('burgerBtn');
  const nav = document.getElementById('mainNav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      nav.classList.toggle('open');
      this.classList.toggle('active');
    });
  }

  // Éléments animés au défilement (Intersection Observer)
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
      }
    });
  }, { 
    threshold: 0.1 
  });

  document.querySelectorAll('[data-anim]').forEach(el => obs.observe(el));
});