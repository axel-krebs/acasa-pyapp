requirejs.config({
    baseUrl: 'js/lib',
    paths: {
        jquery: 'jquery-3.6.3.min'
    }
});

// Start the main app logic.
requirejs(['jquery'],
function(jq) {
    console.log('jQuery loaded..')
    // Initialize UI from REST data
    jq.ajax({
        url: "test.html",
        context: document.body
      }).done(function() {
        jq( this ).addClass( "done" );
      });
});
