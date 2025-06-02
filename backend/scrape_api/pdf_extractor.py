import io
import tempfile

# Primary: use PyPDF2 for text extraction
try:
    from pypdf import PdfReader  # pypdf>=3
except ImportError:
    from PyPDF2 import PdfReader  # fallback PyPDF2

# Fallback: pdfminer
try:
    from pdfminer.high_level import extract_text as _pdfminer_extract
except ImportError:
    _pdfminer_extract = None

def extract_text(pdf_bytes: bytes) -> str:
    """
    Extract and return human-readable text from PDF bytes using the best available library.
    """
    # First attempt with pypdf / PyPDF2
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = []
        for page in reader.pages:
            page_text = page.extract_text()
            print('page_text: ', page_text)
            if page_text:
                text.append(page_text)
        combined = '\n'.join(text).strip()
        if combined:
            return combined
    except Exception:
        pass
    # Fallback to pdfminer
    if _pdfminer_extract:
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=True) as tmp:
            tmp.write(pdf_bytes)
            tmp.flush()
            try:
                return _pdfminer_extract(tmp.name)
            except Exception:
                return ''
    return ''