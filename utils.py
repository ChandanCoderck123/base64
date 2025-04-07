import io
import pdfplumber
import fitz
from pdf2image import convert_from_bytes
import pytesseract

def extract_text_from_pdf(pdf_bytes):
    extracted_text = ""
    errors = {}

    # Step 1: Try with pdfplumber
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"
    except Exception as e:
        errors['pdfplumber'] = str(e)

    # Step 2: Try with PyMuPDF (fitz)
    if not extracted_text.strip():
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                for page in doc:
                    extracted_text += page.get_text() + "\n"
        except Exception as e:
            errors['PyMuPDF'] = str(e)

    # Step 3: Try OCR with pytesseract
    if not extracted_text.strip():
        try:
            images = convert_from_bytes(pdf_bytes)
            for i, img in enumerate(images):
                text = pytesseract.image_to_string(img)
                if text:
                    extracted_text += text + "\n"
        except Exception as e:
            errors['OCR'] = str(e)

    # Final Check
    if not extracted_text.strip():
        raise ValueError(f"Text extraction failed. Errors: {errors}")

    return extracted_text
