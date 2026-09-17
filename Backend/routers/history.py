from flask import Blueprint, request, jsonify
from database import get_user_history

history_bp = Blueprint('history', __name__)

@history_bp.route('/', methods=['GET'])
def get_history():
    user_email = request.args.get('email', 'guest@satquery.ai')
    limit = int(request.args.get('limit', 50))
    history_items = get_user_history(user_email, limit)
    return jsonify({
        "success": True,
        "count": len(history_items),
        "history": history_items
    }), 200
