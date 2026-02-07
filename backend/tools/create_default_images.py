from PIL import Image, ImageDraw
import os

os.makedirs('static/images', exist_ok=True)

# Create default-men.jpg
img = Image.new('RGB', (400, 300), color=(100, 100, 100))
draw = ImageDraw.Draw(img)
draw.text((150, 120), "Men Shoes", fill=(255, 255, 255))
img.save('static/images/default-men.jpg', 'JPEG')

# Create default-product.jpg
img = Image.new('RGB', (400, 300), color=(120, 120, 120))
draw = ImageDraw.Draw(img)
draw.text((130, 120), "Product", fill=(255, 255, 255))
img.save('static/images/default-product.jpg', 'JPEG')

print("Images created successfully")
