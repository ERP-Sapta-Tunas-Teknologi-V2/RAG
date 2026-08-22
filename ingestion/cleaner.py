from pathlib import Path
import pymupdf
import pymupdf4llm
import re

def convert_to_md(path):
    doc = pymupdf.open(path)
    pages = []

    for page_number in range(len(doc)):
        markdown = pymupdf4llm.to_markdown(doc, pages=[page_number])
        pages.append({"page": page_number + 1, "markdown": markdown})

    doc.close()
    return pages

def remove_bold(markdown):
    return markdown.replace("**", "")

def h1_to_h2(markdown):
    return re.sub(r"^# (?!#)", "## ", markdown, flags=re.MULTILINE)

def preprocessing(file_path):
    path = Path(file_path)
    if path.suffix.lower() != ".pdf": raise ValueError(f"Unsupported file type: {path.suffix}")

    pages = convert_to_md(path)
    for page in pages:
        markdown = page["markdown"]
        markdown = remove_bold(markdown)
        markdown = h1_to_h2(markdown)

        page["markdown"] = markdown
    return pages