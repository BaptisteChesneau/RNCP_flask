/**
 * ML2C CONSEIL — Scripts comportementaux de la page "Nos Valeurs"
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Gestion du Header et de sa classe au scroll
    window.addEventListener('scroll', () => {
        const mainHeader = document.getElementById('mainHeader');
        if (mainHeader) {
            mainHeader.classList.toggle('scrolled', window.scrollY > 60);
        }
    });

    // 2. Gestion du Menu Burger Mobile
    const burgerBtn = document.getElementById('burgerBtn');
    const mainNav = document.getElementById('mainNav');
    
    if (burgerBtn && mainNav) {
        burgerBtn.addEventListener('click', function() {
            mainNav.classList.toggle('open');
            this.classList.toggle('active');
        });
    }

    // 3. Animation d'apparition des éléments au défilement (Intersection Observer)
    const animOptions = {
        threshold: 0.08
    };

    const scrollObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, animOptions);

    // Ciblage des éléments à animer
    const targetsToAnimate = document.querySelectorAll('.val-detail-card, .meth-card, .val-comp-row');
    
    targetsToAnimate.forEach(el => {
        // État initial (masqué et décalé vers le bas)
        el.style.opacity = '0';
        el.style.transform = 'translateY(14px)';
        el.style.transition = 'opacity .4s ease, transform .4s ease';
        
        // Liaison avec l'observateur
        scrollObserver.observe(el);
    });
});