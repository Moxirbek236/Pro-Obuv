"""
Universal Restaurant System Deployment Configuration
"""

import os

def get_server_config():
    """Server konfiguratsiyasini qaytarish"""
    return {
        'host': '0.0.0.0',  # Replit uchun 0.0.0.0 kerak
        'port': int(os.environ.get('PORT', 5000)),
        'debug': os.environ.get('FLASK_ENV') == 'development',
        'threaded': True
    }

def get_production_config():
    """Production muhit uchun konfiguratsiya"""
    return {
        'host': '0.0.0.0',
        'port': int(os.environ.get('PORT', 5000)),
        'debug': False,
        'threaded': True,
        'use_reloader': False,
        'use_debugger': False
    }