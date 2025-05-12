from flask import Flask, request, jsonify
import base64
from utils import extract_text_from_pdf

app = Flask(__name__)

@app.route('/extract-text', methods=['POST'])
def extract_text():
    data = request.get_json()

    if not data or 'pdf_base64' not in data:
        return jsonify({"error": "Missing 'pdf_base64' field in request."}), 400

    b64_string = "".join(data['pdf_base64'].split())

    missing_padding = len(b64_string) % 4
    if missing_padding:
        b64_string += '=' * (4 - missing_padding)

    try:
        pdf_bytes = base64.b64decode(b64_string, validate=True)

        # NEW: extract_text_from_pdf returns dictionary
        result = extract_text_from_pdf(pdf_bytes)

        return jsonify(result)

    except Exception as e:
        print("Extraction failed:", e)
        return jsonify({
            "error": "Text extraction failed.",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5003, debug=True)
