document.addEventListener('DOMContentLoaded', () => {
  /* ── Global Variables ── */
  let activeCat = 'all';
  const searchInput = document.getElementById('searchInput');
  const blogCats = document.querySelectorAll('.blog-cat');
  const tagItems = document.querySelectorAll('.tag-item');
  const newsletterBtn = document.getElementById('newsletterBtn');
  const pageBtns = document.querySelectorAll('.page-btn');

  /* ── Event Listeners ── */
  
  // Text search input
  if (searchInput) {
    searchInput.addEventListener('input', applyFilters);
  }

  // Category buttons click (Hero)
  blogCats.forEach(btn => {
    btn.addEventListener('click', function() {
      blogCats.forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      activeCat = this.dataset.cat;
      applyFilters();
      
      const mainSection = document.querySelector('.blog-main');
      if (mainSection) {
        window.scrollTo({ top: mainSection.offsetTop - 80, behavior: 'smooth' });
      }
    });
  });

  // Tags click (Sidebar)
  tagItems.forEach(tag => {
    tag.addEventListener('click', function() {
      const cat = this.dataset.tagCat;
      activeCat = cat;
      blogCats.forEach(b => {
        b.classList.toggle('active', b.dataset.cat === cat);
      });
      applyFilters();
    });
  });

  // Newsletter subscription
  if (newsletterBtn) {
    newsletterBtn.addEventListener('click', function() {
      const input = this.previousElementSibling;
      if (!input || !input.value || !input.value.includes('@')) {
        if (input) {
          input.style.border = '2px solid rgba(255,255,255,.6)';
          input.focus();
        }
        return;
      }
      this.innerHTML = '<i class="fas fa-check"></i> Subscribed !';
      this.style.background = 'rgba(255,255,255,.35)';
      this.disabled = true;
      input.value = '';
    });
  }

  // Pagination (Demo)
  pageBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      pageBtns.forEach(b => b.classList.remove('active'));
      this.classList.add('active');
    });
  });

  /* ── Shared Filtering Function ── */
  function applyFilters() {
    const query = searchInput ? searchInput.value.toLowerCase() : '';
    const cards = document.querySelectorAll('.article-card');
    const featured = document.querySelector('.article-featured');
    const noResult = document.getElementById('noResult');
    let visibleCount = 0;

    /* Filtering the featured article */
    if (featured) {
      const featCat = featured.dataset.cat;
      const featTitleElement = featured.querySelector('.article-featured-title');
      const featTitle = featTitleElement ? featTitleElement.textContent.toLowerCase() : '';
      const featMatch = (activeCat === 'all' || featCat === activeCat) && featTitle.includes(query);
      
      featured.style.display = featMatch ? '' : 'none';
      if (featMatch) visibleCount++;
    }

    /* Filtering the article grid */
    cards.forEach(card => {
      const cat = card.dataset.cat;
      const title = card.dataset.title ? card.dataset.title.toLowerCase() : '';
      const match = (activeCat === 'all' || cat === activeCat) && title.includes(query);
      
      card.style.display = match ? '' : 'none';
      if (match) visibleCount++;
    });

    /* Handling the no-results message display */
    if (noResult) {
      noResult.style.display = visibleCount === 0 ? 'block' : 'none';
    }
  }
});