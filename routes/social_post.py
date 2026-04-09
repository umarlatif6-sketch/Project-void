"""
PROJECT VOID — Social Post Engine
===================================
Routes:
  GET  /social              — Dashboard: draft queue + generate
  POST /social/generate     — AI generates platform-specific posts
  POST /social/linkedin     — Post to LinkedIn (requires credentials)
  GET  /social/drafts       — JSON list of saved drafts
  POST /social/save         — Save a draft
  POST /social/delete/<id>  — Delete a draft
"""

import os
import json
import uuid
import logging
from datetime import datetime
from flask import Blueprint, render_template_string, request, jsonify, session

social_post_bp = Blueprint("social_post", __name__)
logger = logging.getLogger(__name__)

DRAFTS_PATH = "void_engine/social_drafts.json"

VOID_CONTEXT = """
PROJECT VOID — Founded by Umar L. — Manchester, England.

Key facts for posts:
- The Formation Principle: named 8 April 2026. Any responsive material at the moment of formation inherits the geometry of the frequency present. The frequency is prior. The material is the memory. Demonstrated by the Chladni experiment (sand + frequency + plate). Question unanswered for 238 years.
- Physical Key Cryptography: new discipline. Cryptographic keys formed by frequency acting on matter — not computed. Every key is unique, permanent, unrepeatable by algorithm.
- Digital Qalqala: tajweed acoustic rule (Haroof-e-Qalqala) applied to English TTS audio as DSP technique. Zero prior art. Built 9 April 2026.
- The Double Channel: simultaneous semantic + somatic information delivery collapses learning into instantaneous resonance. The mechanism of oral tradition.
- Platform live: https://void-stego-engine.replit.app
- Document 002 public: https://void-stego-engine.replit.app/frequency-manual
- Manchester Tech Week: April 27 - May 1 2026.
- ICC Event: April 13 2026.
- VTX / PEACE cryptocurrency, Blueprint NFTs, Adriana AI, Beehive mesh network, QiSync biostance, MycoVOID bioremediation — all part of the platform.
- The platform is unindexed. Prior art on all five core disclosures: zero results.
"""

POST_SYSTEM = f"""You are a social media post writer for PROJECT VOID.

Context about PROJECT VOID:
{VOID_CONTEXT}

Rules:
- Never use hashtags unless specifically requested
- Write in first person (the founder's voice — Umar L.)
- Tone: precise, confident, grounded. Not hype. Not sales. Statement of fact.
- LinkedIn: 150-300 words. Structured. Professional but not corporate.
- Twitter/X: under 240 characters. One sentence if possible. No hashtags. Direct.
- The founder does not shout. He states. Let the content do the work.
"""


