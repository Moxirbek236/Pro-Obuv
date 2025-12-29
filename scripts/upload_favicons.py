import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.getcwd())

from services.cloudinary_service import cloudinary_service

load_dotenv()

def upload_favicons():
    favicon_dir = 'favicons'
    if not os.path.exists(favicon_dir):
        print(f"Directory {favicon_dir} missing")
        return

    files = os.listdir(favicon_dir)
    for filename in files:
        local_path = os.path.join(favicon_dir, filename)
        if os.path.isfile(local_path):
            public_id = f"favicons/{filename}"
            # Strip extension for images to match get_cloudinary_url logic
            name, ext = os.path.splitext(filename)
            if ext.lower() in ['.webp', '.png', '.jpg', '.jpeg']:
                public_id = f"favicons/{name}"
            
            resource_type = "image"
            if ext.lower() in ['.ico', '.webmanifest', '.json', '.xml']:
                resource_type = "raw"
                public_id = f"favicons/{filename}" # Keep extension for raw
            
            print(f"Uploading {local_path} as {public_id} (type: {resource_type})...")
            with open(local_path, 'rb') as f:
                result = cloudinary_service.upload_image(f, folder="favicons", public_id=os.path.basename(public_id), resource_type=resource_type)
                if result:
                    print(f"Success: {result.get('secure_url')}")
                else:
                    print(f"Failed to upload {local_path}")

if __name__ == "__main__":
    upload_favicons()
