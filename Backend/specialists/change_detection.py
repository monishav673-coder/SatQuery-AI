import cv2
import numpy as np
from services.image_processing import align_images_orb, get_direction_from_coords

def detect_multitemporal_changes(before_rgb, after_rgb):
    """
    Perform multitemporal change detection between 'before' and 'after' satellite scenes.
    Aligns imagery, calculates absolute structural difference, segments change masks,
    and categorizes change regions (Built-up expansion, Flood/Water expansion, Vegetation change).
    """
    h, w = before_rgb.shape[:2]
    total_pixels = h * w
    
    # 1. Co-registration / alignment
    aligned_after, is_aligned = align_images_orb(before_rgb, after_rgb)
    
    # 2. Convert to LAB and Grayscale for luminance & color difference
    before_lab = cv2.cvtColor(before_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    after_lab = cv2.cvtColor(aligned_after, cv2.COLOR_RGB2LAB).astype(np.float32)
    
    # Delta E color distance
    delta_e = np.sqrt(np.sum((before_lab - after_lab)**2, axis=2))
    
    # Absolute difference in grayscale
    before_gray = cv2.cvtColor(before_rgb, cv2.COLOR_RGB2GRAY)
    after_gray = cv2.cvtColor(aligned_after, cv2.COLOR_RGB2GRAY)
    diff_gray = cv2.absdiff(before_gray, after_gray)
    
    # Combine differences
    diff_combined = (delta_e * 0.6) + (diff_gray * 0.4)
    diff_uint8 = np.uint8(np.clip(diff_combined, 0, 255))
    
    # Otsu or adaptive threshold for significant remote-sensing changes
    _, change_mask = cv2.threshold(diff_uint8, 38, 255, cv2.THRESH_BINARY)
    
    # Morphological noise filtering
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    cleaned_mask = cv2.morphologyEx(change_mask, cv2.MORPH_OPEN, kernel)
    cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel)
    
    change_pixels = np.count_nonzero(cleaned_mask)
    change_percentage = round((change_pixels / total_pixels) * 100, 2)
    
    # Classify changed areas
    # New buildings in after: bright/red in after, not in before
    hsv_after = cv2.cvtColor(aligned_after, cv2.COLOR_RGB2HSV)
    hsv_before = cv2.cvtColor(before_rgb, cv2.COLOR_RGB2HSV)
    
    # Water mask after
    water_after = cv2.inRange(hsv_after, np.array([85, 30, 20]), np.array([145, 255, 255]))
    water_before = cv2.inRange(hsv_before, np.array([85, 30, 20]), np.array([145, 255, 255]))
    new_water_mask = cv2.bitwise_and(cleaned_mask, cv2.bitwise_and(water_after, cv2.bitwise_not(water_before)))
    
    # Built-up mask after
    bldg_after1 = cv2.inRange(hsv_after, np.array([0, 25, 45]), np.array([22, 255, 255]))
    bldg_after2 = cv2.inRange(hsv_after, np.array([0, 0, 130]), np.array([180, 45, 255]))
    bldg_after = cv2.bitwise_or(bldg_after1, bldg_after2)
    new_bldg_mask = cv2.bitwise_and(cleaned_mask, bldg_after)
    
    new_water_px = np.count_nonzero(new_water_mask)
    new_bldg_px = np.count_nonzero(new_bldg_mask)
    other_change_px = max(0, change_pixels - new_water_px - new_bldg_px)
    
    # Contours of major change clusters
    contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    change_regions = []
    min_change_area = max(40, int(total_pixels * 0.0002))
    
    c_id = 1
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area >= min_change_area:
            x, y, bw, bh = cv2.boundingRect(cnt)
            cx = int(x + bw / 2)
            cy = int(y + bh / 2)
            direction = get_direction_from_coords(cx, cy, w, h)
            
            # Determine specific change nature for this cluster
            roi_new_water = new_water_mask[y:y+bh, x:x+bw]
            roi_new_bldg = new_bldg_mask[y:y+bh, x:x+bw]
            
            if np.count_nonzero(roi_new_water) > (area * 0.3):
                c_type = "Hydrological / Water Expansion / Inundation"
            elif np.count_nonzero(roi_new_bldg) > (area * 0.25):
                c_type = "New Built-up / Urban Expansion"
            else:
                c_type = "Vegetation / Land-surface Modification"
                
            change_regions.append({
                "id": f"change_{c_id}",
                "type": c_type,
                "bbox": [int(x), int(y), int(bw), int(bh)],
                "center": [cx, cy],
                "area_pixels": int(area),
                "direction": direction
            })
            c_id += 1
            
    # Direction summary
    directions_summary = {}
    for cr in change_regions:
        d = cr['direction']
        directions_summary[d] = directions_summary.get(d, 0) + 1
        
    return {
        "change_percentage": change_percentage,
        "is_aligned": is_aligned,
        "regions_count": len(change_regions),
        "breakdown": {
            "urban_expansion_pct": round((new_bldg_px / max(total_pixels, 1)) * 100, 2),
            "water_expansion_pct": round((new_water_px / max(total_pixels, 1)) * 100, 2),
            "vegetation_land_alteration_pct": round((other_change_px / max(total_pixels, 1)) * 100, 2)
        },
        "change_regions": change_regions,
        "directions_summary": directions_summary,
        "mask": cleaned_mask,
        "aligned_after": aligned_after,
        "model_used": "SatQuery Multitemporal Differential Change Specialist (ORB Co-registration + Delta-E Radiometric Analysis)"
    }
