"""
THE TREE OF KNOWLEDGE — Route
PROJECT VOID | Umar Latif
"""

from flask import Blueprint, render_template, request, jsonify
from void_engine.knowledge_tree import three_brain_read, FORMATION_RATIO
from void_engine.knowledge_tree_store import (
    get_knowledge_tree_node,
    get_import_run,
    get_knowledge_tree_stats,
    init_knowledge_tree_tables,
    search_story_signals,
    search_knowledge_tree_nodes,
)
from void_engine.names_286 import LAMBDA, BASE_FREQ

knowledge_tree_bp = Blueprint('knowledge_tree', __name__)


def _safe_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@knowledge_tree_bp.route('/knowledge-tree')
def knowledge_tree_page():
    init_knowledge_tree_tables()
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


@knowledge_tree_bp.route('/api/knowledge-tree/nodes', methods=['GET'])
def api_nodes():
    init_knowledge_tree_tables()
    query = request.args.get('q', '').strip()
    limit = min(_safe_int(request.args.get('limit'), 25), 100)
    offset = max(_safe_int(request.args.get('offset'), 0), 0)
    return jsonify({
        "query": query,
        "limit": limit,
        "offset": offset,
        "items": search_knowledge_tree_nodes(query=query, limit=limit, offset=offset),
    })


@knowledge_tree_bp.route('/api/knowledge-tree/search', methods=['GET'])
def api_search():
    return api_nodes()


@knowledge_tree_bp.route('/api/knowledge-tree/stats', methods=['GET'])
def api_stats():
    init_knowledge_tree_tables()
    source_path = request.args.get('source_path', '').strip()
    format_name = request.args.get('format', '').strip() or None
    payload = get_knowledge_tree_stats()
    if source_path and format_name:
        payload["import_run"] = get_import_run(source_path, format_name)
    return jsonify(payload)


@knowledge_tree_bp.route('/api/knowledge-tree/node', methods=['GET'])
def api_node():
    init_knowledge_tree_tables()
    source = request.args.get('source', '').strip()
    title = request.args.get('title', '').strip()
    if not source or not title:
        return jsonify({"error": "Provide source and title"}), 400
    payload = get_knowledge_tree_node(source, title)
    if not payload:
        return jsonify({"error": "Node not found"}), 404
    return jsonify(payload)


@knowledge_tree_bp.route('/api/knowledge-tree/signals', methods=['GET'])
def api_signals():
    init_knowledge_tree_tables()
    query = request.args.get('q', '').strip()
    signal_type = request.args.get('signal_type', 'all').strip().lower()
    raw_name_index = request.args.get('name_index', '').strip()
    name_index = None
    if raw_name_index:
        try:
            name_index = int(raw_name_index)
        except ValueError:
            return jsonify({"error": "name_index must be an integer"}), 400

    if signal_type not in {'all', 'analogy', 'perspective'}:
        return jsonify({"error": "signal_type must be all, analogy, or perspective"}), 400

    limit = min(_safe_int(request.args.get('limit'), 30), 100)
    offset = max(_safe_int(request.args.get('offset'), 0), 0)

    payload = search_story_signals(
        query=query,
        signal_type=signal_type,
        name_index=name_index,
        limit=limit,
        offset=offset,
    )
    return jsonify({
        "query": query,
        "signal_type": signal_type,
        "name_index": name_index,
        "limit": limit,
        "offset": offset,
        "total": payload.get("total", 0),
        "clusters": payload.get("clusters", []),
        "items": payload.get("items", []),
    })
