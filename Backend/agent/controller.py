import os
import uuid
from agent.planner import plan_tasks
from agent.router import SpecialistRouter
from services.image_processing import load_image_cv, get_image_metadata, calculate_spatial_distribution
from services.confidence import calculate_confidence
from services.evidence import generate_visual_evidence
from database import save_analysis

class AgentController:
    """
    Master Agentic AI Controller for SatQuery AI.
    Executes dynamic multi-specialist remote sensing workflows based on query & imagery.
    """
    def __init__(self):
        self.router = SpecialistRouter()

    def run_analysis(self, user_email, mode, query, file_paths, location_meta=None):
        analysis_id = f"SQ-{uuid.uuid4().hex[:8].upper()}"
        execution_steps = []
        specialists_used = []
        
        # 1. Planning
        tasks = plan_tasks(query, mode)
        execution_steps.append("Input validated and query intent parsed")
        execution_steps.append(f"Generated task plan with {len(tasks)} sub-stages")
        
        # 2. Image Loading & Preprocessing
        primary_path = file_paths.get('primary') or file_paths.get('optical') or file_paths.get('before')
        if not primary_path or not os.path.exists(primary_path):
            raise FileNotFoundError("Primary satellite image file is missing or invalid.")
            
        bgr_primary, rgb_primary, pil_primary = load_image_cv(primary_path)
        img_meta = get_image_metadata(primary_path)
        h, w = rgb_primary.shape[:2]
        execution_steps.append(f"Preprocessed input scene ({w}×{h} px, {img_meta['format']})")
        
        # Specialist Results Storage
        optical_metrics = {}
        sar_metrics = {}
        fusion_metrics = {}
        building_result = {"count": 0, "objects": [], "coverage_percentage": 0.0}
        water_result = {"count": 0, "objects": [], "coverage_percentage": 0.0}
        agri_result = {"coverage_percentage": 0.0, "dominant_regions": [], "objects": []}
        land_cover_result = {"agriculture": 0.0, "water": 0.0, "built_up": 0.0, "bare_land": 0.0, "other": 100.0}
        change_result = {}
        
        # 3. Optical Analysis
        optical_spec = self.router.get_specialist("optical")
        optical_metrics = optical_spec(rgb_primary)
        specialists_used.append("Optical Radiometric Specialist")
        execution_steps.append(f"Radiometric analysis completed (Sharpness: {optical_metrics['sharpness_index']}, Entropy: {optical_metrics['spatial_entropy']})")
        
        # 4. Mode-Specific Specialist Execution
        if mode == "multitemporal":
            after_path = file_paths.get('after')
            if not after_path or not os.path.exists(after_path):
                raise FileNotFoundError("Multitemporal mode requires both 'Before' and 'After' satellite scenes.")
            _, rgb_after, _ = load_image_cv(after_path)
            
            change_spec = self.router.get_specialist("change_detection")
            change_result = change_spec(rgb_primary, rgb_after)
            specialists_used.append("Multitemporal Differential Change Specialist")
            execution_steps.append(f"Differential change detection executed (Overall surface change: {change_result['change_percentage']}%)")
            
            # Extract building and water features on the 'after' scene as well
            bldg_spec = self.router.get_specialist("building")
            building_result = bldg_spec(change_result.get('aligned_after', rgb_after))
            water_spec = self.router.get_specialist("water")
            water_result = water_spec(change_result.get('aligned_after', rgb_after))
            agri_spec = self.router.get_specialist("agriculture")
            agri_result = agri_spec(change_result.get('aligned_after', rgb_after))
            
        elif mode == "optical_sar":
            sar_path = file_paths.get('sar')
            if not sar_path or not os.path.exists(sar_path):
                raise FileNotFoundError("Optical + SAR mode requires both Optical and SAR satellite images.")
            _, rgb_sar, _ = load_image_cv(sar_path)
            
            sar_spec = self.router.get_specialist("sar")
            sar_metrics = sar_spec(rgb_sar)
            specialists_used.append("SAR Radar Backscatter Specialist")
            execution_steps.append(f"SAR backscatter analysis complete (High-reflectance urban: {sar_metrics['high_backscatter_urban_pct']}%, Specular water: {sar_metrics['low_backscatter_water_pct']}%)")
            
            # Optical Feature Detectors
            bldg_spec = self.router.get_specialist("building")
            building_result = bldg_spec(rgb_primary)
            water_spec = self.router.get_specialist("water")
            water_result = water_spec(rgb_primary)
            agri_spec = self.router.get_specialist("agriculture")
            agri_result = agri_spec(rgb_primary)
            specialists_used.extend(["Building Detection Specialist", "Water Body Segmentation Specialist", "Agricultural Specialist"])
            
            # Fusion
            fusion_spec = self.router.get_specialist("fusion")
            fusion_metrics = fusion_spec(
                {"buildings": building_result, "water_bodies": water_result},
                sar_metrics, rgb_primary, rgb_sar
            )
            specialists_used.append("Optical-SAR Feature Fusion Specialist")
            execution_steps.append(f"Cross-modal fusion completed (Agreement: {fusion_metrics['cross_modal_agreement_pct']}%)")
            
        else: # Single Image or Location
            if "building_detection" in tasks:
                bldg_spec = self.router.get_specialist("building")
                building_result = bldg_spec(rgb_primary)
                specialists_used.append("Building Detection Specialist")
                execution_steps.append(f"Building detection completed ({building_result['count']} structures detected)")
                
            if "water_detection" in tasks:
                water_spec = self.router.get_specialist("water")
                water_result = water_spec(rgb_primary)
                specialists_used.append("Water Body Segmentation Specialist")
                execution_steps.append(f"Water segmentation completed ({water_result['count']} features, {water_result['coverage_percentage']}% coverage)")
                
            if "agriculture_analysis" in tasks:
                agri_spec = self.router.get_specialist("agriculture")
                agri_result = agri_spec(rgb_primary)
                specialists_used.append("Agricultural & Vegetation Specialist")
                execution_steps.append(f"Vegetation index evaluated ({agri_result['coverage_percentage']}% canopy cover)")
                
        # 5. Land Cover Classification (BigEarthNet)
        lc_spec = self.router.get_specialist("land_cover")
        land_cover_result = lc_spec(
            rgb_primary,
            building_mask=building_result.get('mask'),
            water_mask=water_result.get('mask'),
            agri_mask=agri_result.get('mask')
        )
        specialists_used.append("BigEarthNet Land Cover Classifier")
        execution_steps.append("5-class land-cover classification mapped")
        
        # 6. Spatial Orientation
        bldg_directions = calculate_spatial_distribution(building_result.get('objects', []), w, h)
        water_directions = calculate_spatial_distribution(water_result.get('objects', []), w, h)
        execution_steps.append("9-directional spatial orientation matrix computed")
        
        # 7. Confidence Calculation
        confidence_info = calculate_confidence(
            optical_metrics, building_result, water_result, agri_result,
            mode=mode, fusion_result=fusion_metrics
        )
        execution_steps.append(f"Derived multi-factor confidence: {confidence_info['score']}/100 ({confidence_info['level']})")
        
        # 8. Visual Evidence Generation
        evidence_info = generate_visual_evidence(
            rgb_primary,
            building_result=building_result,
            water_result=water_result,
            agri_result=agri_result,
            change_result=change_result
        )
        execution_steps.append("Generated high-resolution visual evidence overlay with bounding boxes and segmentations")
        
        # 9. Natural-Language VQA Synthesis
        intermediate_results = {
            "buildings": building_result,
            "water_bodies": water_result,
            "agriculture": agri_result,
            "land_cover": land_cover_result,
            "change_detection": change_result,
            "fusion": fusion_metrics
        }
        vqa_spec = self.router.get_specialist("vqa")
        ai_answer = vqa_spec(query, intermediate_results, mode)
        specialists_used.append("Vision-Language Semantic Assistant")
        execution_steps.append("Synthesized natural-language interpretation from extracted remote sensing evidence")
        
        # Clean non-serializable masks from response objects
        bldg_clean = {
            "count": building_result.get('count', 0),
            "coverage_percentage": building_result.get('coverage_percentage', 0.0),
            "objects": building_result.get('objects', []),
            "spatial_distribution": bldg_directions,
            "model_used": building_result.get('model_used', 'N/A')
        }
        water_clean = {
            "count": water_result.get('count', 0),
            "coverage_percentage": water_result.get('coverage_percentage', 0.0),
            "objects": water_result.get('objects', []),
            "spatial_distribution": water_directions,
            "model_used": water_result.get('model_used', 'N/A')
        }
        agri_clean = {
            "coverage_percentage": agri_result.get('coverage_percentage', 0.0),
            "dominant_regions": agri_result.get('dominant_regions', []),
            "fields_count": agri_result.get('fields_count', 0),
            "model_used": agri_result.get('model_used', 'N/A')
        }
        change_clean = {
            "change_percentage": change_result.get('change_percentage', 0.0),
            "breakdown": change_result.get('breakdown', {}),
            "change_regions": change_result.get('change_regions', []),
            "directions_summary": change_result.get('directions_summary', {}),
            "model_used": change_result.get('model_used', 'N/A')
        } if mode == 'multitemporal' else {}
        
        land_cover_clean = {
            "agriculture": land_cover_result.get('agriculture', 0.0),
            "water": land_cover_result.get('water', 0.0),
            "built_up": land_cover_result.get('built_up', 0.0),
            "bare_land": land_cover_result.get('bare_land', 0.0),
            "other": land_cover_result.get('other', 0.0),
            "taxonomy": land_cover_result.get('taxonomy', 'BigEarthNet-19')
        }
        
        final_response = {
            "success": True,
            "analysis_id": analysis_id,
            "mode": mode,
            "query": query,
            "image_metadata": img_meta,
            "location_metadata": location_meta,
            "data_quality": {
                "source": "Uploaded Satellite Scene" if not location_meta else location_meta.get('provider', 'Satellite Service'),
                "resolution": img_meta.get('dimensions'),
                "model_suite": "SatQuery Modular Specialist Ensemble",
                "scale_info": "Image-relative percentage estimation (No sensor GCPs)" if not location_meta else location_meta.get('resolution', 'Standard Ground Sample Distance')
            },
            "result": {
                "answer": ai_answer,
                "confidence": confidence_info,
                "land_cover": land_cover_clean,
                "buildings": bldg_clean,
                "water_bodies": water_clean,
                "agriculture": agri_clean,
                "change_detection": change_clean,
                "fusion": fusion_metrics if mode == 'optical_sar' else {},
                "evidence": {
                    "filename": evidence_info['filename'],
                    "file_path": evidence_info['file_path'],
                    "data_uri": evidence_info['data_uri']
                }
            },
            "agent": {
                "selected_tasks": tasks,
                "specialists_used": list(dict.fromkeys(specialists_used)),
                "execution_steps": execution_steps
            }
        }
        
        # Save analysis to database
        save_analysis(user_email, mode, query, final_response)
        
        return final_response
