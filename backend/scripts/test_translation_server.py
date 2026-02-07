from app import app
from flask import render_template_string

@app.route('/test-translations')
def test_translations():
    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Translation Test</title>
    </head>
    <body>
        <h1>Translation Test</h1>
        <h2>Server-side:</h2>
        <p>nav.home: {{ _('nav.home') }}</p>
        <p>menu.all_products: {{ _('menu.all_products') }}</p>
        <p>Current language: {{ current_language }}</p>
        
        <h2>Client-side:</h2>
        <p>nav.home: <span data-translate="nav.home"></span></p>
        <p>menu.all_products: <span data-translate="menu.all_products"></span></p>
        
        <script>
            console.log('Translations available:', Object.keys(window.TRANSLATIONS).length);
            console.log('Sample nav.home:', window.TRANSLATIONS['nav.home']);
            console.log('Sample menu.all_products:', window.TRANSLATIONS['menu.all_products']);
            
            // Apply translations
            document.querySelectorAll('[data-translate]').forEach(el => {
                const key = el.getAttribute('data-translate');
                if (window.TRANSLATIONS[key]) {
                    el.textContent = window.TRANSLATIONS[key];
                }
            });
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(template)

if __name__ == '__main__':
    print('Starting test server...')
    print('Visit http://localhost:5000/test-translations')
    app.run(debug=True, port=5000)
