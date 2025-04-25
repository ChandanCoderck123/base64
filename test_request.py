import requests
import base64
import sys

def send_pdf(pdf_path):
    with open(pdf_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')

    r = requests.post("http://127.0.0.1:5000/extract-text", json={
        "pdf_base64": encoded
    })

    print("Status:", r.status_code)
    print("Response:", r.json())

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_requests.py <pdf_path>")
    else:
        send_pdf(sys.argv[1])
