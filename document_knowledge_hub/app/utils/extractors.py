from typing import Optional
from PyPDF2 import PdfReader
import docx
import io

def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text_chunks = []
        for p in reader.pages:
            text_chunks.append(p.extract_text() or "")
        return "\n".join(text_chunks)
    except Exception as e:
        return ""

def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        f = io.BytesIO(file_bytes)
        doc = docx.Document(f)
        paragraphs = [p.text for p in doc.paragraphs]
        return "\n".join(paragraphs)
    except Exception as e:
        return ""

def extract_text_from_txt(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode(errors="ignore")
    except Exception as e:
        return ""

def extract_text(filename: str, content: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(content)
    if lower.endswith(".docx"):
        return extract_text_from_docx(content)
    if lower.endswith(".txt"):
        return extract_text_from_txt(content)
    # fallback
    return content.decode(errors="ignore")
