from flask import Blueprint, request, jsonify
from database import create_user, verify_user, update_user_language

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email', '')
    password = data.get('password', '')
    preferred_language = data.get('preferred_language', 'en')
    
    success, result = create_user(email, password, preferred_language)
    if success:
        return jsonify({
            "success": True,
            "message": "User registered successfully.",
            "user": result
        }), 201
    else:
        return jsonify({
            "success": False,
            "error": result
        }), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '')
    password = data.get('password', '')
    
    success, result = verify_user(email, password)
    if success:
        return jsonify({
            "success": True,
            "message": "Login successful.",
            "user": result
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": "Invalid email or password."
        }), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    }), 200

@auth_bp.route('/update-language', methods=['POST'])
def change_language():
    data = request.get_json() or {}
    email = data.get('email', '')
    language = data.get('language', 'en')
    if email:
        update_user_language(email, language)
    return jsonify({"success": True, "language": language}), 200
