import cv2
import numpy as np
from services.image_processing import get_direction_from_coords

def analyze_agriculture(rgb_img):
    """
    Measure agricultural and vegetation coverage from remote sensing imagery.
    Uses Visible Atmospherically Resistant Index (VARI) and Excess Green Index (ExG).
    VARI = (G - R) / (G + R - B + eps)
    ExG = 2*G - R - B
    """
    h, w = rgb_img.shape[:2]
    total_pixels = h * w
    
    r = rgb_img[:, :, 0].astype(np.float32)
    g = rgb_img[:, :, 1].astype(np.float32)
    b = rgb_img[:, :, 2].astype(np.float32)
    
    # Calculate VARI index
    denom = g + r - b
    denom[denom == 0] = 1e-5
    vari = (g - r) / denom
    
    # Calculate ExG index
    exg = (2.0 * g) - r - b
    
    # HSV green filter to ensure true vegetation hue
    hsv = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2HSV)
    green_hue_mask = cv2.inRange(hsv, np.array([28, 35, 30]), np.array([88, 255, 255]))
    
    # Combine indices
    veg_mask = ((vari > 0.04) | (exg > 15)) & (green_hue_mask > 0)
    veg_mask_uint8 = (veg_mask * 255).astype(np.uint8)
    
    # Morphological filtering
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    cleaned = cv2.morphologyEx(veg_mask_uint8, cv2.MORPH_OPEN, kernel)
    
    # Contours of distinct agricultural parcels / vegetation zones
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    veg_objects = []
    veg_pixel_count = 0
    f_id = 1
    
    min_veg_area = max(50, int(total_pixels * 0.0003))
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area >= min_veg_area:
            x, y, bw, bh = cv2.boundingRect(cnt)
            cx = int(x + bw / 2)
            cy = int(y + bh / 2)
            direction = get_direction_from_coords(cx, cy, w, h)
            
            veg_pixel_count += area
            veg_objects.append({
                "id": f"field_{f_id}",
                "bbox": [int(x), int(y), int(bw), int(bh)],
                "center": [cx, cy],
                "area_pixels": int(area),
                "direction": direction
            })
            f_id += 1
            
    coverage_pct = round((np.count_nonzero(cleaned) / total_pixels) * 100, 2)
    
    # Identify dominant directions of vegetation
    directions_count = {}
    for obj in veg_objects:
        d = obj['direction']
        directions_count[d] = directions_count.get(d, 0) + 1
    
    sorted_dirs = sorted(directions_count.items(), key=lambda x: x[1], reverse=True)
    dominant_regions = [d[0] for d in sorted_dirs[:3]] if sorted_dirs else ["Uniform"]
    
    return {
        "coverage_percentage": coverage_pct,
        "fields_count": len(veg_objects),
        "dominant_regions": dominant_regions,
        "objects": veg_objects,
        "mask": cleaned,
        "model_used": "SatQuery Remote-Sensing Agricultural & Vegetation Specialist (VARI/ExG Vegetation Index)"
    }
