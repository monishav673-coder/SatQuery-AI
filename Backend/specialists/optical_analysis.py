import cv2
import numpy as np

def analyze_optical(rgb_img):
    """
    Extract radiometric, spectral reflectance, and optical texture metrics.
    """
    h, w = rgb_img.shape[:2]
    gray = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2GRAY)
    
    mean_val = float(np.mean(gray))
    std_val = float(np.std(gray))
    
    # Calculate image entropy (texture complexity)
    hist, _ = np.histogram(gray, bins=256, range=(0, 256), density=True)
    hist = hist[hist > 0]
    entropy = -np.sum(hist * np.log2(hist))
    
    # Sharpness via Laplacian variance
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    
    return {
        "modality": "Optical (Multispectral/RGB)",
        "mean_radiance": round(mean_val, 2),
        "contrast_std": round(std_val, 2),
        "spatial_entropy": round(entropy, 2),
        "sharpness_index": round(laplacian_var, 2),
        "model_used": "SatQuery Optical Spectral & Radiometric Analyzer"
    }
