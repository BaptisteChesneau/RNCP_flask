document.addEventListener("DOMContentLoaded", function () {
  // Header scrolled effect handling
  const hdr = document.getElementById('mainHeader');
  if (hdr) {
    window.addEventListener('scroll', () => {
      hdr.classList.toggle('scrolled', window.scrollY > 60);
    });
  }

  // Mobile Burger menu handling
  const burger = document.getElementById('burgerBtn');
  const nav = document.getElementById('mainNav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      nav.classList.toggle('open');
      this.classList.toggle('active');
    });
  }

  // Intersection Observer to trigger scroll animations
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
      }
    });
  }, { 
    threshold: 0.1 
  });

  // Observe all elements with the data-anim attribute
  document.querySelectorAll('[data-anim]').forEach(el => obs.observe(el));
});