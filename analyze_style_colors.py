import os
import sys

try:
    from PIL import Image
    from collections import Counter
except ImportError:
    print("Pillow not installed")
    sys.exit(0)

def get_dominant_color(image_path, num_colors=3):
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        img = img.resize((50, 50))  # Resize for speed
        pixels = list(img.getdata())
        counts = Counter(pixels)
        total_pixels = len(pixels)
        
        # Filter pixels: ignore white/black/gray
        vibrant_pixels = []
        for r, g, b in pixels:
            # Simple saturation check: max(rgb) - min(rgb)
            saturation = max(r, g, b) - min(r, g, b)
            # Ignore if saturation is low (grayish) or very bright white or very dark black
            if saturation > 20 and max(r,g,b) < 250 and min(r,g,b) > 10:
                vibrant_pixels.append((r, g, b))
        
        if not vibrant_pixels:
            return "No vibrant colors found"

        counts = Counter(vibrant_pixels)
        total_pixels = len(pixels) # Keep original total for percentage relative to whole image? Or specific?
        # Let's use vibrant count for relative frequency among colors
        
        sorted_pixels = counts.most_common(5)
        
        hex_colors = []
        for color, count in sorted_pixels:
            hex_code = '#{:02x}{:02x}{:02x}'.format(*color)
            hex_colors.append((hex_code, count/len(vibrant_pixels)))
        return hex_colors
    except Exception as e:
        return str(e)

style_dir = r"d:\Safety.uz\styles_images"
files = [f for f in os.listdir(style_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]

print(f"Found {len(files)} images.")

for f in files:
    path = os.path.join(style_dir, f)
    print(f"\nAnalyzing {f}:")
    colors = get_dominant_color(path)
    if isinstance(colors, list):
        for hex_c, freq in colors:
            print(f"  {hex_c} ({freq:.1%})")
    else:
        print(f"  Error: {colors}")
