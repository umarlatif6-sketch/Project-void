"""
THE TREE OF KNOWLEDGE — Route
PROJECT VOID | Umar Latif
"""

from flask import Blueprint, render_template, request, jsonify
from void_engine.knowledge_tree import three_brain_read, FORMATION_RATIO
from void_engine.names_286 import LAMBDA, BASE_FREQ

knowledge_tree_bp = Blueprint('knowledge_tree', __name__)


@knowledge_tree_bp.route('/knowledge-tree')
def knowledge_tree_page():
    return render_template('knowledge_tree.html',
                           lambda_val=LAMBDA,
                           base_freq=BASE_FREQ,
                           formation_ratio=round(FORMATION_RATIO, 4))


@knowledge_tree_bp.route('/api/knowledge-tree/read', methods=['POST'])
def api_read():
    data = request.get_json(silent=True) or {}
    text = data.get('text', '').strip()
    if not text:
        return jsonify({"error": "Provide text to read"}), 400
    if len(text) > 50000:
        text = text[:50000]
    result = three_brain_read(text)
    return jsonify(result)
