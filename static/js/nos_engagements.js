document.addEventListener('DOMContentLoaded', () => {
    
    // Gestion du style du header au scroll
    window.addEventListener('scroll', () => {
        const header = document.getElementById('mainHeader');
        if (header) {
            header.classList.toggle('scrolled', window.scrollY > 60);
        }
    });

    // Gestion du menu Burger mobile
    const burgerBtn = document.getElementById('burgerBtn');
    const mainNav = document.getElementById('mainNav');
    
    if (burgerBtn && mainNav) {
        burgerBtn.addEventListener('click', function() {
            mainNav.classList.toggle('open');
            this.classList.toggle('active');
        });
    }

    // Animation d'apparition (Fade-in / Intersection Observer)
    const observeOptions = {
        threshold: 0.08
    };

    const fadeInObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                // On détache l'élément une fois animé
                fadeInObserver.unobserve(entry.target); 
            }
        });
    }, observeOptions);

    // Initialisation des styles de départ et ciblage des éléments à animer
    const elementsToAnimate = document.querySelectorAll('.eng-card, .eng-temoignage');
    
    elementsToAnimate.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(16px)';
        el.style.transition = 'opacity .45s ease, transform .45s ease';
        fadeInObserver.observe(el);
    });
});