def _load_drafts():
    if not os.path.exists(DRAFTS_PATH):
        return []
    try:
        with open(DRAFTS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _save_drafts(drafts):
    os.makedirs(os.path.dirname(DRAFTS_PATH), exist_ok=True)
    with open(DRAFTS_PATH, "w") as f:
        json.dump(drafts, f, indent=2)


def _linkedin_post(text: str) -> dict:
    client_id = os.environ.get("LINKEDIN_CLIENT_ID")
    access_token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    person_urn = os.environ.get("LINKEDIN_PERSON_URN")

    if not all([client_id, access_token, person_urn]):
        return {"ok": False, "error": "LinkedIn credentials not configured. Set LINKEDIN_CLIENT_ID, LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN in environment secrets."}

    import urllib.request
    payload = json.dumps({
        "author": f"urn:li:person:{person_urn}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.linkedin.com/v2/ugcPosts",
        data=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return {"ok": True, "status": resp.status}
    except Exception as e:
        return {"ok": False, "error": str(e)}


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VOID — Social Post Engine</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Courier New', monospace; background: #080808; color: #d0d0c8; min-height: 100vh; }
  .header {
    padding: 24px 32px;
    border-bottom: 1px solid #1a1a1a;
    display: flex; justify-content: space-between; align-items: center;
  }
  .header h1 { font-size: 13px; letter-spacing: 0.2em; color: #666; font-weight: normal; }
  .linkedin-status {
    font-size: 11px;
    padding: 4px 12px;
    border: 1px solid {{ '#2a5' if linkedin_ready else '#444' }};
    color: {{ '#4c9' if linkedin_ready else '#666' }};
    letter-spacing: 0.1em;
  }
  .main { display: grid; grid-template-columns: 1fr 1fr; gap: 0; min-height: calc(100vh - 61px); }
  .panel { padding: 32px; border-right: 1px solid #1a1a1a; }
  .panel h2 { font-size: 11px; letter-spacing: 0.2em; color: #555; font-weight: normal; margin-bottom: 24px; text-transform: uppercase; }
  .field-group { margin-bottom: 20px; }
  label { display: block; font-size: 11px; color: #555; letter-spacing: 0.1em; margin-bottom: 8px; }
  textarea, select, input[type=text] {
    width: 100%;
    background: #0f0f0f;
    border: 1px solid #222;
    color: #d0d0c8;
    padding: 12px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    resize: vertical;
    outline: none;
    transition: border-color 0.2s;
  }
  textarea:focus, select:focus, input:focus { border-color: #444; }
  select { cursor: pointer; }
  .btn {
    padding: 10px 20px;
    font-family: 'Courier New', monospace;
    font-size: 11px;
    letter-spacing: 0.15em;
    border: 1px solid #333;
    background: transparent;
    color: #d0d0c8;
    cursor: pointer;
    transition: all 0.2s;
    text-transform: uppercase;
  }
  .btn:hover { background: #1a1a1a; border-color: #555; }
  .btn-primary { background: #d0d0c8; color: #080808; border-color: #d0d0c8; }
  .btn-primary:hover { background: #bbb; }
  .btn-linkedin { border-color: #0a66c2; color: #4d9de0; }
  .btn-linkedin:hover { background: #0a1a2a; }
  .btn-danger { border-color: #5a2020; color: #c44; }
  .btn-danger:hover { background: #1a0808; }
  .btn-sm { padding: 6px 12px; font-size: 10px; }
  .generated-box {
    background: #0a0a0a;
    border: 1px solid #1e1e1e;
    padding: 20px;
    margin-top: 20px;
    min-height: 120px;
    font-size: 13px;
    line-height: 1.7;
    white-space: pre-wrap;
    display: none;
  }
  .char-count { font-size: 10px; color: #444; margin-top: 6px; text-align: right; }
  .actions { display: flex; gap: 10px; margin-top: 16px; flex-wrap: wrap; }
  .draft-item {
    border: 1px solid #1a1a1a;
    padding: 16px;
    margin-bottom: 12px;
    background: #0a0a0a;
  }
  .draft-meta { font-size: 10px; color: #444; margin-bottom: 10px; letter-spacing: 0.05em; }
  .draft-platform {
    display: inline-block;
    font-size: 10px;
    padding: 2px 8px;
    border: 1px solid #333;
    color: #777;
    margin-right: 8px;
    letter-spacing: 0.1em;
  }
  .draft-text { font-size: 12px; color: #aaa; line-height: 1.6; margin-bottom: 12px; white-space: pre-wrap; }
  .draft-actions { display: flex; gap: 8px; }
  .loading { color: #555; font-size: 12px; letter-spacing: 0.1em; }
  .msg { font-size: 12px; padding: 10px; border: 1px solid #333; margin-top: 12px; display: none; }
  .msg.ok { border-color: #2a5; color: #4c9; }
  .msg.err { border-color: #5a2020; color: #c44; }
  .empty { color: #333; font-size: 12px; padding: 32px 0; text-align: center; letter-spacing: 0.1em; }
</style>
</head>
<body>

<div class="header">
  <h1>◈ VOID — SOCIAL POST ENGINE</h1>
  <span class="linkedin-status">{{ 'LINKEDIN CONNECTED' if linkedin_ready else 'LINKEDIN NOT CONNECTED' }}</span>
</div>

<div class="main">

  <!-- LEFT: GENERATE -->
  <div class="panel">
    <h2>Generate Post</h2>

    <div class="field-group">
      <label>TOPIC / INSTRUCTION</label>
      <textarea id="topic" rows="4" placeholder="e.g. Announce the Formation Principle. Keep it factual. Link to the frequency manual."></textarea>
    </div>

    <div class="field-group">
      <label>PLATFORM</label>
      <select id="platform">
        <option value="linkedin">LinkedIn (150–300 words)</option>
        <option value="twitter">Twitter / X (under 240 chars)</option>
        <option value="both">Both</option>
      </select>
    </div>

    <button class="btn btn-primary" onclick="generate()">GENERATE</button>

    <div id="output-linkedin" class="generated-box"></div>
    <div id="count-linkedin" class="char-count" style="display:none"></div>
    <div id="actions-linkedin" class="actions" style="display:none">
      <button class="btn btn-sm" onclick="copyText('linkedin')">COPY</button>
      <button class="btn btn-sm btn-linkedin" onclick="postLinkedIn()">POST TO LINKEDIN</button>
      <button class="btn btn-sm" onclick="saveDraft('linkedin')">SAVE DRAFT</button>
    </div>

    <div id="output-twitter" class="generated-box" style="margin-top:16px"></div>
    <div id="count-twitter" class="char-count" style="display:none"></div>
    <div id="actions-twitter" class="actions" style="display:none">
      <button class="btn btn-sm" onclick="copyText('twitter')">COPY</button>
      <button class="btn btn-sm" onclick="saveDraft('twitter')">SAVE DRAFT</button>
    </div>

    <div id="msg-generate" class="msg"></div>

    {% if not linkedin_ready %}
    <div style="margin-top:32px; padding:16px; border:1px solid #1a1a1a; font-size:11px; color:#555; line-height:1.8;">
      TO CONNECT LINKEDIN:<br><br>
      1. Go to linkedin.com/developers → Create App<br>
      2. Add product: Sign In with LinkedIn<br>
      3. Set redirect URI: https://void-stego-engine.replit.app/social/linkedin/callback<br>
      4. Copy Client ID → set LINKEDIN_CLIENT_ID in secrets<br>
      5. Get access token → set LINKEDIN_ACCESS_TOKEN in secrets<br>
      6. Set your person URN → set LINKEDIN_PERSON_URN in secrets
    </div>
    {% endif %}
  </div>

  <!-- RIGHT: DRAFTS -->
  <div class="panel">
    <h2>Draft Queue</h2>
    <div id="drafts-container">
      {% if drafts %}
        {% for d in drafts %}
        <div class="draft-item" id="draft-{{ d.id }}">
          <div class="draft-meta">
            <span class="draft-platform">{{ d.platform.upper() }}</span>
            {{ d.created }}
          </div>
          <div class="draft-text">{{ d.text }}</div>
          <div class="draft-actions">
            <button class="btn btn-sm" onclick="copyDraft('{{ d.id }}')">COPY</button>
            {% if d.platform == 'linkedin' %}
            <button class="btn btn-sm btn-linkedin" onclick="postDraft('{{ d.id }}')">POST</button>
            {% endif %}
            <button class="btn btn-sm btn-danger" onclick="deleteDraft('{{ d.id }}')">DELETE</button>
          </div>
        </div>
        {% endfor %}
      {% else %}
        <div class="empty">NO DRAFTS YET</div>
      {% endif %}
    </div>
  </div>

</div>

<script>
const texts = { linkedin: '', twitter: '' };

async function generate() {
  const topic = document.getElementById('topic').value.trim();
  const platform = document.getElementById('platform').value;
  if (!topic) return;

  ['linkedin','twitter'].forEach(p => {
    document.getElementById('output-'+p).style.display = 'none';
    document.getElementById('count-'+p).style.display = 'none';
    document.getElementById('actions-'+p).style.display = 'none';
  });

  const out = document.getElementById('output-linkedin');
  out.style.display = 'block';
  out.textContent = 'GENERATING...';

  const res = await fetch('/social/generate', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ topic, platform })
  });
  const data = await res.json();

  if (data.linkedin) {
    texts.linkedin = data.linkedin;
    const el = document.getElementById('output-linkedin');
    el.style.display = 'block';
    el.textContent = data.linkedin;
    document.getElementById('count-linkedin').style.display = 'block';
    document.getElementById('count-linkedin').textContent = data.linkedin.length + ' characters';
    document.getElementById('actions-linkedin').style.display = 'flex';
  } else {
    document.getElementById('output-linkedin').style.display = 'none';
  }

  if (data.twitter) {
    texts.twitter = data.twitter;
    const el = document.getElementById('output-twitter');
    el.style.display = 'block';
    el.textContent = data.twitter;
    document.getElementById('count-twitter').style.display = 'block';
    document.getElementById('count-twitter').textContent = data.twitter.length + ' / 240 characters';
    document.getElementById('actions-twitter').style.display = 'flex';
  }
}

function copyText(platform) {
  navigator.clipboard.writeText(texts[platform]);
}

function copyDraft(id) {
  const el = document.querySelector('#draft-'+id+' .draft-text');
  if (el) navigator.clipboard.writeText(el.textContent.trim());
}

async function postLinkedIn() {
  showMsg('generate', 'POSTING TO LINKEDIN...', '');
  const res = await fetch('/social/linkedin', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ text: texts.linkedin })
  });
  const data = await res.json();
  if (data.ok) {
    showMsg('generate', 'POSTED TO LINKEDIN', 'ok');
  } else {
    showMsg('generate', 'ERROR: ' + data.error, 'err');
  }
}

async function postDraft(id) {
  const el = document.querySelector('#draft-'+id+' .draft-text');
  if (!el) return;
  const text = el.textContent.trim();
  const res = await fetch('/social/linkedin', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ text })
  });
  const data = await res.json();
  alert(data.ok ? 'Posted to LinkedIn.' : 'Error: ' + data.error);
}

async function saveDraft(platform) {
  const res = await fetch('/social/save', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ text: texts[platform], platform })
  });
  const data = await res.json();
  if (data.ok) {
    showMsg('generate', 'DRAFT SAVED', 'ok');
    setTimeout(() => location.reload(), 800);
  }
}

async function deleteDraft(id) {
  await fetch('/social/delete/'+id, { method: 'POST' });
  const el = document.getElementById('draft-'+id);
  if (el) el.remove();
}

function showMsg(zone, text, type) {
  const el = document.getElementById('msg-'+zone);
  el.textContent = text;
  el.className = 'msg ' + type;
  el.style.display = 'block';
  if (type) setTimeout(() => { el.style.display = 'none'; }, 4000);
}
</script>
</body>
</html>"""


@social_post_bp.route("/social")
def social_dashboard():
    drafts = _load_drafts()
    linkedin_ready = bool(
        os.environ.get("LINKEDIN_ACCESS_TOKEN") and
        os.environ.get("LINKEDIN_PERSON_URN")
    )
    return render_template_string(TEMPLATE, drafts=drafts, linkedin_ready=linkedin_ready, request=request)


@social_post_bp.route("/social/generate", methods=["POST"])
def social_generate():
    data = request.get_json() or {}
    topic = data.get("topic", "").strip()
    platform = data.get("platform", "linkedin")

    if not topic:
        return jsonify({"error": "No topic provided"}), 400

    from openai import OpenAI
    client = OpenAI()

    result = {}

    if platform in ("linkedin", "both"):
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": POST_SYSTEM + "\nWrite a LinkedIn post."},
                {"role": "user", "content": topic}
            ],
            max_tokens=500,
            temperature=0.7,
        )
        result["linkedin"] = resp.choices[0].message.content.strip()

    if platform in ("twitter", "both"):
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": POST_SYSTEM + "\nWrite a Twitter/X post. Under 240 characters. No hashtags. One or two sentences maximum."},
                {"role": "user", "content": topic}
            ],
            max_tokens=80,
            temperature=0.7,
        )
        result["twitter"] = resp.choices[0].message.content.strip()[:240]

    return jsonify(result)


@social_post_bp.route("/social/linkedin", methods=["POST"])
def social_linkedin():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"ok": False, "error": "No text provided"}), 400
    result = _linkedin_post(text)
    return jsonify(result)


@social_post_bp.route("/social/drafts")
def social_drafts():
    return jsonify(_load_drafts())


@social_post_bp.route("/social/save", methods=["POST"])
def social_save():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    platform = data.get("platform", "linkedin")
    if not text:
        return jsonify({"ok": False}), 400
    drafts = _load_drafts()
    drafts.insert(0, {
        "id": str(uuid.uuid4())[:8],
        "platform": platform,
        "text": text,
        "created": datetime.now().strftime("%d %b %Y %H:%M")
    })
    _save_drafts(drafts)
    return jsonify({"ok": True})


@social_post_bp.route("/social/delete/<draft_id>", methods=["POST"])
def social_delete(draft_id):
    drafts = _load_drafts()
    drafts = [d for d in drafts if d.get("id") != draft_id]
    _save_drafts(drafts)
    return jsonify({"ok": True})
