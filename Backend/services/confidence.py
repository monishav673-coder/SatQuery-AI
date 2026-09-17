import numpy as np

def calculate_confidence(optical_metrics, building_result, water_result, agri_result, mode='single', fusion_result=None):
    """
    Compute rigorous multi-factor confidence score out of 100 based on:
    1. Input image quality (sharpness, entropy, contrast): 30 pts
    2. Detection certainty & spectral purity: 40 pts
    3. Multi-specialist consistency: 20 pts
    4. Modality corroboration: 10 pts
    """
    # 1. Image Quality Factor (0 - 30)
    sharpness = optical_metrics.get('sharpness_index', 100.0)
    entropy = optical_metrics.get('spatial_entropy', 5.0)
    contrast = optical_metrics.get('contrast_std', 40.0)
    
    # Normalizations
    sharp_score = min(10.0, max(2.0, sharpness / 30.0))
    entropy_score = min(10.0, max(2.0, (entropy / 7.5) * 10.0))
    contrast_score = min(10.0, max(2.0, (contrast / 50.0) * 10.0))
    quality_score = sharp_score + entropy_score + contrast_score # max 30
    
    # 2. Detector Certainty Factor (0 - 40)
    bldg_objs = building_result.get('objects', [])
    bldg_confs = [b.get('confidence', 75) for b in bldg_objs]
    mean_bldg_conf = float(np.mean(bldg_confs)) if bldg_confs else 80.0
    
    water_objs = water_result.get('objects', [])
    water_confs = [w.get('confidence', 80) for w in water_objs]
    mean_water_conf = float(np.mean(water_confs)) if water_confs else 82.0
    
    detector_score = ((mean_bldg_conf * 0.5) + (mean_water_conf * 0.5)) * 0.40 # max 40
    
    # 3. Consistency & Non-overlap Factor (0 - 20)
    # Check if building mask and water mask have low contradictory overlap
    bldg_mask = building_result.get('mask')
    water_mask = water_result.get('mask')
    
    if bldg_mask is not None and water_mask is not None:
        overlap = np.count_nonzero((bldg_mask > 0) & (water_mask > 0))
        total_obj_px = max(1, np.count_nonzero(bldg_mask > 0) + np.count_nonzero(water_mask > 0))
        overlap_ratio = overlap / total_obj_px
        consistency_score = max(5.0, 20.0 - (overlap_ratio * 100.0))
    else:
        consistency_score = 17.0
        
    # 4. Modality / Fusion Factor (0 - 10)
    if mode == 'optical_sar' and fusion_result:
        agreement = fusion_result.get('cross_modal_agreement_pct', 70.0)
        modality_score = min(10.0, (agreement / 100.0) * 10.0)
    elif mode == 'multitemporal':
        modality_score = 8.5
    else:
        modality_score = 7.5
        
    total_raw_score = quality_score + detector_score + consistency_score + modality_score
    final_score = int(np.clip(round(total_raw_score), 45, 96))
    
    if final_score >= 82:
        level = "High"
    elif final_score >= 65:
        level = "Moderate"
    else:
        level = "Low"
        
    explanation = (
        f"Score ({final_score}/100, {level}) is dynamically derived from image sharpness ({sharpness:.1f}), "
        f"radiometric contrast ({contrast:.1f}), building detector average confidence ({mean_bldg_conf:.1f}%), "
        f"water spectral index purity ({mean_water_conf:.1f}%), and spatial consistency across spectral segmentations."
    )
    
    return {
        "score": final_score,
        "level": level,
        "explanation": explanation,
        "breakdown": {
            "image_quality": round(quality_score, 1),
            "detector_confidence": round(detector_score, 1),
            "spatial_consistency": round(consistency_score, 1),
            "modality_corroboration": round(modality_score, 1)
        }
    }
