
"""
Universal Deployment Configuration
Turli muhitlar uchun deployment sozlamalari
"""

import os

class DeploymentManager:
    """Deployment boshqaruvi"""
    
    @staticmethod
    def get_deployment_config():
        """Deployment konfiguratsiyasini olish"""
        env = os.environ.get('FLASK_ENV', 'production')
        
        if env == 'development':
            return {
                "host": "0.0.0.0",
                "port": int(os.environ.get('PORT', 5000)),
                "debug": True,
                "threaded": True,
                "use_reloader": True
            }
        else:
            return {
                "host": "0.0.0.0", 
                "port": int(os.environ.get('PORT', 5000)),
                "debug": False,
                "threaded": True,
                "use_reloader": False
            }
    
    @staticmethod
    def setup_production_logging():
        """Production uchun logging sozlash"""
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Logs papkasini yaratish
        os.makedirs('logs', exist_ok=True)
        
        # Production logging
        if not logging.getLogger().handlers:
            file_handler = RotatingFileHandler(
                'logs/restaurant.log', 
                maxBytes=10485760, 
                backupCount=5
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s'
            ))
            file_handler.setLevel(logging.INFO)
            logging.getLogger().addHandler(file_handler)
            logging.getLogger().setLevel(logging.INFO)
    
    @staticmethod
    def check_requirements():
        """Kerakli kutubxonalar mavjudligini tekshirish"""
        required_packages = [
            'flask', 'werkzeug', 'flask_sqlalchemy', 
            'flask_limiter', 'flask_cors', 'flask_compress',
            'pytz', 'qrcode', 'requests', 'python-dotenv'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        return missing_packages
    
    @staticmethod
    def initialize_app_data():
        """Dastur ma'lumotlarini boshlang'ich holga keltirish"""
        # Kerakli papkalarni yaratish
        folders = [
            'static/uploads',
            'static/images', 
            'logs',
            'backups',
            'instance'
        ]
        
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
        
        # Default rasmlarni tekshirish
        default_images = [
            'static/images/default-food.jpg',
            'static/images/default-drink.jpg'
        ]
        
        for image_path in default_images:
            if not os.path.exists(image_path):
                # Placeholder rasm yaratish
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    img = Image.new('RGB', (300, 200), color='lightgray')
                    draw = ImageDraw.Draw(img)
                    draw.text((150, 100), "No Image", fill='black', anchor='mm')
                    img.save(image_path)
                except Exception:
                    # Agar PIL mavjud bo'lmasa, oddiy file yaratish
                    with open(image_path, 'w') as f:
                        f.write("# Placeholder image")

def get_server_config():
    """Server konfiguratsiyasini olish"""
    deployment_manager = DeploymentManager()
    
    # Kerakli paketlarni tekshirish
    missing = deployment_manager.check_requirements()
    if missing:
        print(f"Kerakli paketlar mavjud emas: {missing}")
        print("pip install -r requirements.txt buyrug'ini bajaring")
    
    # Ma'lumotlarni boshlash
    deployment_manager.initialize_app_data()
    
    # Production logging
    if os.environ.get('FLASK_ENV') == 'production':
        deployment_manager.setup_production_logging()
    
    # Server konfiguratsiyasi
    return deployment_manager.get_deployment_config()
