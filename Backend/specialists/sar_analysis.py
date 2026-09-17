import cv2
import numpy as np

def analyze_sar(sar_img):
    """
    Process SAR (Synthetic Aperture Radar) backscatter intensity imagery.
    Detects high backscatter (double-bounce manmade structures), moderate backscatter (volume scattering vegetation),
    and low backscatter (smooth specular water surfaces).
    """
    if len(sar_img.shape) == 3:
        sar_gray = cv2.cvtColor(sar_img, cv2.COLOR_RGB2GRAY)
    else:
        sar_gray = sar_img
        
    h, w = sar_gray.shape[:2]
    total_pixels = h * w
    
    # 1. Speckle noise filtering (Median + Bilateral filter proxy for Lee filter)
    filtered = cv2.bilateralFilter(sar_gray, d=5, sigmaColor=50, sigmaSpace=50)
    
    # Equivalent Number of Looks (ENL) / Speckle index estimation
    mean_int = float(np.mean(filtered))
    std_int = float(np.std(filtered))
    speckle_index = round((std_int / max(mean_int, 1e-5)), 3)
    
    # 2. Backscatter segmentation
    # High backscatter: Corner reflection / built-up structures (> 200)
    high_backscatter_mask = filtered > 195
    # Very low backscatter: Specular reflectance on calm water / smooth roads (< 35)
    low_backscatter_mask = filtered < 35
    # Moderate backscatter: Rough soil / canopy volume scattering (35 - 195)
    moderate_backscatter_mask = (filtered >= 35) & (filtered <= 195)
    
    high_pct = round((np.count_nonzero(high_backscatter_mask) / total_pixels) * 100, 2)
    low_pct = round((np.count_nonzero(low_backscatter_mask) / total_pixels) * 100, 2)
    mod_pct = round((np.count_nonzero(moderate_backscatter_mask) / total_pixels) * 100, 2)
    
    return {
        "modality": "SAR (Synthetic Aperture Radar)",
        "mean_intensity": round(mean_int, 2),
        "speckle_index": speckle_index,
        "high_backscatter_urban_pct": high_pct,
        "low_backscatter_water_pct": low_pct,
        "diffuse_vegetation_soil_pct": mod_pct,
        "high_mask": high_backscatter_mask.astype(np.uint8) * 255,
        "low_mask": low_backscatter_mask.astype(np.uint8) * 255,
        "model_used": "SatQuery SAR Radar Backscatter & Speckle Filtering Specialist"
    }
