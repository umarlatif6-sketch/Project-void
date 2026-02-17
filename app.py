import os
import uuid
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

from void_engine.compressor import compress_file, decompress_data
from void_engine.stega import encode, decode, encode_burst
from void_engine.calculator import analyze_carrier

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "void-engine-dev-key")

INPUT_DIR = "input_files"
OUTPUT_DIR = "output_audio"

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/files")
def list_files():
    def get_files(directory):
        if not os.path.isdir(directory):
            return []
        result = []
        for f in sorted(os.listdir(directory)):
            fp = os.path.join(directory, f)
            if os.path.isfile(fp):
                size = os.path.getsize(fp)
                result.append({"name": f, "size": size, "path": fp})
        return result

    return jsonify({
        "input": get_files(INPUT_DIR),
        "output": get_files(OUTPUT_DIR),
    })


@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "No filename"}), 400

    filename = secure_filename(f.filename)
    dest = request.form.get("dest", "input")
    directory = INPUT_DIR if dest == "input" else OUTPUT_DIR
    filepath = os.path.join(directory, filename)
    f.save(filepath)

    return jsonify({
        "success": True,
        "filename": filename,
        "size": os.path.getsize(filepath),
    })


@app.route("/api/encode", methods=["POST"])
def encode_file():
    data = request.json
    carrier = data.get("carrier")
    payload = data.get("payload")
    lsb_depth = int(data.get("lsb_depth", 1))

    if not carrier or not payload:
        return jsonify({"error": "Carrier and payload files are required"}), 400

    carrier_path = os.path.join(INPUT_DIR, carrier)
    payload_path = os.path.join(INPUT_DIR, payload)

    if not os.path.exists(carrier_path):
        return jsonify({"error": f"Carrier file not found: {carrier}"}), 404
    if not os.path.exists(payload_path):
        return jsonify({"error": f"Payload file not found: {payload}"}), 404

    try:
        compressed, name, ext, orig_size = compress_file(payload_path)

        base_name = os.path.splitext(carrier)[0]
        output_name = f"{base_name}_void.wav"
        output_path = os.path.join(OUTPUT_DIR, output_name)

        hash_key = encode(carrier_path, compressed, name, ext, output_path, lsb_depth)

        return jsonify({
            "success": True,
            "hash_key": hash_key,
            "output_file": output_name,
            "output_size": os.path.getsize(output_path),
            "original_size": orig_size,
            "compressed_size": len(compressed),
            "lsb_depth": lsb_depth,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/burst", methods=["POST"])
def burst_encode():
    data = request.json
    signal = data.get("signal", "")

    if not signal:
        return jsonify({"error": "Signal text is required"}), 400
    if len(signal) > 10:
        return jsonify({"error": "Signal text must be 10 characters or fewer"}), 400

    try:
        burst_id = uuid.uuid4().hex[:8]
        output_name = f"burst_{burst_id}.wav"
        output_path = os.path.join(OUTPUT_DIR, output_name)

        hash_key = encode_burst(signal, output_path)

        return jsonify({
            "success": True,
            "hash_key": hash_key,
            "output_file": output_name,
            "output_size": os.path.getsize(output_path),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/decode", methods=["POST"])
def decode_file():
    data = request.json
    stego_file = data.get("stego_file")
    hash_key = data.get("hash_key", "").strip()
    lsb_depth = int(data.get("lsb_depth", 1))
    source = data.get("source", "output")

    if not stego_file or not hash_key:
        return jsonify({"error": "Encoded WAV file and Hash Key are required"}), 400

    directory = OUTPUT_DIR if source == "output" else INPUT_DIR
    stego_path = os.path.join(directory, stego_file)

    if not os.path.exists(stego_path):
        return jsonify({"error": f"File not found: {stego_file}"}), 404

    try:
        compressed_data, name_ext, checksum = decode(stego_path, hash_key, lsb_depth)
        original_data = decompress_data(compressed_data)

        output_path = os.path.join(OUTPUT_DIR, name_ext)
        with open(output_path, "wb") as f:
            f.write(original_data)

        return jsonify({
            "success": True,
            "filename": name_ext,
            "size": len(original_data),
            "checksum": checksum,
            "output_path": output_path,
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Decoding failed: {str(e)}"}), 400


@app.route("/api/capacity", methods=["POST"])
def check_capacity():
    data = request.json
    filename = data.get("filename")
    source = data.get("source", "input")

    if not filename:
        return jsonify({"error": "No file specified"}), 400

    directory = INPUT_DIR if source == "input" else OUTPUT_DIR
    filepath = os.path.join(directory, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": f"File not found: {filename}"}), 404

    try:
        info = analyze_carrier(filepath)
        return jsonify({"success": True, **info})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/download/<folder>/<filename>")
def download_file(folder, filename):
    if folder not in ("input_files", "output_audio"):
        return jsonify({"error": "Invalid folder"}), 400

    filepath = os.path.join(folder, secure_filename(filename))
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    return send_file(filepath, as_attachment=True)


@app.route("/api/delete/<folder>/<filename>", methods=["DELETE"])
def delete_file(folder, filename):
    if folder not in ("input_files", "output_audio"):
        return jsonify({"error": "Invalid folder"}), 400

    filepath = os.path.join(folder, secure_filename(filename))
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    os.remove(filepath)
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
