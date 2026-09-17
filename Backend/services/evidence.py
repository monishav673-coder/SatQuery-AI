import cv2
import numpy as np
import base64
import os
import uuid

def generate_visual_evidence(base_rgb, building_result=None, water_result=None, agri_result=None, change_result=None, output_dir=None):
    """
    Generate rich visual evidence overlays on top of the original satellite image:
    - Bounding boxes + Labels on Buildings (Red/Cyan)
    - Translucent segmentation mask on Water (Blue)
    - Translucent segmentation mask on Agriculture (Green)
    - Highlighted change mask (Amber/Magenta) for Multitemporal
    - Image-relative 3x3 compass reference grid
    """
    h, w = base_rgb.shape[:2]
    annotated_bgr = cv2.cvtColor(base_rgb, cv2.COLOR_RGB2BGR)
    overlay = annotated_bgr.copy()
    
    # 1. Overlay Agriculture (Green: BGR 40, 180, 40)
    if agri_result and 'mask' in agri_result and agri_result['mask'] is not None:
        mask = agri_result['mask']
        overlay[mask > 0] = [35, 175, 45]
        
    # 2. Overlay Water (Blue: BGR 210, 100, 30)
    if water_result and 'mask' in water_result and water_result['mask'] is not None:
        w_mask = water_result['mask']
        overlay[w_mask > 0] = [215, 110, 25]
        
    # 3. Overlay Multitemporal Changes (Magenta/Amber: BGR 20, 160, 240)
    if change_result and 'mask' in change_result and change_result['mask'] is not None:
        c_mask = change_result['mask']
        overlay[c_mask > 0] = [20, 60, 235]
        
    # Blend semi-transparent masks
    alpha = 0.38
    cv2.addWeighted(overlay, alpha, annotated_bgr, 1 - alpha, 0, annotated_bgr)
    
    # 4. Draw Building Bounding Boxes & IDs
    if building_result and 'objects' in building_result:
        for bldg in building_result['objects']:
            bx, by, bw, bh = bldg['bbox']
            bid = bldg['id']
            conf = bldg.get('confidence', 80)
            
            # Draw Box
            cv2.rectangle(annotated_bgr, (bx, by), (bx + bw, by + bh), (0, 0, 230), 2)
            
            # Label banner
            label_text = f"{bid} ({conf}%)"
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = 0.38
            thickness = 1
            (tw, th), _ = cv2.getTextSize(label_text, font, scale, thickness)
            
            cv2.rectangle(annotated_bgr, (bx, max(0, by - th - 6)), (bx + tw + 6, max(0, by)), (0, 0, 180), -1)
            cv2.putText(annotated_bgr, label_text, (bx + 3, max(0, by - 3)), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)
            
    # 5. Draw Water Body Outlines & Labels
    if water_result and 'objects' in water_result:
        for wobj in water_result['objects']:
            wx, wy, ww, wh = wobj['bbox']
            wid = wobj['id']
            cv2.rectangle(annotated_bgr, (wx, wy), (wx + ww, wy + wh), (230, 120, 0), 2)
            cv2.putText(annotated_bgr, wid, (wx + 4, wy + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            
    # 6. Draw Subtle Compass Grid Lines & Labels
    grid_color = (180, 180, 180)
    # Horizontal grid lines
    cv2.line(annotated_bgr, (0, int(h * 0.33)), (w, int(h * 0.33)), grid_color, 1, cv2.LINE_AA)
    cv2.line(annotated_bgr, (0, int(h * 0.67)), (w, int(h * 0.67)), grid_color, 1, cv2.LINE_AA)
    # Vertical grid lines
    cv2.line(annotated_bgr, (int(w * 0.33), 0), (int(w * 0.33), h), grid_color, 1, cv2.LINE_AA)
    cv2.line(annotated_bgr, (int(w * 0.67), 0), (int(w * 0.67), h), grid_color, 1, cv2.LINE_AA)
    
    # Add subtle compass label in corner
    cv2.putText(annotated_bgr, "N", (w - 24, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 240, 255), 2, cv2.LINE_AA)
    cv2.arrowedLine(annotated_bgr, (w - 20, 42), (w - 20, 14), (0, 240, 255), 2, tipLength=0.4)
    
    # Save image
    evidence_filename = f"evidence_{uuid.uuid4().hex[:10]}.jpg"
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, evidence_filename)
    else:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'uploads', evidence_filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
    cv2.imwrite(file_path, annotated_bgr, [cv2.IMWRITE_JPEG_QUALITY, 92])
    
    # Encode to Base64 Data URI
    _, buffer = cv2.imencode('.jpg', annotated_bgr)
    b64_str = base64.b64encode(buffer).decode('utf-8')
    data_uri = f"data:image/jpeg;base64,{b64_str}"
    
    return {
        "file_path": file_path,
        "filename": evidence_filename,
        "data_uri": data_uri
    }
