import io
from flask import Blueprint, render_template, send_file, abort

brand_bp = Blueprint("brand", __name__)


@brand_bp.route("/brand")
def brand_kit():
    return render_template("brand.html")


@brand_bp.route("/brand/content")
def brand_content():
    return render_template("brand_content.html")


@brand_bp.route("/brand/legal")
def brand_legal():
    return render_template("brand_legal.html")


@brand_bp.route("/brand/legal/download/<doc_type>/<fmt>")
def brand_legal_download(doc_type, fmt):
    if doc_type not in ("nda", "rca"):
        abort(404)
    if fmt not in ("pdf", "docx"):
        abort(404)

    from void_engine.brand_docs import generate_pdf, generate_docx

    filenames = {
        "nda": "PROJECT_VOID_Mutual_NDA",
        "rca": "PROJECT_VOID_Research_Collaboration_Agreement",
    }
    base = filenames[doc_type]

    if fmt == "pdf":
        data = generate_pdf(doc_type)
        return send_file(
            io.BytesIO(data),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{base}.pdf",
        )
    else:
        data = generate_docx(doc_type)
        return send_file(
            io.BytesIO(data),
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            as_attachment=True,
            download_name=f"{base}.docx",
        )
