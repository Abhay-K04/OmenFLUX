"""
Script to generate the official high-resolution OmenGlow logo and multi-resolution Windows ICO.
Creates:
  - omenglow/assets/omenglow.png (512x512 with RGBA transparency)
  - omenglow/assets/omenglow.ico (256, 128, 64, 48, 32, 16 sizes for Windows Taskbar & Titlebar)
"""

import math
import os
from PIL import Image, ImageDraw, ImageFilter


def create_omenglow_assets():
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "omenglow", "assets"), exist_ok=True)
    assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "omenglow", "assets"))

    # Master canvas at 1024x1024 for high-fidelity supersampling
    size = 1024
    center = size / 2.0
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # 1. Dark Premium Squircle Base (so it looks crisp on both light & dark taskbars)
    bg_pad = 48
    bg_radius = 210
    bg_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg_layer)

    # Sleek dark carbon backdrop
    bg_draw.rounded_rectangle(
        [bg_pad, bg_pad, size - bg_pad, size - bg_pad],
        radius=bg_radius,
        fill=(14, 16, 26, 240),
        outline=(35, 40, 60, 255),
        width=12,
    )

    # Subtle inner ambient rim
    bg_draw.rounded_rectangle(
        [bg_pad + 12, bg_pad + 12, size - bg_pad - 12, size - bg_pad - 12],
        radius=bg_radius - 12,
        outline=(20, 24, 38, 200),
        width=8,
    )

    img = Image.alpha_composite(img, bg_layer)

    # 2. Outer RGB Neon Ambient Aura (Blurred glow beneath diamond)
    glow_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    d_radius = 330
    diamond_pts = [
        (center, center - d_radius),      # Top
        (center + d_radius, center),      # Right
        (center, center + d_radius),      # Bottom
        (center - d_radius, center),      # Left
    ]

    # Draw vibrant colored arcs for ambient backglow
    # Left / Top-left glow: Pink
    glow_draw.polygon([diamond_pts[0], diamond_pts[3], (center, center)], fill=(255, 0, 90, 160))
    # Top / Top-right glow: Cyan
    glow_draw.polygon([diamond_pts[0], diamond_pts[1], (center, center)], fill=(0, 220, 255, 160))
    # Bottom / Bottom-left glow: Purple
    glow_draw.polygon([diamond_pts[3], diamond_pts[2], (center, center)], fill=(160, 0, 255, 160))
    # Right / Bottom-right glow: Mint
    glow_draw.polygon([diamond_pts[1], diamond_pts[2], (center, center)], fill=(0, 255, 160, 160))

    # Heavy blur for outer aura
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=64))
    img = Image.alpha_composite(img, glow_layer)

    # 3. Precision Beveled Diamond Frame (Outer titanium/stealth bezel)
    bezel_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bezel_draw = ImageDraw.Draw(bezel_layer)

    outer_d = 300
    bezel_pts = [
        (center, center - outer_d),
        (center + outer_d, center),
        (center, center + outer_d),
        (center - outer_d, center),
    ]

    bezel_draw.polygon(bezel_pts, fill=(20, 23, 34, 255), outline=(50, 58, 85, 255), width=8)
    img = Image.alpha_composite(img, bezel_layer)

    # 4. The 4 Illumination Zones (Angled Facets with negative-space channels)
    # The diamond is divided into 4 distinct glowing quadrilaterals:
    # Zone 0: Left (WASD) - Neon Hot Pink / Crimson
    # Zone 1: Top (Center-Left) - Electric Cyan
    # Zone 2: Bottom (Center-Right) - Vibrant Cyber Violet
    # Zone 3: Right (Numpad/Right) - Emerald Mint Green
    facets_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    facets_draw = ImageDraw.Draw(facets_layer)

    # Channel spacing gap between facets
    gap = 22
    inner_d = 265
    core_hole = 55  # Inner core diamond cutout

    # Helper function to compute inset points
    # Zone 0: Left Facet
    # Vertices: Left tip, towards Top, towards Core, towards Bottom
    z0_pts = [
        (center - inner_d + gap, center),
        (center - gap, center - inner_d / 2.0 + gap),
        (center - core_hole, center),
        (center - gap, center + inner_d / 2.0 - gap),
    ]
    facets_draw.polygon(z0_pts, fill=(255, 15, 95, 255))

    # Zone 1: Top Facet (Cyan)
    z1_pts = [
        (center, center - inner_d + gap),
        (center + inner_d / 2.0 - gap, center - gap),
        (center, center - core_hole),
        (center - inner_d / 2.0 + gap, center - gap),
    ]
    facets_draw.polygon(z1_pts, fill=(0, 225, 255, 255))

    # Zone 2: Bottom Facet (Violet/Purple)
    z2_pts = [
        (center, center + inner_d - gap),
        (center - inner_d / 2.0 + gap, center + gap),
        (center, center + core_hole),
        (center + inner_d / 2.0 - gap, center + gap),
    ]
    facets_draw.polygon(z2_pts, fill=(155, 30, 255, 255))

    # Zone 3: Right Facet (Mint Green)
    z3_pts = [
        (center + inner_d - gap, center),
        (center + gap, center + inner_d / 2.0 - gap),
        (center + core_hole, center),
        (center + gap, center - inner_d / 2.0 + gap),
    ]
    facets_draw.polygon(z3_pts, fill=(0, 255, 175, 255))

    # Subtle inner gradient / lighting overlay on facets for 3D glassy sheen
    sheen_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sheen_draw = ImageDraw.Draw(sheen_layer)
    # Top-to-bottom white specular glare
    sheen_draw.polygon(
        [
            (center, center - inner_d),
            (center + inner_d / 1.5, center - inner_d / 3.0),
            (center - inner_d / 1.5, center + inner_d / 4.0),
        ],
        fill=(255, 255, 255, 45),
    )

    facets_combined = Image.alpha_composite(facets_layer, sheen_layer)
    img = Image.alpha_composite(img, facets_combined)

    # 5. Luminous Central Diamond Core (Glowing nexus)
    core_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    core_draw = ImageDraw.Draw(core_layer)

    c_r = 38
    core_pts = [
        (center, center - c_r),
        (center + c_r, center),
        (center, center + c_r),
        (center - c_r, center),
    ]
    # Pure luminous core
    core_draw.polygon(core_pts, fill=(255, 255, 255, 250), outline=(220, 245, 255, 255), width=4)

    # Soft core glow
    core_glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    core_glow_draw = ImageDraw.Draw(core_glow)
    core_glow_draw.polygon(core_pts, fill=(0, 230, 255, 200))
    core_glow = core_glow.filter(ImageFilter.GaussianBlur(radius=18))

    img = Image.alpha_composite(img, core_glow)
    img = Image.alpha_composite(img, core_layer)

    # 6. Save High-Res PNG (512x512)
    png_img = img.resize((512, 512), Image.Resampling.LANCZOS)
    png_path = os.path.join(assets_dir, "omenglow.png")
    png_img.save(png_path, "PNG")
    print(f"[OK] Generated PNG: {png_path} (512x512)")

    # 7. Generate Multi-Resolution Windows ICO
    # Standard Windows icon sizes: 256, 128, 64, 48, 32, 16
    ico_path = os.path.join(assets_dir, "omenglow.ico")
    ico_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(ico_path, format="ICO", sizes=ico_sizes)
    print(f"[OK] Generated Windows ICO: {ico_path} with sizes {ico_sizes}")


if __name__ == "__main__":
    create_omenglow_assets()
