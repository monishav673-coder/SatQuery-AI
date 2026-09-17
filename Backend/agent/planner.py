def plan_tasks(query, mode):
    """
    Decompose natural language query and analysis mode into a directed sequence of execution tasks.
    """
    q = (query or "").lower().strip()
    tasks = []
    
    # Fundamental preprocessing tasks
    tasks.append("validate_inputs")
    tasks.append("image_preprocessing")
    
    if mode == "multitemporal":
        tasks.append("co_registration_alignment")
        tasks.append("multitemporal_difference_analysis")
        tasks.append("change_classification")
        tasks.append("spatial_change_mapping")
    elif mode == "optical_sar":
        tasks.append("optical_radiometric_analysis")
        tasks.append("sar_backscatter_speckle_analysis")
        tasks.append("optical_sar_feature_fusion")
        tasks.append("building_detection")
        tasks.append("water_detection")
        tasks.append("agriculture_analysis")
    else: # single or location
        tasks.append("optical_radiometric_analysis")
        
        # Determine specific focus from query
        has_bldg = any(k in q for k in ['building', 'house', 'structure', 'urban', 'settlement', 'city', 'built', 'all', 'where', 'identify', 'analyze']) or len(q) < 5
        has_water = any(k in q for k in ['water', 'river', 'lake', 'pond', 'ocean', 'flood', 'all', 'where', 'identify', 'analyze']) or len(q) < 5
        has_agri = any(k in q for k in ['agri', 'crop', 'farm', 'vegetation', 'green', 'forest', 'field', 'all', 'where', 'identify', 'analyze']) or len(q) < 5
        
        if has_bldg:
            tasks.append("building_detection")
        if has_water:
            tasks.append("water_detection")
        if has_agri:
            tasks.append("agriculture_analysis")
            
        tasks.append("land_cover_classification")
        tasks.append("spatial_direction_mapping")
        
    tasks.append("confidence_evaluation")
    tasks.append("visual_evidence_generation")
    tasks.append("vision_language_synthesis")
    
    return tasks
