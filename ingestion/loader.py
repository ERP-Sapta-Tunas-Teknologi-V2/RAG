from docling.document_converter import DocumentConverter, InputFormat

def load_document(markdown):
    converter = DocumentConverter()
    result = converter.convert_string(markdown, format=InputFormat.MD)

    return result.document