from flask import Flask, request, jsonify  # Flask components to handle server and HTTP
import base64                             # For decoding the Base64-encoded PDF
from utils import extract_text_from_pdf   # Import your main text extraction function

# Initialize the Flask application
app = Flask(__name__)

# Define the API route and method (POST request to extract text)
@app.route('/extract-text', methods=['POST'])
def extract_text():
    # Parse incoming JSON payload
    data = request.get_json()

    # Validate that the required field is present
    if not data or 'pdf_base64' not in data:
        return jsonify({"error": "Missing 'pdf_base64' field in request."}), 400

    # Sanitize Base64 string: remove whitespace or newlines
    b64_string = "".join(data['pdf_base64'].split())

    # Handle padding issues in Base64 string (must be multiple of 4)
    missing_padding = len(b64_string) % 4
    if missing_padding:
        b64_string += '=' * (4 - missing_padding)

    try:
        # Decode the Base64 string to get raw PDF bytes
        pdf_bytes = base64.b64decode(b64_string, validate=True)

        # Call our main function to extract text from the PDF bytes
        extracted_text = extract_text_from_pdf(pdf_bytes)

        # Return the extracted text in a JSON response
        return jsonify({"extracted_text": extracted_text})

    except Exception as e:
        # Catch all unexpected errors (pdfplumber, PyMuPDF, OCR, etc.)
        print("Extraction failed:", e)  # Print error for server logs
        return jsonify({
            "error": "Text extraction failed.",
            "details": str(e)  # Return specific error messages for debugging
        }), 500

# Run the Flask server in debug mode (auto-reloads, better error visibility)
if __name__ == '__main__':
    app.run(debug=True)
