import io # For byte stream operations on PDF bytes
import pdfplumber # Library to extract text from PDFs with structure preservation
import fitz  # # PyMuPDF for text extraction from PDFs
from pdf2image import convert_from_bytes # Converts PDF pages to images (for OCR fallback)
import pytesseract # Tesseract OCR engine to extract text from images
import mammoth  # for DOCX reading
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import subprocess
import tempfile
import os

def is_cid_garbage(text):
    """Detect text containing too many (cid:xx) glyphs — signs of embedded fonts without mapping."""
    if not text:
        return False # If empty, not considered CID garbage
    cid_count = text.count("(cid:") # Count how many times (cid:xxx) appears
    word_count = max(len(text.split()), 1)  # Total words in text (avoid divide by zero)
    return (cid_count / word_count) > 0.2 # If >20% of words are (cid:), consider it garbage

def is_garbage_text(text):
    """Check for short or non-readable text (symbols, gibberish)."""
    if not text or len(text.strip()) < 20:
        return True # Very short = likely garbage
    alnum_count = sum(c.isalnum() for c in text)  # Count how many characters are letters/numbers
    return (alnum_count / max(len(text), 1)) < 0.2 # If <20% are alphanum, mark as garbage

def convert_docx_to_pdf_bytes(docx_bytes):
    """Converts a DOCX to PDF using Unicode-safe rendering via ReportLab."""
    docx_stream = io.BytesIO(docx_bytes)
    result = mammoth.extract_raw_text(docx_stream)
    text_content = result.value.strip()

    if not text_content:
        raise ValueError("DOCX file contains no readable text.")

    buffer = io.BytesIO()

    # Register a Unicode-safe font (make sure the .ttf file is present or update path accordingly)
    pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))

    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("DejaVu", 11)
    width, height = A4
    y = height - 40

    for line in text_content.split("\n"):
        line = line.strip()
        if not line:
            y -= 15
            continue
        if y < 40:
            c.showPage()
            c.setFont("DejaVu", 11)
            y = height - 40
        c.drawString(40, y, line)
        y -= 15

    c.save()
    return buffer.getvalue()

def convert_doc_to_pdf_bytes(doc_bytes):
    """Converts a DOC (old binary) to PDF using LibreOffice in headless mode."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.doc') as temp_doc:
        temp_doc.write(doc_bytes)
        temp_doc_path = temp_doc.name

    output_pdf_path = temp_doc_path.replace('.doc', '.pdf')

    try:
        subprocess.run([
            "soffice",  # LibreOffice executable (must be installed and in PATH)
            "--headless",
            "--convert-to", "pdf",
            "--outdir", os.path.dirname(temp_doc_path),
            temp_doc_path
        ], check=True)
    
        with open(output_pdf_path, 'rb') as f:
            pdf_data = f.read()

        return pdf_data
    except subprocess.CalledProcessError as e:
        raise ValueError(f"LibreOffice failed to convert DOC to PDF: {e}")

    finally:
        # Always clean up temp files
        if os.path.exists(temp_doc_path):
            os.remove(temp_doc_path)
        if os.path.exists(output_pdf_path):
            os.remove(output_pdf_path)

def extract_text_from_pdf(pdf_or_docx_bytes):
    results = {}
    warnings = []
    errors = {}

    # Check if it's a PDF
    if not pdf_or_docx_bytes.startswith(b'%PDF'):
        try:
            # Try DOCX first
            pdf_or_docx_bytes = convert_docx_to_pdf_bytes(pdf_or_docx_bytes)
        except Exception as e:
            # If DOCX parsing fails, assume it might be old DOC format
            try:
                pdf_or_docx_bytes = convert_doc_to_pdf_bytes(pdf_or_docx_bytes)  
            except Exception as e2:
                raise ValueError(f"Failed to convert DOC/DOCX to PDF: {e2}")

    # 1. Try pdfplumber
    pdfplumber_text = ""
    try:
        with pdfplumber.open(io.BytesIO(pdf_or_docx_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pdfplumber_text += page_text + "\n"
        if is_cid_garbage(pdfplumber_text) or is_garbage_text(pdfplumber_text):
            warnings.append("pdfplumber output looks like garbage.")
    except Exception as e:
        errors["pdfplumber"] = str(e)

    results["pdfplumber"] = pdfplumber_text.strip()

    # 2. Try PyMuPDF
    pymupdf_text = ""
    try:
        with fitz.open(stream=pdf_or_docx_bytes, filetype="pdf") as doc:
            for page in doc:
                pymupdf_text += page.get_text()
        if is_cid_garbage(pymupdf_text) or is_garbage_text(pymupdf_text):
            warnings.append("pymupdf output looks like garbage.")
    except Exception as e:
        errors["pymupdf"] = str(e)

    results["pymupdf"] = pymupdf_text.strip()

    # 3. Try OCR
    ocr_text = ""
    try:
        images = convert_from_bytes(pdf_or_docx_bytes)
        for img in images:
            text = pytesseract.image_to_string(img)
            if text:
                ocr_text += text + "\n"
    except Exception as e:
        errors["ocr"] = str(e)

    results["ocr"] = ocr_text.strip()

    # 4. Select Best Output
    # Sort methods by length of extracted clean text (longest first)
    candidates = []
    for method, text in results.items():
        if text:
            candidates.append((len(text), method, text))

    # Sort longest text first
    candidates.sort(reverse=True)

    # Try first best then second best then third best
    final_method = None
    final_text = ""

    for _, method, text in candidates:
        if not is_cid_garbage(text) and not is_garbage_text(text):
            final_method = method
            final_text = text
            break

    if not final_text:
        raise ValueError(f"All extraction methods failed or returned unreadable content. Errors: {errors}")

    return {
        "method_used": final_method,
        "extracted_text": final_text.strip(),
        "warnings": warnings,
    }
