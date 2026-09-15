document.addEventListener('DOMContentLoaded', () => {
  // 1. Header on scroll with safety check and passive listener
  const hdr = document.getElementById('mainHeader');
  if (hdr) {
    window.addEventListener('scroll', () => {
      hdr.classList.toggle('scrolled', window.scrollY > 60);
    }, { passive: true });
  }

  // 2. Burger menu with safety check and accessibility
  const burger = document.getElementById('burgerBtn');
  const nav = document.getElementById('mainNav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      const isOpen = nav.classList.toggle('open');
      this.classList.toggle('active', isOpen);
      this.setAttribute('aria-expanded', isOpen);
    });
  }

  // 3. Intersection Observer based on .visible CSS class (data-anim)
  const animElements = document.querySelectorAll('.vis-pilier, .vis-ia-card, .vis-diff, [data-anim]');

  if ('IntersectionObserver' in window && animElements.length > 0) {
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          obs.unobserve(entry.target); // Release memory once the element has appeared
        }
      });
    }, { threshold: 0.08 });

    animElements.forEach(el => observer.observe(el));
  } else {
    // Fallback: if observer is not supported, display directly
    animElements.forEach(el => el.classList.add('visible'));
  }
});