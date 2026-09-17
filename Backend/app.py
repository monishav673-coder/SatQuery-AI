import os
import sys
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db
from routers.auth import auth_bp
from routers.analysis import analysis_bp
from routers.location import location_bp
from routers.reports import reports_bp
from routers.history import history_bp

def create_app():
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), '..', 'Frontend'),
        static_url_path=''
    )
    
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Configure directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(base_dir, 'uploads')
    reports_folder = os.path.join(base_dir, 'reports')
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(reports_folder, exist_ok=True)
    
    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['REPORTS_FOLDER'] = reports_folder
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max upload
    
    # Initialize Database
    init_db()
    
    # Register API Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(analysis_bp, url_prefix='/api')
    app.register_blueprint(location_bp, url_prefix='/api')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(history_bp, url_prefix='/api/history')
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            "status": "online",
            "service": "SatQuery AI Remote Sensing Engine",
            "version": "2.0.0",
            "models": {
                "optical_analyzer": "Online",
                "sar_analyzer": "Online",
                "building_detector": "Online",
                "water_detector": "Online",
                "vegetation_analyzer": "Online",
                "bigearthnet_landcover": "Online",
                "change_detector": "Online",
                "optical_sar_fusion": "Online"
            }
        }), 200

    # Serve sample files
    @app.route('/samples/<path:filename>')
    def serve_sample(filename):
        sample_dir = os.path.join(os.path.dirname(__file__), '..', 'samples')
        return send_from_directory(sample_dir, filename)

    # Serve uploaded/evidence files
    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        
    # Serve Frontend SPA
    @app.route('/')
    def serve_index():
        return send_from_directory(app.static_folder, 'index.html')
        
    @app.route('/<path:path>')
    def serve_static(path):
        full_path = os.path.join(app.static_folder, path)
        if os.path.exists(full_path):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({"success": False, "error": "API endpoint not found."}), 404
        return send_from_directory(app.static_folder, 'index.html')

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"success": False, "error": "Internal server error."}), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    host = os.getenv('HOST', '127.0.0.1')
    print(f"============================================================")
    print(f"SATQUERY AI Remote Sensing Server starting on http://{host}:{port}")
    print(f"============================================================")
    app.run(host=host, port=port, debug=False)
