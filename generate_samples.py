"""
Generate realistic sample remote sensing satellite imagery for testing and 1-click demo:
- single_sample.jpg: Multi-feature satellite scene (water, agricultural fields, built-up residential structures)
- optical_sample.jpg: Optical satellite scene (green vegetation, river channel, city grid)
- sar_sample.jpg: Co-registered SAR backscatter image with speckle pattern and structural radar reflection
- before_sample.jpg: Pre-development / pre-flood satellite scene
- after_sample.jpg: Post-development / post-flood scene showing new buildings and expanded water/flood region
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

os.makedirs('samples', exist_ok=True)

def generate_single_sample():
    # 512x512 satellite scene
    w, h = 512, 512
    img = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Base terrain (warm soil & light vegetation: RGB ~ (145, 160, 110))
    for y in range(h):
        for x in range(w):
            noise = (np.sin(x/15.0) * np.cos(y/15.0) * 15) + (np.sin(x/5.0) * 5)
            img[y, x] = [
                int(np.clip(135 + noise + np.random.randint(-5, 5), 0, 255)),
                int(np.clip(155 + noise + np.random.randint(-5, 5), 0, 255)),
                int(np.clip(105 + noise + np.random.randint(-5, 5), 0, 255))
            ]

    pil_img = Image.fromarray(img)
    draw = ImageDraw.Draw(pil_img)

    # 1. Agricultural Fields (Green rectangular patches in South & East)
    draw.rectangle([280, 260, 480, 360], fill=(45, 130, 45), outline=(30, 95, 30))
    draw.rectangle([300, 380, 490, 490], fill=(55, 150, 50), outline=(35, 110, 35))
    draw.rectangle([40, 320, 200, 480], fill=(70, 160, 60), outline=(45, 115, 40))

    # 2. Water Body / River (Meandering river in North-West to South-East)
    river_points = [
        (0, 80), (70, 95), (140, 130), (190, 180), (220, 230),
        (230, 280), (220, 330), (230, 400), (245, 511)
    ]
    for i in range(len(river_points)-1):
        draw.line([river_points[i], river_points[i+1]], fill=(30, 90, 175), width=28)
    # Lake in North-West
    draw.ellipse([30, 15, 140, 75], fill=(25, 80, 165), outline=(20, 60, 130))

    # 3. Built-up / Urban settlements (Clusters of buildings with roofs in North & North-East)
    building_coords = [
        # North cluster
        (190, 20, 230, 50), (240, 15, 275, 45), (195, 60, 230, 85), (245, 55, 280, 90),
        # North-East cluster
        (320, 30, 360, 65), (375, 25, 420, 55), (435, 35, 475, 70), (330, 80, 370, 115),
        (385, 75, 425, 110), (440, 85, 485, 120), (350, 130, 395, 165), (410, 125, 460, 160),
        # Center-East cluster
        (320, 180, 365, 220), (380, 175, 425, 215), (440, 185, 480, 225),
        # West side cluster
        (20, 200, 60, 235), (75, 195, 120, 230), (30, 250, 70, 285)
    ]
    roof_colors = [(180, 70, 60), (195, 85, 65), (160, 165, 175), (210, 90, 70), (170, 175, 180)]
    for idx, (x1, y1, x2, y2) in enumerate(building_coords):
        col = roof_colors[idx % len(roof_colors)]
        draw.rectangle([x1, y1, x2, y2], fill=col, outline=(90, 90, 90), width=1)

    pil_img = pil_img.filter(ImageFilter.GaussianBlur(radius=0.4))
    pil_img.save('samples/single_sample.jpg', quality=95)
    print("Saved samples/single_sample.jpg")

def generate_optical_sar_pair():
    w, h = 512, 512
    # Optical: High color differentiation
    opt = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            opt[y, x] = [130, 150, 100]
    opt_pil = Image.fromarray(opt)
    d_opt = ImageDraw.Draw(opt_pil)
    # Optical vegetation
    d_opt.rectangle([50, 50, 220, 240], fill=(40, 140, 45))
    d_opt.rectangle([280, 50, 470, 240], fill=(50, 155, 55))
    # Optical river
    d_opt.rectangle([210, 0, 270, 512], fill=(25, 85, 180))
    # Optical buildings
    for y in range(280, 470, 45):
        for x in range(60, 460, 55):
            d_opt.rectangle([x, y, x+35, y+30], fill=(185, 80, 65), outline=(70, 70, 70))
    opt_pil.save('samples/optical_sample.jpg', quality=95)
    print("Saved samples/optical_sample.jpg")

    # SAR: Radar backscatter intensity
    sar = np.random.gamma(shape=2.0, scale=25.0, size=(h, w)).astype(np.uint8)
    sar_pil = Image.fromarray(sar, mode='L')
    d_sar = ImageDraw.Draw(sar_pil)
    # SAR Water: very low backscatter
    d_sar.rectangle([210, 0, 270, 512], fill=12)
    # SAR Vegetation: moderate volume scattering
    d_sar.rectangle([50, 50, 220, 240], fill=100)
    d_sar.rectangle([280, 50, 470, 240], fill=110)
    # SAR Urban: strong dihedral double-bounce
    for y in range(280, 470, 45):
        for x in range(60, 460, 55):
            d_sar.rectangle([x, y, x+35, y+30], fill=245)
    sar_pil = sar_pil.convert('RGB')
    sar_pil.save('samples/sar_sample.jpg', quality=95)
    print("Saved samples/sar_sample.jpg")

def generate_multitemporal_pair():
    w, h = 512, 512
    # Before Image
    before = Image.new('RGB', (w, h), color=(140, 160, 115))
    d_before = ImageDraw.Draw(before)
    d_before.rectangle([100, 100, 400, 400], fill=(55, 145, 50))
    d_before.line([(450, 0), (430, 250), (460, 512)], fill=(30, 90, 170), width=16)
    d_before.rectangle([40, 40, 75, 70], fill=(175, 80, 65))
    d_before.rectangle([90, 45, 120, 75], fill=(180, 85, 70))
    before.save('samples/before_sample.jpg', quality=95)
    print("Saved samples/before_sample.jpg")

    # After Image: Urban expansion + flooded area
    after = before.copy()
    d_after = ImageDraw.Draw(after)
    new_buildings = [
        (130, 130, 175, 170), (190, 130, 240, 175), (260, 135, 310, 180), (330, 140, 380, 185),
        (135, 200, 180, 245), (200, 205, 250, 250), (270, 200, 320, 245), (340, 210, 385, 255),
        (140, 280, 190, 330), (210, 285, 260, 335), (280, 280, 330, 330), (345, 285, 390, 335)
    ]
    for x1, y1, x2, y2 in new_buildings:
        d_after.rectangle([x1, y1, x2, y2], fill=(200, 90, 70), outline=(80, 80, 80))
    d_after.ellipse([380, 320, 500, 480], fill=(25, 75, 160))
    after.save('samples/after_sample.jpg', quality=95)
    print("Saved samples/after_sample.jpg")

if __name__ == '__main__':
    generate_single_sample()
    generate_optical_sar_pair()
    generate_multitemporal_pair()
    print("Sample generation complete!")
