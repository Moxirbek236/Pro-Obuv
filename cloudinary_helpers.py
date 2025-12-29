from flask import url_for
from services.cloudinary_service import cloudinary_service
import re
import os

def is_cloudinary_url(url):
    """Checks if a URL or path is already a Cloudinary URL."""
    if not url:
        return False
    return "res.cloudinary.com" in url or url.startswith("http")

def get_cloudinary_url(path, **kwargs):
    """
    Returns a Cloudinary URL for a given path/public_id.
    ALWAYS forces Cloudinary usage according to user request.
    """
    if not path:
        return ""
    
    # If it's already a full Cloudinary URL
    if "res.cloudinary.com" in path:
        if "f_auto" in path and "q_auto" in path:
            return path
        # If it's a Cloudinary URL but lacks optimization, we try to extract public_id
        # or just return as is for now to avoid complex re-parsing.
        # However, it's better to ensure f_auto,q_auto.
        if "/upload/" in path and "f_auto" not in path:
            return path.replace("/upload/", "/upload/f_auto,q_auto/")
        return path

    if path.startswith(('http://', 'https://')):
        return path

    clean_path = path.replace(url_for('static', filename=''), '').lstrip('/') if 'static' in path else path.lstrip('/')
    
    # Define public_id based on path
    if clean_path.startswith('uploads/products/'):
        public_id = clean_path.replace('uploads/products/', 'products/')
    elif clean_path.startswith('uploads/avatars/'):
        public_id = clean_path.replace('uploads/avatars/', 'avatars/')
    elif clean_path.startswith('favicons/'):
        public_id = clean_path # keep folder
    elif clean_path.startswith('icons/'):
        public_id = clean_path # keep folder
    else:
        # Default prefix for other static assets
        if not any(clean_path.startswith(p) for p in ['products/', 'avatars/', 'news/', 'favicons/', 'icons/']):
            public_id = f"static-root/{clean_path}"
        else:
            public_id = clean_path

    # Strip extension for images/videos in Cloudinary
    name, ext = os.path.splitext(public_id)
    if ext.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.mp4', '.mov', '.webm']:
        public_id = name
            
    return cloudinary_service.get_optimized_url(public_id, **kwargs)

def get_cloudinary_thumbnail(path, width=200, height=200, crop="fill"):
    """Returns a thumbnail URL."""
    return get_cloudinary_url(path, width=width, height=height, crop=crop)

def register_cloudinary_helpers(app):
    """Registers helpers with Jinja2."""
    app.jinja_env.filters['cloudinary_url'] = get_cloudinary_url
    app.jinja_env.filters['cloudinary_thumb'] = get_cloudinary_thumbnail
    app.jinja_env.filters['is_cloudinary'] = is_cloudinary_url
    
    # Global functions
    app.jinja_env.globals.update(
        cloudinary_url=get_cloudinary_url,
        cloudinary_thumb=get_cloudinary_thumbnail,
        is_cloudinary=is_cloudinary_url
    )
