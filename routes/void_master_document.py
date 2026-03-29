"""
PROJECT VOID — Master Reference Document
Route: GET /void-master-document

Renders the single-page master reference document covering all seven
crystallization layers in flowing prose. Serves as the canonical
internal, external, legal, and philosophical reference for PROJECT VOID.
"""

from flask import Blueprint, render_template

void_master_document_bp = Blueprint("void_master_document", __name__)


@void_master_document_bp.route("/void-master-document")
def void_master_document():
    return render_template("void_master_document.html")
