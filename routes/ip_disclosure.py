"""
IP Disclosure — Intellectual Property Document
Route: GET /ip-disclosure  — Rendered IP disclosure document for legal counsel
Route: GET /void-disclosures/download  — Raw markdown file download
"""

import os
from flask import Blueprint, render_template_string, send_file, abort

ip_disclosure_bp = Blueprint("ip_disclosure", __name__)

DISCLOSURE_PATH = "IP_DISCLOSURE.md"


def _load_disclosure() -> str:
    if not os.path.exists(DISCLOSURE_PATH):
        abort(404)
    with open(DISCLOSURE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _md_to_html(md: str) -> str:
    try:
        import markdown
        return markdown.markdown(md, extensions=["tables", "toc"])
    except ImportError:
        lines = []
        for line in md.split("\n"):
            if line.startswith("## "):
                lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("# "):
                lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("**") and line.endswith("**"):
                lines.append(f"<p><strong>{line[2:-2]}</strong></p>")
            elif line.strip() == "---":
                lines.append("<hr>")
            elif line.strip() == "":
                lines.append("<br>")
            else:
                line = line.replace("**", "<strong>", 1)
                while "**" in line:
                    line = line.replace("**", "</strong>", 1)
                lines.append(f"<p>{line}</p>")
        return "\n".join(lines)


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IP Disclosure — PROJECT VOID</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Georgia', serif;
    background: #0a0a0a;
    color: #e8e8e0;
    line-height: 1.8;
  }
  .print-bar {
    position: fixed;
    top: 0; left: 0; right: 0;
    background: #111;
    border-bottom: 1px solid #333;
    padding: 12px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 1000;
  }
  .print-bar span {
    font-size: 13px;
    color: #888;
    letter-spacing: 0.05em;
  }
  .print-bar a {
    text-decoration: none;
    font-size: 13px;
    letter-spacing: 0.08em;
    padding: 8px 20px;
    border: 1px solid #444;
    color: #e8e8e0;
    cursor: pointer;
    background: transparent;
    margin-left: 12px;
    transition: all 0.2s;
  }
  .print-bar a:hover { background: #222; border-color: #888; }
  .print-bar .primary {
    background: #e8e8e0;
    color: #0a0a0a;
    border-color: #e8e8e0;
  }
  .print-bar .primary:hover { background: #ccc; }
  .container {
    max-width: 860px;
    margin: 0 auto;
    padding: 100px 48px 80px;
  }
  h1 {
    font-size: 22px;
    font-weight: normal;
    letter-spacing: 0.05em;
    border-bottom: 1px solid #333;
    padding-bottom: 24px;
    margin-bottom: 32px;
    color: #fff;
  }
  h2 {
    font-size: 15px;
    font-weight: normal;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #aaa;
    margin: 48px 0 16px;
    padding-top: 24px;
    border-top: 1px solid #222;
  }
  h3 {
    font-size: 14px;
    font-weight: bold;
    color: #ccc;
    margin: 24px 0 12px;
    letter-spacing: 0.05em;
  }
  p {
    margin-bottom: 14px;
    color: #d0d0c8;
    font-size: 15px;
  }
  strong { color: #fff; }
  hr {
    border: none;
    border-top: 1px solid #222;
    margin: 32px 0;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    font-size: 13px;
  }
  th {
    background: #1a1a1a;
    color: #aaa;
    padding: 10px 14px;
    text-align: left;
    font-weight: normal;
    letter-spacing: 0.05em;
    border: 1px solid #2a2a2a;
  }
  td {
    padding: 10px 14px;
    border: 1px solid #1e1e1e;
    color: #c8c8c0;
    vertical-align: top;
  }
  tr:nth-child(even) td { background: #0e0e0e; }
  code, pre {
    font-family: 'Courier New', monospace;
    font-size: 12px;
    background: #111;
    color: #88cc88;
    padding: 2px 6px;
    border-radius: 2px;
  }
  pre {
    display: block;
    padding: 16px 20px;
    margin: 16px 0;
    overflow-x: auto;
    border-left: 2px solid #333;
    line-height: 1.6;
  }
  blockquote {
    border-left: 3px solid #444;
    padding: 12px 20px;
    margin: 20px 0;
    color: #aaa;
    font-style: italic;
  }
  li {
    margin-bottom: 8px;
    color: #c8c8c0;
    font-size: 15px;
    margin-left: 20px;
  }
  .stamp {
    text-align: center;
    padding: 48px 0 24px;
    color: #444;
    font-size: 13px;
    letter-spacing: 0.1em;
  }

  @media print {
    .print-bar { display: none; }
    body { background: #fff; color: #000; }
    .container { padding: 40px; }
    h1, h2, h3, strong { color: #000; }
    p, td, li { color: #333; }
    th { background: #f0f0f0; color: #000; }
    h2 { color: #666; border-top: 1px solid #ccc; }
    hr { border-top: 1px solid #ccc; }
    table { border: 1px solid #ccc; }
    th, td { border: 1px solid #ccc; }
    code, pre { background: #f5f5f5; color: #333; border-left: 2px solid #ccc; }
  }
</style>
</head>
<body>

<div class="print-bar">
  <span>PROJECT VOID — IP DISCLOSURE DOCUMENT — 9 APRIL 2026</span>
  <div>
    <a href="/void-disclosures/download">↓ DOWNLOAD .MD</a>
    <a class="primary" onclick="window.print()">⎙ PRINT / SAVE PDF</a>
  </div>
</div>

<div class="container">
  {{ content | safe }}
  <div class="stamp">◈ PROJECT VOID — MANCHESTER, ENGLAND — 9 APRIL 2026</div>
</div>

</body>
</html>"""


@ip_disclosure_bp.route("/void-disclosures")
def ip_disclosure():
    raw = _load_disclosure()
    content = _md_to_html(raw)
    return render_template_string(TEMPLATE, content=content)


@ip_disclosure_bp.route("/void-disclosures/download")
def ip_disclosure_download():
    if not os.path.exists(DISCLOSURE_PATH):
        abort(404)
    return send_file(
        DISCLOSURE_PATH,
        as_attachment=True,
        download_name="PROJECT_VOID_IP_DISCLOSURE_9APR2026.md",
        mimetype="text/markdown",
    )
