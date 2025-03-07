import io
import pdfplumber
import fitz

def extract_text_from_pdf(pdf_bytes):
    extracted_text = ""
    errors = {}

    # Try pdfplumber first
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"
    except Exception as e:
        errors['pdfplumber'] = str(e)

    # Fallback to PyMuPDF if no text extracted
    if not extracted_text.strip():
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                for page in doc:
                    extracted_text += page.get_text() + "\n"
        except Exception as e:
            errors['PyMuPDF'] = str(e)

    if not extracted_text.strip():
        raise ValueError(f"Text extraction failed. Errors: {errors}")

    return extracted_text
