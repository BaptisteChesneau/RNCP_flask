document.addEventListener("DOMContentLoaded", function () {
  // 1. Header scroll effect handling with passive listener
  const hdr = document.getElementById('mainHeader');
  if (hdr) {
    window.addEventListener('scroll', () => {
      hdr.classList.toggle('scrolled', window.scrollY > 60);
    }, { passive: true });
  }

  // 2. Burger menu handling with ARIA accessibility
  const burger = document.getElementById('burgerBtn');
  const nav = document.getElementById('mainNav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      const isOpen = nav.classList.toggle('open');
      this.classList.toggle('active', isOpen);
      this.setAttribute('aria-expanded', isOpen);
    });
  }

  // 3. Scroll animation handling with fallback and unobserve
  const animElements = document.querySelectorAll('[data-anim]');

  if ('IntersectionObserver' in window && animElements.length > 0) {
    const obs = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target); // Release memory once animated
        }
      });
    }, { threshold: 0.05 });

    animElements.forEach(el => obs.observe(el));
  } else {
    // Fallback: if observer is not supported, display directly
    animElements.forEach(el => el.classList.add('visible'));
  }
});