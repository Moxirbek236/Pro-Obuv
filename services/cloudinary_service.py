import cloudinary
import cloudinary.uploader
import cloudinary.utils
import os
from dotenv import load_dotenv

load_dotenv()

class CloudinaryService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CloudinaryService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        cloudinary.config(
            cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'dpfbu9aid'),
            api_key=os.getenv('CLOUDINARY_API_KEY', '476124988873837'),
            api_secret=os.getenv('CLOUDINARY_API_SECRET', '5IRqnu0U729V1PQW9VlPqNu3o8k'),
            secure=True
        )
        self._initialized = True

    def upload_image(self, file_stream, folder="uploads", public_id=None, resource_type="auto"):
        """
        Uploads a file to Cloudinary.
        file_stream can be a file-like object (e.g., request.files['file'].stream)
        """
        try:
            upload_result = cloudinary.uploader.upload(
                file_stream,
                folder=folder,
                public_id=public_id,
                resource_type=resource_type,
                overwrite=True,
                invalidate=True
            )
            return upload_result
        except Exception as e:
            print(f"Cloudinary upload error: {str(e)}")
            return None

    def delete_image(self, public_id, resource_type="image"):
        """Deletes an asset from Cloudinary."""
        try:
            result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            return result
        except Exception as e:
            print(f"Cloudinary delete error: {str(e)}")
            return None

    def get_optimized_url(self, public_id, **kwargs):
        """Generates an optimized URL with f_auto and q_auto by default."""
        options = {
            "fetch_format": "auto",
            "quality": "auto",
            "secure": True
        }
        options.update(kwargs)
        
        # Determine resource_type if not provided
        resource_type = kwargs.get("resource_type", "image")
        
        # Handle raw files (non-images)
        if any(public_id.endswith(ext) for ext in ['.webmanifest', '.json', '.ico', '.txt', '.pdf']):
            resource_type = "raw"
            options.pop("fetch_format", None)
            options.pop("quality", None)

        return cloudinary.utils.cloudinary_url(public_id, resource_type=resource_type, **options)[0]

# Export a singleton instance
cloudinary_service = CloudinaryService()
