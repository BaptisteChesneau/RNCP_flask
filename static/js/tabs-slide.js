$(document).ready(function() {
    // On tab click
    $('#accountTab a').on('click', function(e) {
      e.preventDefault();

      var $this = $(this);
      var targetSelector = $this.attr('href');

      // If the clicked tab is already active, do nothing
      if ($this.hasClass('active')) {
        return;
      }

      var $currentTab = $('#accountTabContent .tab-pane.active');
      var $targetTab = $(targetSelector);

      // Slide-out animation for the active tab
      $currentTab.animate({ left: '-100%', opacity: 0 }, 300, function() {
        $currentTab.removeClass('active').css({ left: '0%', opacity: 1 });

        // Prepare the target tab for the slide-in animation
        $targetTab.css({ left: '100%', opacity: 0 }).addClass('active');

        // Slide-in animation for the target tab
        $targetTab.animate({ left: '0%', opacity: 1 }, 300);
      });

      // Update active class on tab links
      $('#accountTab a').removeClass('active');
      $this.addClass('active');
    });
});