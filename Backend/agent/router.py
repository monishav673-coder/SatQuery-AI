from specialists.building_detection import detect_buildings
from specialists.water_detection import detect_water_bodies
from specialists.agriculture import analyze_agriculture
from specialists.land_cover import classify_land_cover
from specialists.change_detection import detect_multitemporal_changes
from specialists.optical_analysis import analyze_optical
from specialists.sar_analysis import analyze_sar
from specialists.optical_sar_fusion import fuse_optical_sar
from specialists.vqa import generate_vqa_response

class SpecialistRouter:
    """
    Routes planned tasks to domain-specific computer vision & remote sensing specialists.
    """
    def __init__(self):
        self.specialists = {
            "optical": analyze_optical,
            "sar": analyze_sar,
            "fusion": fuse_optical_sar,
            "building": detect_buildings,
            "water": detect_water_bodies,
            "agriculture": analyze_agriculture,
            "land_cover": classify_land_cover,
            "change_detection": detect_multitemporal_changes,
            "vqa": generate_vqa_response
        }

    def get_specialist(self, name):
        return self.specialists.get(name)
