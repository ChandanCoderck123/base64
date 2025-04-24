import requests
import base64

# Load your PDF and encode it to Base64
with open("sample.pdf", "rb") as pdf_file:
    encoded_pdf = base64.b64encode(pdf_file.read()).decode('utf-8')

response = requests.post("http://127.0.0.1:5003/extract-text", json={
    "pdf_base64": encoded_pdf
})

print(response.json())
