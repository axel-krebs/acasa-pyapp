requirejs.config({
    baseUrl: '/js/lib',
    paths: {
        app: '/js/app'
    }
});

// Start the main app logic.
requirejs(['jquery-3.6.3.min', 'app/sub'],
function($, sub) {
    console.log('jQuery loaded..')
});