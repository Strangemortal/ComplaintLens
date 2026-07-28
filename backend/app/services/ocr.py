import io
from pypdf import PdfReader

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extracts plain text from pdf bytes.
    """
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error during PDF text extraction: {e}")
        return ""
