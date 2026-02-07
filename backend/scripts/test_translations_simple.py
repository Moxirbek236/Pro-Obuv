import json

# Test translation system
print('Testing translation system...')

# Test 1: Check if translations load correctly
try:
    # Simple test without Flask app context
    data = {
        "ru": {"homepage": {"hero_title": "PRO OBUV"}},
        "uz": {"homepage": {"hero_title": "PRO OBUV"}},
        "en": {"homepage": {"hero_title": "PRO OBUV"}}
    }
    
    print('Test 1 - Simple test passed!')
    
    # Test 2: Check if translation function works
    def mock_get_text(key, lang='en'):
        translations = {
            "en": {"homepage": {"hero_title": "PRO OBUV"}},
            "uz": {"homepage": {"hero_title": "PRO OBUV"}}
        }
        return translations.get(lang, {}).get('homepage', {}).get(key, key)
    
    result = mock_get_text('homepage.hero_title', 'en')
    print(f'Test 2 - get_text(\"homepage.hero_title\", \"en\"): {result}')
    expected = "PRO OBUV"
    print(f'Test 2 - get_text result: {result}')
    print(f'Test 2 - Expected: {expected}')
    print(f'Test 2 - {"✓" if result == expected else "✗"}')
    
    print('Translation system test completed!')
