from flask import Blueprint, jsonify, send_file, current_app
import os
from database import get_analysis_by_id
from services.report import generate_pdf_report

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/<analysis_id>', methods=['GET'])
def get_report_json(analysis_id):
    analysis_data = get_analysis_by_id(analysis_id)
    if not analysis_data:
        return jsonify({"success": False, "error": f"Report with ID '{analysis_id}' not found."}), 404
    return jsonify(analysis_data), 200

@reports_bp.route('/<analysis_id>/pdf', methods=['GET'])
def download_pdf_report(analysis_id):
    analysis_data = get_analysis_by_id(analysis_id)
    if not analysis_data:
        return jsonify({"success": False, "error": f"Analysis record '{analysis_id}' not found."}), 404
        
    reports_dir = current_app.config['REPORTS_FOLDER']
    os.makedirs(reports_dir, exist_ok=True)
    pdf_path = os.path.join(reports_dir, f"SatQuery_Report_{analysis_id}.pdf")
    
    if not os.path.exists(pdf_path):
        generate_pdf_report(analysis_data, pdf_path)
        
    return send_file(
        pdf_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"SatQuery_Report_{analysis_id}.pdf"
    )
