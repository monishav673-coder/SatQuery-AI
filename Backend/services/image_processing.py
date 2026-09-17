import cv2
import numpy as np
from PIL import Image
import os

def load_image_cv(image_path):
    """Load image as BGR and RGB numpy arrays safely, handling UTF-8 paths."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")
    
    # Read via PIL to avoid Windows path unicode bugs
    pil_img = Image.open(image_path).convert('RGB')
    rgb_arr = np.array(pil_img)
    bgr_arr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)
    return bgr_arr, rgb_arr, pil_img

def get_image_metadata(image_path):
    """Extract actual image properties."""
    file_size_bytes = os.path.getsize(image_path)
    file_size_kb = round(file_size_bytes / 1024, 2)
    filename = os.path.basename(image_path)
    
    with Image.open(image_path) as img:
        width, height = img.size
        img_format = img.format or os.path.splitext(filename)[1].replace('.', '').upper()
        mode = img.mode
    
    return {
        "filename": filename,
        "width": width,
        "height": height,
        "dimensions": f"{width} × {height} px",
        "file_size_kb": file_size_kb,
        "format": img_format,
        "mode": mode
    }

def get_direction_from_coords(cx, cy, width, height):
    """
    Classify (cx, cy) pixel coordinate into 9-directional image-relative compass sector:
    North-West, North, North-East, West, Center, East, South-West, South, South-East
    """
    x_ratio = cx / max(width, 1)
    y_ratio = cy / max(height, 1)
    
    # Grid sectors: 0-0.33, 0.33-0.67, 0.67-1.0
    if y_ratio < 0.35:
        if x_ratio < 0.35:
            return "North-West"
        elif x_ratio > 0.65:
            return "North-East"
        else:
            return "North"
    elif y_ratio > 0.65:
        if x_ratio < 0.35:
            return "South-West"
        elif x_ratio > 0.65:
            return "South-East"
        else:
            return "South"
    else:
        if x_ratio < 0.35:
            return "West"
        elif x_ratio > 0.65:
            return "East"
        else:
            return "Center"

def calculate_spatial_distribution(objects, width, height):
    """Group detected objects into compass direction bins."""
    directions_count = {
        "North": 0,
        "North-East": 0,
        "East": 0,
        "South-East": 0,
        "South": 0,
        "South-West": 0,
        "West": 0,
        "North-West": 0,
        "Center": 0
    }
    for obj in objects:
        dir_name = obj.get('direction')
        if dir_name in directions_count:
            directions_count[dir_name] += 1
    return directions_count

def align_images_orb(img1_rgb, img2_rgb):
    """Align img2 to img1 using ORB feature matching and Homography."""
    h1, w1 = img1_rgb.shape[:2]
    h2, w2 = img2_rgb.shape[:2]
    
    if (w1, h1) != (w2, h2):
        img2_rgb = cv2.resize(img2_rgb, (w1, h1))
    
    gray1 = cv2.cvtColor(img1_rgb, cv2.COLOR_RGB2GRAY)
    gray2 = cv2.cvtColor(img2_rgb, cv2.COLOR_RGB2GRAY)
    
    orb = cv2.ORB_create(nfeatures=1000)
    kp1, des1 = orb.detectAndCompute(gray1, None)
    kp2, des2 = orb.detectAndCompute(gray2, None)
    
    if des1 is None or des2 is None or len(des1) < 10 or len(des2) < 10:
        return img2_rgb, False
    
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = matcher.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)
    
    good_matches = matches[:max(10, int(len(matches) * 0.3))]
    if len(good_matches) < 4:
        return img2_rgb, False
    
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    
    H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)
    if H is not None:
        aligned = cv2.warpPerspective(img2_rgb, H, (w1, h1))
        return aligned, True
    return img2_rgb, False
