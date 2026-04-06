#!/usr/bin/env python3
"""
Generate icon assets for ADRION 369 UAP systray application.
Creates PNG and ICO files in multiple sizes.
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def create_icon(size: int, output_path: Path) -> Image.Image:
    """Create a circular icon with ADRION branding"""
    # Create image
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Draw outer circle (dark blue border)
    border_width = max(1, size // 32)
    draw.ellipse(
        [(border_width, border_width), (size - border_width, size - border_width)],
        fill=(52, 152, 219),  # Nice blue
        outline=(25, 25, 112),  # Dark blue border
        width=border_width
    )

    # Draw inner accent circle (lighter)
    accent_offset = size // 4
    draw.ellipse(
        [(accent_offset, accent_offset), (size - accent_offset, size - accent_offset)],
        outline=(100, 200, 255),
        width=max(1, border_width // 2)
    )

    # Add "A" text if size is large enough
    if size >= 32:
        try:
            # Try to use a decent font
            font_size = size // 2
            font = ImageFont.load_default()
            text = "A"
            # Get text bounding box
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (size - text_width) // 2
            y = (size - text_height) // 2
            draw.text((x, y), text, fill=(255, 255, 255), font=font)
        except:
            pass

    img.save(output_path)
    print(f"✓ Generated {output_path.name} ({size}x{size})")
    return img

def main():
    """Generate all icon sizes"""
    icon_dir = Path(__file__).parent / "uap" / "desktop" / "systray"
    icon_dir.mkdir(parents=True, exist_ok=True)

    print("ADRION 369 - Icon Generator")
    print("=" * 50)

    # Generate PNG sizes
    sizes = [16, 32, 48, 64, 128, 256]
    for size in sizes:
        output_file = icon_dir / f"icon-{size}x{size}.png"
        create_icon(size, output_file)

    # Create ICO from 256x256 PNG
    img_256 = Image.open(icon_dir / "icon-256x256.png")
    ico_path = icon_dir / "icon.ico"
    img_256.save(ico_path, format='ICO', sizes=[(size, size) for size in sizes])
    print(f"✓ Generated {ico_path.name} (multi-resolution)")

    # Create a simple PNG for the systray default
    default_png = icon_dir / "icon.png"
    Image.open(icon_dir / "icon-32x32.png").save(default_png)
    print(f"✓ Generated {default_png.name} (32x32 default)")

    print("=" * 50)
    print("✓ All icons generated successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
