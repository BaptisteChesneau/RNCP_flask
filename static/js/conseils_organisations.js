document.addEventListener("DOMContentLoaded", function () {
  // Gestion de l'effet scrolled sur le Header
  const hdr = document.getElementById('mainHeader');
  if (hdr) {
    window.addEventListener('scroll', () => {
      hdr.classList.toggle('scrolled', window.scrollY > 60);
    });
  }

  // Gestion du menu Burger mobile
  const burger = document.getElementById('burgerBtn');
  const nav = document.getElementById('mainNav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      nav.classList.toggle('open');
      this.classList.toggle('active');
    });
  }

  // Intersection Observer pour déclencher les animations au défilement
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
      }
    });
  }, { 
    threshold: 0.1 
  });

  // Observation de tous les éléments possédant l'attribut data-anim
  document.querySelectorAll('[data-anim]').forEach(el => obs.observe(el));
});