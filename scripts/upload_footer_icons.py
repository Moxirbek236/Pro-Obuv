import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cloudinary configuration
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

def upload_icon(local_path, public_id):
    try:
        if not os.path.exists(local_path):
            print(f"File not found: {local_path}")
            return None
        
        # Use image resource type for webp
        response = cloudinary.uploader.upload(
            local_path,
            public_id=public_id,
            overwrite=True,
            resource_type="image"
        )
        print(f"Uploaded {local_path} to {response['secure_url']}")
        return response['secure_url']
    except Exception as e:
        print(f"Error uploading {local_path}: {e}")
        return None

if __name__ == "__main__":
    icon_dir = r"D:\Safety.uz\icons"
    
    # Mapping of local files to expected footer public_ids (prefixed with icons/)
    # (local_filename, target_public_id)
    mappings = [
        ("Phone_icon.webp", "icons/phone"),
        ("2023_Facebook_icon.svg.webp", "icons/facebook"),
        ("gmail.webp", "icons/gmail"),
        ("threads.webp", "icons/threads"),
        ("uzum.webp", "icons/uzum"),
        ("yandex.webp", "icons/yandex"),
        ("2111463.webp", "icons/maps"), # Assuming this is the map icon
    ]
    
    for local_name, target_id in mappings:
        upload_icon(os.path.join(icon_dir, local_name), target_id)

    # Also upload the site.webmanifest as raw to be sure
    manifest_path = r"D:\Safety.uz\favicons\site.webmanifest"
    if os.path.exists(manifest_path):
        try:
            res = cloudinary.uploader.upload(
                manifest_path,
                public_id="favicons/site.webmanifest",
                resource_type="raw",
                overwrite=True
            )
            print(f"Uploaded manifest to {res['secure_url']}")
        except Exception as e:
            print(f"Error uploading manifest: {e}")
