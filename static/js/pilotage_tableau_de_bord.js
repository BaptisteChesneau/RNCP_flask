document.addEventListener("DOMContentLoaded", function () {
  // Gestion du Header lors du défilement
  const hdr = document.getElementById('mainHeader');
  if (hdr) {
    window.addEventListener('scroll', () => {
      hdr.classList.toggle('scrolled', window.scrollY > 60);
    });
  }

  // Menu Burger Responsif
  const burger = document.getElementById('burgerBtn');
  const nav = document.getElementById('mainNav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      nav.classList.toggle('open');
      this.classList.toggle('active');
    });
  }

  // Animation des blocs au défilement (Intersection Observer)
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
      }
    });
  }, { 
    threshold: 0.08 
  });

  document.querySelectorAll('[data-anim]').forEach(el => obs.observe(el));
});