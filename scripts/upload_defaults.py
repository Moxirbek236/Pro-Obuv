import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.getcwd())

from services.cloudinary_service import cloudinary_service

load_dotenv()

def upload_defaults():
    defaults = [
        ('static/images/default-men.jpg', 'static-root/images/default-men'),
        ('static/images/default-product.jpg', 'static-root/images/default-product'),
        ('static/images/default-avatar.svg', 'static-root/images/default-avatar')
    ]
    
    for local_path, public_id in defaults:
        if os.path.exists(local_path):
            print(f"Uploading {local_path} to Cloudinary as {public_id}...")
            resource_type = "image"
            if local_path.endswith('.svg'):
                # Some Cloudinary accounts require raw for SVG or specific flags
                # but let's try image first
                resource_type = "image"
            
            with open(local_path, 'rb') as f:
                result = cloudinary_service.upload_image(f, folder=os.path.dirname(public_id), public_id=os.path.basename(public_id), resource_type=resource_type)
                if result:
                    print(f"Success: {result.get('secure_url')}")
                else:
                    print(f"Failed to upload {local_path}")
        else:
            print(f"Local file {local_path} missing")

if __name__ == "__main__":
    upload_defaults()
