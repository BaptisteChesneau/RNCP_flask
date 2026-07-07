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
  const animElements = document.querySelectorAll('[data-anim]');

  if ('IntersectionObserver' in window && animElements.length > 0) {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          // Optionnel : on個 arrête d'observer l'élément une fois apparu
          obs.unobserve(e.target); 
        }
      });
    }, { 
      threshold: 0.01 // Seuil minimaliste pour éviter les bugs sur mobile
    });

    animElements.forEach(el => obs.observe(el));
  } else {
    // Solution de secours : si l'observer échoue, on affiche tout directement
    animElements.forEach(el => el.classList.add('visible'));
  }
});