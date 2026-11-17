from io import BytesIO
from pathlib import Path
import csv
import html
import json
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".csv", ".json", ".html", ".htm", ".docx"}


def extract_text(filename: str, content: bytes) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension or 'no extension'}")
    try:
        if extension == ".pdf":
            text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
        elif extension == ".docx":
            from docx import Document
            document = Document(BytesIO(content))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
            for table in document.tables:
                text += "\n" + "\n".join(" | ".join(cell.text for cell in row.cells) for row in table.rows)
        elif extension == ".csv":
            rows = csv.reader(content.decode("utf-8-sig").splitlines())
            text = "\n".join(" | ".join(row) for row in rows)
        elif extension == ".json":
            parsed = json.loads(content.decode("utf-8-sig"))
            text = json.dumps(parsed, ensure_ascii=False, indent=2)
        elif extension in {".html", ".htm"}:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content.decode("utf-8-sig"), "html.parser")
            for node in soup(["script", "style", "noscript"]):
                node.decompose()
            text = html.unescape(soup.get_text("\n"))
        else:
            text = content.decode("utf-8-sig")
    except (UnicodeDecodeError, json.JSONDecodeError, csv.Error) as exc:
        raise ValueError("The uploaded file is malformed or is not valid UTF-8 text") from exc
    text = text.strip()
    if not text:
        raise ValueError("No extractable text found in the uploaded document")
    return text
