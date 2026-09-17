import cv2
import numpy as np

def classify_land_cover(rgb_img, building_mask=None, water_mask=None, agri_mask=None):
    """
    Perform multi-class pixel land-cover classification aligned with BigEarthNet remote-sensing taxonomy:
    1. Built-up / Urban Infrastructure
    2. Water Bodies
    3. Agriculture / Vegetation
    4. Bare Soil / Barren Land
    5. Other / Unclassified
    """
    h, w = rgb_img.shape[:2]
    total_pixels = h * w
    
    # Base masks if not passed
    hsv = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2HSV)
    
    if water_mask is None:
        water_mask = cv2.inRange(hsv, np.array([85, 30, 20]), np.array([145, 255, 255]))
    if agri_mask is None:
        agri_mask = cv2.inRange(hsv, np.array([28, 35, 30]), np.array([88, 255, 255]))
    if building_mask is None:
        b1 = cv2.inRange(hsv, np.array([0, 25, 45]), np.array([22, 255, 255]))
        b2 = cv2.inRange(hsv, np.array([0, 0, 130]), np.array([180, 45, 255]))
        building_mask = cv2.bitwise_or(b1, b2)
        
    # Bare soil: brownish / yellowish / sandy hues (HSV H: 10-25, S: 25-150, V: 70-200)
    bare_soil_mask = cv2.inRange(hsv, np.array([8, 15, 60]), np.array([26, 160, 210]))
    
    # Priority rasterization:
    # 1. Water (highest priority)
    # 2. Built-up
    # 3. Agriculture / Vegetation
    # 4. Bare Soil
    # 5. Other
    
    label_map = np.zeros((h, w), dtype=np.uint8) # 0: Other, 1: Water, 2: Built-up, 3: Agri, 4: Bare Soil
    
    # Apply bare soil
    label_map[bare_soil_mask > 0] = 4
    # Apply agriculture
    label_map[agri_mask > 0] = 3
    # Apply built-up
    label_map[building_mask > 0] = 2
    # Apply water
    label_map[water_mask > 0] = 1
    
    water_px = np.count_nonzero(label_map == 1)
    built_px = np.count_nonzero(label_map == 2)
    agri_px = np.count_nonzero(label_map == 3)
    soil_px = np.count_nonzero(label_map == 4)
    other_px = total_pixels - (water_px + built_px + agri_px + soil_px)
    
    water_pct = round((water_px / total_pixels) * 100, 1)
    built_pct = round((built_px / total_pixels) * 100, 1)
    agri_pct = round((agri_px / total_pixels) * 100, 1)
    soil_pct = round((soil_px / total_pixels) * 100, 1)
    other_pct = max(0.0, round(100.0 - (water_pct + built_pct + agri_pct + soil_pct), 1))
    
    return {
        "water": water_pct,
        "built_up": built_pct,
        "agriculture": agri_pct,
        "bare_land": soil_pct,
        "other": other_pct,
        "label_map": label_map,
        "taxonomy": "BigEarthNet-19 Sentinel-2 Remote Sensing Corine Land Cover Mapping"
    }
