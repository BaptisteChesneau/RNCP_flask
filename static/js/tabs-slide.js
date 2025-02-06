$(document).ready(function() {
    // Lors du clic sur un onglet
    $('#accountTab a').on('click', function(e) {
      e.preventDefault();
      
      var $this = $(this);
      var targetSelector = $this.attr('href');
      
      // Si l'onglet cliqué est déjà actif, ne rien faire
      if ($this.hasClass('active')) {
        return;
      }
      
      var $currentTab = $('#accountTabContent .tab-pane.active');
      var $targetTab = $(targetSelector);
      
      // Animation de glissement sortant pour l'onglet actif
      $currentTab.animate({ left: '-100%', opacity: 0 }, 300, function() {
        $currentTab.removeClass('active').css({ left: '0%', opacity: 1 });
        
        // Prépare l'onglet cible pour l'animation entrante
        $targetTab.css({ left: '100%', opacity: 0 }).addClass('active');
        
        // Animation de glissement entrant pour l'onglet cible
        $targetTab.animate({ left: '0%', opacity: 1 }, 300);
      });
      
      // Mise à jour de la classe active sur les onglets
      $('#accountTab a').removeClass('active');
      $this.addClass('active');
    });
  });  