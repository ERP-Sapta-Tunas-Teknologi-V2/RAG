from docling.document_converter import DocumentConverter, InputFormat

converter = DocumentConverter()

def load_markdown(markdown):
    result = converter.convert_string(markdown, format=InputFormat.MD)
    return result.document

def load_document(file_path):
    result = converter.convert(file_path)
    return result.document