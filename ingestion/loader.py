from docling.document_converter import DocumentConverter, InputFormat

converter = DocumentConverter()

def load_document(markdown):
    result = converter.convert_string(markdown, format=InputFormat.MD)
    return result.document