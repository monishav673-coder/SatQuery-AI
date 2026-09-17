from flask import Blueprint, request, jsonify, current_app
import os
import uuid
import base64
from services.geospatial import validate_coordinates, reverse_geocode, fetch_satellite_tile_for_coords
from agent.controller import AgentController

location_bp = Blueprint('location', __name__)
agent_controller = AgentController()

@location_bp.route('/preview-location', methods=['POST', 'GET'])
def preview_location():
    """
    Fetch reverse geocoded area name and satellite tile preview for given latitude & longitude.
    """
    try:
        if request.method == 'GET':
            lat_raw = request.args.get('latitude') or request.args.get('lat')
            lon_raw = request.args.get('longitude') or request.args.get('lon')
        else:
            data = request.get_json() or {}
            lat_raw = data.get('latitude') or data.get('lat')
            lon_raw = data.get('longitude') or data.get('lon')
            
        if lat_raw is None or lon_raw is None:
            return jsonify({"success": False, "error": "Latitude and Longitude are required."}), 400
            
        is_valid, lat, lon, err_msg = validate_coordinates(lat_raw, lon_raw)
        if not is_valid:
            return jsonify({"success": False, "error": err_msg}), 400
            
        # Reverse geocoding for area name
        loc_info = reverse_geocode(lat, lon)
        
        # Retrieve satellite tile for coordinate
        upload_folder = current_app.config['UPLOAD_FOLDER']
        preview_filename = f"geotile_preview_{uuid.uuid4().hex[:8]}.jpg"
        preview_path = os.path.join(upload_folder, preview_filename)
        
        tile_fetched, downloaded_path, tile_meta = fetch_satellite_tile_for_coords(lat, lon, zoom=16, output_path=preview_path)
        
        data_uri = None
        if tile_fetched and downloaded_path and os.path.exists(downloaded_path):
            with open(downloaded_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                data_uri = f"data:image/jpeg;base64,{encoded_string}"
                
        return jsonify({
            "success": True,
            "coordinates": {
                "latitude": lat,
                "longitude": lon
            },
            "location": loc_info,
            "tile": {
                "fetched": tile_fetched,
                "provider": tile_meta.get('provider', 'Esri World Imagery'),
                "resolution": tile_meta.get('resolution', '~1.2 meters/pixel (Orthorectified)'),
                "tile_coords": tile_meta.get('tile_coords'),
                "tile_url": f"/uploads/{preview_filename}" if tile_fetched else None,
                "data_uri": data_uri
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to preview location: {str(e)}"
        }), 500

@location_bp.route('/analyze-location', methods=['POST'])
def analyze_location():
    try:
        data = request.get_json() or {}
        lat_raw = data.get('latitude')
        lon_raw = data.get('longitude')
        query = data.get('query', 'Identify buildings, water bodies and agricultural areas, and tell me where they are located.')
        user_email = data.get('user_email', 'scientist@isro.gov.in')
        
        # 1. Validate coordinates
        is_valid, lat, lon, err_msg = validate_coordinates(lat_raw, lon_raw)
        if not is_valid:
            return jsonify({"success": False, "error": err_msg}), 400
            
        # 2. Reverse geocode location
        loc_info = reverse_geocode(lat, lon)
        
        # 3. Retrieve satellite imagery
        upload_folder = current_app.config['UPLOAD_FOLDER']
        tile_filename = f"geotile_{uuid.uuid4().hex[:8]}.jpg"
        tile_path = os.path.join(upload_folder, tile_filename)
        
        tile_fetched, downloaded_path, tile_meta = fetch_satellite_tile_for_coords(lat, lon, zoom=16, output_path=tile_path)
        
        if not tile_fetched:
            return jsonify({
                "success": False,
                "error": tile_meta.get('error', 'Location analysis requires a configured satellite data provider.'),
                "location_details": loc_info,
                "coordinates": {"latitude": lat, "longitude": lon}
            }), 400
            
        # Convert original tile to base64 data URI so frontend has access to both original scene and overlay
        raw_data_uri = None
        if os.path.exists(downloaded_path):
            with open(downloaded_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                raw_data_uri = f"data:image/jpeg;base64,{encoded_string}"
                
        # 4. Run Analysis Pipeline on the retrieved satellite tile
        loc_meta = {
            "latitude": lat,
            "longitude": lon,
            "display_name": loc_info.get('display_name'),
            "country": loc_info.get('country'),
            "state": loc_info.get('state'),
            "city": loc_info.get('city'),
            "postcode": loc_info.get('postcode'),
            "provider": tile_meta.get('provider', 'Esri World Imagery'),
            "resolution": tile_meta.get('resolution', '~1.2m/pixel (Orthorectified)'),
            "tile_coords": tile_meta.get('tile_coords'),
            "raw_image_url": f"/uploads/{tile_filename}",
            "raw_data_uri": raw_data_uri
        }
        
        file_paths = {'primary': downloaded_path}
        response_data = agent_controller.run_analysis(user_email, "location", query, file_paths, location_meta=loc_meta)
        
        # Attach raw image data URI to response evidence for side-by-side or before/after comparison
        if response_data.get('result', {}).get('evidence'):
            response_data['result']['evidence']['raw_data_uri'] = raw_data_uri
            response_data['result']['evidence']['raw_image_url'] = f"/uploads/{tile_filename}"
            
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Location analysis error: {str(e)}"
        }), 500
