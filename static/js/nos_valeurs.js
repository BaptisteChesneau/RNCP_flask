/**
 * ML2C CONSEIL — Behavioral scripts for the "Our Values" page
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Header scroll effect and class handling
    window.addEventListener('scroll', () => {
        const mainHeader = document.getElementById('mainHeader');
        if (mainHeader) {
            mainHeader.classList.toggle('scrolled', window.scrollY > 60);
        }
    });

    // 2. Mobile Burger Menu handling
    const burgerBtn = document.getElementById('burgerBtn');
    const mainNav = document.getElementById('mainNav');
    
    if (burgerBtn && mainNav) {
        burgerBtn.addEventListener('click', function() {
            mainNav.classList.toggle('open');
            this.classList.toggle('active');
        });
    }

    // 3. Scroll animation appearance effect (Intersection Observer)
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

    // Targeting elements to animate
    const targetsToAnimate = document.querySelectorAll('.val-detail-card, .meth-card, .val-comp-row');
    
    targetsToAnimate.forEach(el => {
        // Initial state (hidden and offset downwards)
        el.style.opacity = '0';
        el.style.transform = 'translateY(14px)';
        el.style.transition = 'opacity .4s ease, transform .4s ease';
        
        // Connect with the observer
        scrollObserver.observe(el);
    });
});