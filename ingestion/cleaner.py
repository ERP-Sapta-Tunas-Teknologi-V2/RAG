from pathlib import Path
import pymupdf4llm
import re

def convert_to_md(path):
    return pymupdf4llm.to_markdown(path)

def remove_bold(markdown):
    return markdown.replace("**", "")

def h1_to_h2(markdown):
    return re.sub(r"^# (?!#)", "## ", markdown, flags=re.MULTILINE)

def preprocessing(file_path):
    path = Path(file_path)
    if path.suffix.lower() not in {".pdf"}:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    md = convert_to_md(path)
    md = remove_bold(md)
    md = h1_to_h2(md)
    
    return md