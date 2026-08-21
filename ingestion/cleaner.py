import pymupdf4llm

def convert_to_md(file_path):
    markdown = pymupdf4llm.to_markdown(file_path)
    return markdown

def remove_bold(markdown):
    md_no_bold = markdown.replace("**", "")
    return md_no_bold

def preprocessing(file_path):
    md = convert_to_md(file_path)
    md_no_bold = remove_bold(md)
    return md_no_bold