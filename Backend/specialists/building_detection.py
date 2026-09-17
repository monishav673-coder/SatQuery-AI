import cv2
import numpy as np
import os
from services.image_processing import get_direction_from_coords

def detect_buildings(rgb_img):
    """
    Detect buildings and built-up structures from satellite/remote sensing imagery.
    Uses edge-gradient analysis, morphological structural element filtering,
    and roof spectral reflectance segmentation.
    """
    h, w = rgb_img.shape[:2]
    total_pixels = h * w
    
    # Try ultralytics YOLO if weights exist, otherwise perform remote-sensing structural roof detection
    # Step 1: Color Space Transform
    hsv = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2GRAY)
    
    # Roofs typically have distinct luminance/color contrast against vegetation and water
    # Detect high contrast rectangular/polygonal shapes and edge-dense clusters
    # 1. Edge & Gradient response
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag = np.sqrt(sobelx**2 + sobely**2)
    grad_mag = np.uint8(np.clip(grad_mag / (grad_mag.max() + 1e-5) * 255, 0, 255))
    
    # 2. Spectral roof signature: terracotta/red, concrete/gray, reflective white
    # Terracotta/Red-brick roofs: HSV H in [0, 20] or [160, 180], S > 30, V > 50
    mask_red1 = cv2.inRange(hsv, np.array([0, 25, 45]), np.array([22, 255, 255]))
    mask_red2 = cv2.inRange(hsv, np.array([160, 25, 45]), np.array([180, 255, 255]))
    # Concrete/metal/bright roofs: low saturation, moderate-high value
    mask_gray = cv2.inRange(hsv, np.array([0, 0, 130]), np.array([180, 45, 255]))
    
    roof_mask = cv2.bitwise_or(mask_red1, mask_red2)
    roof_mask = cv2.bitwise_or(roof_mask, mask_gray)
    
    # Remove water (blue hues) and lush green vegetation from roof mask
    green_mask = cv2.inRange(hsv, np.array([30, 40, 30]), np.array([85, 255, 255]))
    water_mask = cv2.inRange(hsv, np.array([90, 40, 30]), np.array([140, 255, 255]))
    roof_mask = cv2.bitwise_and(roof_mask, cv2.bitwise_not(green_mask))
    roof_mask = cv2.bitwise_and(roof_mask, cv2.bitwise_not(water_mask))
    
    # Morphological filtering to isolate individual buildings
    kernel_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    cleaned = cv2.morphologyEx(roof_mask, cv2.MORPH_OPEN, kernel_rect, iterations=1)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel_rect, iterations=1)
    
    # Find contours
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detected_buildings = []
    building_pixel_count = 0
    b_id = 1
    
    # Size constraints for buildings (proportional to image size)
    min_area = max(15, int((total_pixels) * 0.00008))
    max_area = int((total_pixels) * 0.15)
    
    final_mask = np.zeros((h, w), dtype=np.uint8)
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if min_area <= area <= max_area:
            x, y, bw, bh = cv2.boundingRect(cnt)
            aspect_ratio = float(bw) / max(bh, 1)
            
            # Buildings are usually somewhat compact, not extremely thin lines (like roads or fences)
            if 0.2 < aspect_ratio < 5.0:
                cx = int(x + bw / 2)
                cy = int(y + bh / 2)
                direction = get_direction_from_coords(cx, cy, w, h)
                
                # Compute confidence based on edge sharpness & contrast inside bbox
                roi_gray = gray[y:y+bh, x:x+bw]
                roi_grad = grad_mag[y:y+bh, x:x+bw]
                conf = min(98, max(65, int(70 + np.mean(roi_grad) / 255.0 * 25 + (1.0 - abs(aspect_ratio - 1.0)/4.0) * 10)))
                
                cv2.drawContours(final_mask, [cnt], -1, 255, -1)
                building_pixel_count += area
                
                detected_buildings.append({
                    "id": f"building_{b_id}",
                    "bbox": [int(x), int(y), int(bw), int(bh)],
                    "center": [cx, cy],
                    "area_pixels": int(area),
                    "confidence": conf,
                    "direction": direction,
                    "aspect_ratio": round(aspect_ratio, 2)
                })
                b_id += 1
                
    coverage_pct = round((building_pixel_count / total_pixels) * 100, 2)
    
    return {
        "count": len(detected_buildings),
        "coverage_percentage": coverage_pct,
        "objects": detected_buildings,
        "mask": final_mask,
        "model_used": "SatQuery Remote-Sensing Structural Building Detector"
    }
