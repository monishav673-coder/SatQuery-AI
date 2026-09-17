from flask import Blueprint, request, jsonify, current_app
import os
import uuid
from werkzeug.utils import secure_filename
from agent.controller import AgentController

analysis_bp = Blueprint('analysis', __name__)
agent_controller = AgentController()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'tif', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@analysis_bp.route('/analyze', methods=['POST'])
def analyze():
    try:
        mode = request.form.get('mode', 'single').lower()
        query = request.form.get('query', 'Identify buildings, water bodies and agricultural areas.')
        user_email = request.form.get('user_email', 'guest@satquery.ai')
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        
        file_paths = {}
        
        if mode == 'single':
            # Accept 'image' or 'primary'
            file_obj = request.files.get('image') or request.files.get('primary')
            if not file_obj or file_obj.filename == '':
                return jsonify({"success": False, "error": "Single image mode requires one uploaded satellite image."}), 400
            
            if not allowed_file(file_obj.filename):
                return jsonify({"success": False, "error": "Unsupported file format. Please upload PNG, JPG, JPEG, WEBP or TIFF."}), 400
                
            fname = f"{uuid.uuid4().hex[:8]}_{secure_filename(file_obj.filename)}"
            fpath = os.path.join(upload_folder, fname)
            file_obj.save(fpath)
            file_paths['primary'] = fpath
            
        elif mode == 'optical_sar':
            opt_file = request.files.get('optical')
            sar_file = request.files.get('sar')
            
            if not opt_file or not sar_file or opt_file.filename == '' or sar_file.filename == '':
                return jsonify({"success": False, "error": "Optical + SAR mode requires both an Optical satellite image and a SAR satellite image."}), 400
                
            if not allowed_file(opt_file.filename) or not allowed_file(sar_file.filename):
                return jsonify({"success": False, "error": "Unsupported file format in Optical or SAR upload."}), 400
                
            opt_name = f"opt_{uuid.uuid4().hex[:8]}_{secure_filename(opt_file.filename)}"
            sar_name = f"sar_{uuid.uuid4().hex[:8]}_{secure_filename(sar_file.filename)}"
            opt_path = os.path.join(upload_folder, opt_name)
            sar_path = os.path.join(upload_folder, sar_name)
            
            opt_file.save(opt_path)
            sar_file.save(sar_path)
            file_paths['primary'] = opt_path
            file_paths['optical'] = opt_path
            file_paths['sar'] = sar_path
            
        elif mode == 'multitemporal':
            before_file = request.files.get('before')
            after_file = request.files.get('after')
            
            if not before_file or not after_file or before_file.filename == '' or after_file.filename == '':
                return jsonify({"success": False, "error": "Multitemporal mode requires both a Before image and an After image."}), 400
                
            if not allowed_file(before_file.filename) or not allowed_file(after_file.filename):
                return jsonify({"success": False, "error": "Unsupported file format in Before or After image."}), 400
                
            bef_name = f"bef_{uuid.uuid4().hex[:8]}_{secure_filename(before_file.filename)}"
            aft_name = f"aft_{uuid.uuid4().hex[:8]}_{secure_filename(after_file.filename)}"
            bef_path = os.path.join(upload_folder, bef_name)
            aft_path = os.path.join(upload_folder, aft_name)
            
            before_file.save(bef_path)
            after_file.save(aft_path)
            file_paths['primary'] = bef_path
            file_paths['before'] = bef_path
            file_paths['after'] = aft_path
            
        else:
            return jsonify({"success": False, "error": f"Unknown analysis mode: {mode}"}), 400
            
        # Execute Agent Pipeline
        response_data = agent_controller.run_analysis(user_email, mode, query, file_paths)
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Analysis execution error: {str(e)}"
        }), 500
