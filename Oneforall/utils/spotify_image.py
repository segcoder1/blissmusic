"""
Spotify-styled image generation for autoplay thumbnails
"""
import io
import aiohttp
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import textwrap


async def download_image(url):
    """Download image from URL"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.read()
    except Exception as e:
        print(f"Image Download Error: {e}")
    return None


def create_spotify_thumbnail(thumbnail_url, title, duration, mood="chill"):
    """
    Create a Spotify-styled thumbnail with blurry background
    
    Args:
        thumbnail_url: URL of the original thumbnail
        title: Song title
        duration: Song duration
        mood: Autoplay mood
    
    Returns:
        PIL Image object
    """
    try:
        # Create a new image with Spotify colors
        width, height = 1080, 1080
        
        # Download the thumbnail image
        if isinstance(thumbnail_url, bytes):
            thumb_img = Image.open(io.BytesIO(thumbnail_url))
        else:
            # If it's a URL string, you'd need to handle downloading
            thumb_img = Image.new('RGB', (width, height), color=(20, 20, 20))
        
        # Resize thumbnail to fit
        thumb_img = thumb_img.resize((width, height), Image.Resampling.LANCZOS)
        
        # Create a blurry background by duplicating and blurring
        background = thumb_img.copy()
        background = background.filter(ImageFilter.GaussianBlur(radius=40))
        
        # Darken the background
        background = Image.new('RGB', (width, height), color=(20, 20, 20))
        background.paste(thumb_img, (0, 0))
        background = background.filter(ImageFilter.GaussianBlur(radius=30))
        
        # Add a dark overlay
        overlay = Image.new('RGBA', (width, height), color=(0, 0, 0, 180))
        background = background.convert('RGBA')
        background = Image.alpha_composite(background, overlay)
        background = background.convert('RGB')
        
        # Resize and center the thumbnail for the foreground
        thumb_size = 500
        thumb_img_resized = thumb_img.resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        
        # Add rounded corners to thumbnail
        thumb_rounded = Image.new('RGBA', (thumb_size, thumb_size), (0, 0, 0, 0))
        thumb_img_rgba = thumb_img_resized.convert('RGBA')
        
        # Create mask for rounded corners
        mask = Image.new('L', (thumb_size, thumb_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, thumb_size, thumb_size], radius=50, fill=255)
        thumb_rounded.paste(thumb_img_rgba, (0, 0), mask)
        
        # Center the thumbnail on the background
        x_offset = (width - thumb_size) // 2
        y_offset = (height - thumb_size) // 2 - 100
        
        background.paste(thumb_rounded, (x_offset, y_offset), thumb_rounded)
        
        # Add text
        draw = ImageDraw.Draw(background)
        
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
            info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)
        except:
            title_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
        
        # Wrap title text
        wrapped_title = textwrap.fill(title, width=30)
        
        # Draw title
        title_y = y_offset + thumb_size + 80
        draw.text(
            (width // 2, title_y),
            wrapped_title,
            font=title_font,
            fill=(255, 255, 255),
            anchor="mm"
        )
        
        # Draw duration and mood
        info_text = f"🕐 {duration}  •  🎵 {mood.upper()}"
        info_y = title_y + 100
        draw.text(
            (width // 2, info_y),
            info_text,
            font=info_font,
            fill=(177, 177, 177),
            anchor="mm"
        )
        
        # Add Spotify green accent bar at bottom
        accent_color = (29, 185, 84)  # Spotify green
        draw.rectangle(
            [(0, height - 20), (width, height)],
            fill=accent_color
        )
        
        # Add play icon or accent
        draw.text(
            (width // 2, height - 10),
            "▶ NOW PLAYING",
            font=info_font,
            fill=(255, 255, 255),
            anchor="mm"
        )
        
        return background
    
    except Exception as e:
        print(f"Spotify Thumbnail Creation Error: {e}")
        return None


def create_spotify_thumbnail_simple(title, duration, mood="chill"):
    """
    Create a simple Spotify-styled thumbnail without needing to download images
    
    Args:
        title: Song title
        duration: Song duration
        mood: Autoplay mood
    
    Returns:
        PIL Image object
    """
    try:
        width, height = 1080, 1080
        
        # Create dark background with gradient effect
        background = Image.new('RGB', (width, height), color=(20, 20, 20))
        draw = ImageDraw.Draw(background)
        
        # Create gradient overlay effect (Spotify colors)
        for y in range(height):
            ratio = y / height
            r = int(20 + (40 * ratio))
            g = int(20 + (30 * ratio))
            b = int(20 + (50 * ratio))
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # Add decorative shapes
        accent_color = (29, 185, 84)  # Spotify green
        
        # Draw circles for decoration
        circle_size = 200
        draw.ellipse(
            [(width - circle_size, -50), (width + 50, circle_size - 50)],
            fill=accent_color,
            outline=None
        )
        draw.ellipse(
            [(-50, height - circle_size), (circle_size - 50, height + 50)],
            fill=(29, 185, 84),
            outline=None
        )
        
        # Add blur effect to decorations
        background = background.filter(ImageFilter.GaussianBlur(radius=20))
        
        # Re-add the text on top
        draw = ImageDraw.Draw(background)
        
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        except:
            title_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
        
        # Draw central content
        center_y = height // 2
        
        # Wrap and draw title
        wrapped_title = textwrap.fill(title, width=25)
        draw.text(
            (width // 2, center_y - 100),
            wrapped_title,
            font=title_font,
            fill=(255, 255, 255),
            anchor="mm"
        )
        
        # Draw duration and mood
        info_text = f"🕐 {duration}  •  {mood.upper()}"
        draw.text(
            (width // 2, center_y + 100),
            info_text,
            font=info_font,
            fill=(177, 177, 177),
            anchor="mm"
        )
        
        # Add Spotify green bar at bottom
        draw.rectangle(
            [(0, height - 40), (width, height)],
            fill=accent_color
        )
        
        draw.text(
            (width // 2, height - 20),
            "▶ NOW PLAYING",
            font=info_font,
            fill=(255, 255, 255),
            anchor="mm"
        )
        
        return background
    
    except Exception as e:
        print(f"Simple Spotify Thumbnail Error: {e}")
        return None


def save_image_to_bytes(image):
    """Convert PIL Image to bytes"""
    try:
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG', quality=95)
        img_bytes.seek(0)
        return img_bytes
    except Exception as e:
        print(f"Image Save Error: {e}")
        return None
      
