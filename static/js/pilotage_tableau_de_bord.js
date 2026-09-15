document.addEventListener("DOMContentLoaded", function () {
  // Header scroll handling
  const hdr = document.getElementById('mainHeader');
  if (hdr) {
    window.addEventListener('scroll', () => {
      hdr.classList.toggle('scrolled', window.scrollY > 60);
    });
  }

  // Responsive burger menu
  const burger = document.getElementById('burgerBtn');
  const nav = document.getElementById('mainNav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      nav.classList.toggle('open');
      this.classList.toggle('active');
    });
  }

  // Block animations on scroll (Intersection Observer)
  const animElements = document.querySelectorAll('[data-anim]');

  if ('IntersectionObserver' in window && animElements.length > 0) {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          // Optional: stop observing the element once visible
          obs.unobserve(e.target); 
        }
      });
    }, { 
      threshold: 0.01 // Minimal threshold to avoid mobile bugs
    });

    animElements.forEach(el => obs.observe(el));
  } else {
    // Fallback: if the observer fails, display everything directly
    animElements.forEach(el => el.classList.add('visible'));
  }
});