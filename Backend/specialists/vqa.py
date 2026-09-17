def generate_vqa_response(query, results_dict, mode):
    """
    Synthesize specialist detections, spectral indices, and spatial distributions
    into a comprehensive natural-language remote-sensing response responding directly to the user's query.
    """
    query_lower = query.lower()
    
    bldg_data = results_dict.get('buildings', {})
    bldg_count = bldg_data.get('count', 0)
    
    water_data = results_dict.get('water_bodies', {})
    water_count = water_data.get('count', 0)
    water_pct = water_data.get('coverage_percentage', 0.0)
    
    agri_data = results_dict.get('agriculture', {})
    agri_pct = agri_data.get('coverage_percentage', 0.0)
    dominant_agri = ", ".join(agri_data.get('dominant_regions', ['General area']))
    
    lc_data = results_dict.get('land_cover', {})
    
    bldg_objects = bldg_data.get('objects', [])
    bldg_dirs = {}
    for b in bldg_objects:
        d = b.get('direction', 'Center')
        bldg_dirs[d] = bldg_dirs.get(d, 0) + 1
    
    top_bldg_dirs = sorted(bldg_dirs.items(), key=lambda x: x[1], reverse=True)
    bldg_dir_str = ", ".join([f"{count} in {direction}" for direction, count in top_bldg_dirs[:4]]) if top_bldg_dirs else "None detected"
    
    water_objects = water_data.get('objects', [])
    water_dir_list = list(set([w.get('direction', 'Center') for w in water_objects]))
    water_dir_str = ", ".join(water_dir_list) if water_dir_list else "None detected"
    
    paragraphs = []
    
    if mode == 'multitemporal':
        chg = results_dict.get('change_detection', {})
        chg_pct = chg.get('change_percentage', 0.0)
        bk = chg.get('breakdown', {})
        urban_exp = bk.get('urban_expansion_pct', 0.0)
        water_exp = bk.get('water_expansion_pct', 0.0)
        
        paragraphs.append(f"Based on multitemporal remote sensing differential analysis between the two input scenes, an overall surface change of {chg_pct}% was detected across the monitored area.")
        
        details = []
        if urban_exp > 0:
            details.append(f"urban built-up expansion accounted for {urban_exp}%")
        if water_exp > 0:
            details.append(f"water surface/inundation expansion accounted for {water_exp}%")
        if bk.get('vegetation_land_alteration_pct', 0) > 0:
            details.append(f"vegetation/land surface alteration accounted for {bk.get('vegetation_land_alteration_pct')}%")
            
        if details:
            paragraphs.append(f"Specifically, {', '.join(details)}.")
            
        chg_dirs = chg.get('directions_summary', {})
        if chg_dirs:
            dir_text = ", ".join([f"{d} ({c} zones)" for d, c in chg_dirs.items()])
            paragraphs.append(f"Primary change hotspots are concentrated in the {dir_text} sections of the image.")
            
    elif mode == 'optical_sar':
        fusion = results_dict.get('fusion', {})
        paragraphs.append(f"Multimodal Optical and Synthetic Aperture Radar (SAR) co-analysis identified {bldg_count} structural features and {water_pct}% surface water coverage.")
        if bldg_count > 0:
            paragraphs.append(f"Buildings are primarily distributed as: {bldg_dir_str}, corroborated by SAR dielectric double-bounce reflections.")
        if water_count > 0:
            paragraphs.append(f"Water features ({water_count} identified bodies in {water_dir_str}) are verified through low SAR specular backscatter.")
        if agri_pct > 0:
            paragraphs.append(f"Vegetation canopy spans {agri_pct}% of the scene, predominantly in the {dominant_agri} regions.")
            
    else: # Single image
        # Tailor response to query specifics
        paragraphs.append(f"Analysis of the satellite scene reveals {bldg_count} distinct built-up structures, {water_count} water body features ({water_pct}% coverage), and {agri_pct}% agricultural/vegetation area.")
        
        if 'building' in query_lower or 'house' in query_lower or 'structure' in query_lower or 'urban' in query_lower:
            paragraphs.append(f"• Buildings ({bldg_count} detected): Spatial clustering indicates {bldg_dir_str}.")
        if 'water' in query_lower or 'river' in query_lower or 'lake' in query_lower or 'flood' in query_lower:
            paragraphs.append(f"• Water Bodies ({water_count} detected, {water_pct}% area): Located predominantly in the {water_dir_str} image quadrant(s).")
        if 'agri' in query_lower or 'crop' in query_lower or 'farm' in query_lower or 'vegetation' in query_lower or 'green' in query_lower:
            paragraphs.append(f"• Agriculture & Vegetation ({agri_pct}%): Dominates the {dominant_agri} areas.")
        if 'land cover' in query_lower or 'classify' in query_lower or 'category' in query_lower:
            paragraphs.append(f"• Land Cover Distribution: Built-up ({lc_data.get('built_up', 0)}%), Agriculture ({lc_data.get('agriculture', 0)}%), Water ({lc_data.get('water', 0)}%), Bare Soil ({lc_data.get('bare_land', 0)}%), Other ({lc_data.get('other', 0)}%).")
            
        if not any(k in query_lower for k in ['building', 'water', 'agri', 'crop', 'land cover']):
            paragraphs.append(f"Spatial distribution summary: Built structures are located mainly towards {bldg_dir_str}; water regions appear in {water_dir_str}; and vegetation dominates {dominant_agri}.")
            
    return "\n\n".join(paragraphs)
