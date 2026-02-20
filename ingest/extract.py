from pathlib import Path
from pypdf import PdfReader

def extract_pdf(path: str) -> str:
    reader = PdfReader(path)
    return "\n\n".join(
        page.extract_text() or "" for page in reader.pages
    )

def extract_markdown(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")

def extract_file(path: str) -> str:
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        return extract_pdf(path)
    elif p.suffix.lower() in {".md", ".txt"}:
        return extract_markdown(path)
    raise ValueError(f"Unsupported file type: {p.suffix}")