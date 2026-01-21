import json

# Test translation system
print('Testing translation system...')

# Test 1: Check if translations load correctly
try:
    from app import create_app
    app = create_app()
    with app.app_context():
        # Test translation loading
        from utils import get_text
        result = get_text('homepage.hero_title', 'en')
        print(f'Test 1 - get_text(\"homepage.hero_title\", \"en\"): {result}')
        
        # Test 2: Check if translation keys exist
        data = app.config.get('TRANSLATIONS', {})
        if 'en' in data and 'homepage' in data['en']:
            print('Test 2 - English homepage section exists')
        else:
            print('Test 2 - English homepage section missing')
        
        # Test 3: Check if cart keys exist
        if 'cart' in data.get('uz', {}):
            print('Test 3 - Uzbek cart section exists')
        else:
            print('Test 3 - Uzbek cart section missing')
            
        print('Translation system test completed!')
        
except Exception as e:
    print(f'Error: {e}')
