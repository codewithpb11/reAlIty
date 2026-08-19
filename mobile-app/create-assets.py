from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename, text="R", is_splash=False):
    """Create a simple icon with the reAlIty branding."""
    # Dark background
    img = Image.new('RGB', (size, size), color='#0d0d0d')
    draw = ImageDraw.Draw(img)
    
    if is_splash:
        # Splash screen - larger text, centered
        try:
            font = ImageFont.truetype("arial.ttf", size // 4)
        except:
            font = ImageFont.load_default()
        
        # Draw text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2 - size // 10
        draw.text((x, y), text, fill='#ffffff', font=font)
        
        # Subtitle
        subtitle = "AI Image Detector"
        try:
            sub_font = ImageFont.truetype("arial.ttf", size // 14)
        except:
            sub_font = ImageFont.load_default()
        bbox2 = draw.textbbox((0, 0), subtitle, font=sub_font)
        sw = bbox2[2] - bbox2[0]
        sh = bbox2[3] - bbox2[1]
        draw.text(((size - sw) // 2, y + text_height + size // 20), subtitle, fill='#888888', font=sub_font)
    else:
        # App icon - circle with R
        padding = size // 8
        draw.ellipse([padding, padding, size - padding, size - padding], fill='#1a1a1a', outline='#333333', width=size//100)
        
        try:
            font = ImageFont.truetype("arial.ttf", size // 3)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2 - size // 20
        draw.text((x, y), text, fill='#ffffff', font=font)
    
    img.save(filename, 'PNG')
    print(f"Created {filename} ({size}x{size})")

os.makedirs('mobile-app/assets', exist_ok=True)

# Create app icon (1024x1024)
create_icon(1024, 'mobile-app/assets/icon.png', 'R')

# Create adaptive icon foreground (1024x1024, transparent background concept but we use solid)
create_icon(1024, 'mobile-app/assets/adaptive-icon.png', 'R')

# Create splash screen (1242x2436 - iPhone standard, we'll use square crop friendly)
create_icon(1242, 'mobile-app/assets/splash.png', 'reAlIty', is_splash=True)

print("\nAll assets created!")
