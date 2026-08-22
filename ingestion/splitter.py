from langchain_core.documents import Document
from transformers import AutoTokenizer

EMBEDDING_MODEL = "BAAI/bge-m3"

class StructureAwareChunker:
    def __init__(self, max_tokens=1000):
        self.tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)
        self.max_tokens = max_tokens

    def _extract_item_text(self, item, doc):
        text = getattr(item, "text", None) or getattr(item, "orig", None)

        if text and text.strip():
            return text

        if hasattr(item, "export_to_markdown"):
            try:
                text = item.export_to_markdown(doc=doc)
                if text and text.strip():
                    return text
            except Exception:
                pass

        return None

    def split_documents(self, docling_doc, source, document_id, category, uploaded_at):
        blocks = []

        for item, level in docling_doc.iterate_items():
            label = getattr(getattr(item, "label", None), "value", None)
            # with open("log/label_askrindo.txt", "a", encoding="utf-8") as f:
            #     f.write(f"LABEL={label} | TYPE={type(item).__name__} | TEXT={getattr(item, 'text', None)!r}\n\n")
            if label == "picture":
                continue

            text = self._extract_item_text(item, docling_doc)
            if not text or not text.strip():
                continue

            pages = []

            for prov in getattr(item, "prov", []) or []:
                if prov.page_no not in pages:
                    pages.append(prov.page_no)

            blocks.append({
                "text": text.strip(),
                "label": label,
                "level": level,
                "pages": pages
            })

        sections = self._build_sections(blocks)
        documents = []
        chunk_index = 0

        for section in sections:
            for chunk in self._chunk_section(section):
                documents.append(Document(
                    page_content=chunk["content"],
                    metadata={
                        "source": source,
                        "document_id": document_id,
                        "chunk_index": chunk_index,
                        "page": chunk["pages"],
                        "section": section["section"],
                        "section_title": section["title"],
                        "category": category,
                        "uploaded_at": uploaded_at
                    }
                ))
                chunk_index += 1

        return documents

    def _build_sections(self, blocks):
        sections = []
        current_section = None

        for block in blocks:
            if block["label"] == "section_header":
                if current_section:
                    sections.append(current_section)

                current_section = {
                    "title": block["text"], 
                    "section": self._extract_section_number(block["text"]), 
                    "blocks": [block]
                }
            elif current_section:
                current_section["blocks"].append(block)
            else:
                current_section = {"title": None, "section": None, "blocks": [block]}

        if current_section:
            sections.append(current_section)

        return sections

    def _chunk_section(self, section):
        chunks = []
        current_blocks = []
        current_tokens = 0

        heading = section["title"]

        for block in section["blocks"]:
            text = block["text"]
            tokens = len(self.tokenizer.encode(text, add_special_tokens=False))

            if block["label"] == "table" and tokens > self.max_tokens:
                if current_blocks:
                    chunks.append(self._make_chunk(current_blocks, heading))
                    current_blocks = []
                    current_tokens = 0

                for table_part in self._split_table_block(block):
                    chunks.append(self._make_chunk([table_part], heading))

                continue

            if current_blocks and current_tokens + tokens > self.max_tokens:
                chunks.append(self._make_chunk(current_blocks, heading))
                current_blocks = []
                current_tokens = 0

            current_blocks.append(block)
            current_tokens += tokens

        if current_blocks:
            chunks.append(self._make_chunk(current_blocks, heading))

        return chunks


    def _split_table_block(self, block):
        lines = block["text"].splitlines()

        if len(lines) <= 2:
            return [block]

        header = lines[:2]
        data_rows = lines[2:]

        parts = []
        current_lines = header.copy()
        current_tokens = len(
            self.tokenizer.encode("\n".join(current_lines), add_special_tokens=False)
        )

        for row in data_rows:
            row_tokens = len(
                self.tokenizer.encode(row, add_special_tokens=False)
            )

            if current_lines != header and current_tokens + row_tokens > self.max_tokens:
                parts.append({
                    **block,
                    "text": "\n".join(current_lines)
                })

                current_lines = header.copy()
                current_tokens = len(
                    self.tokenizer.encode("\n".join(current_lines), add_special_tokens=False)
                )

            current_lines.append(row)
            current_tokens += row_tokens

        if len(current_lines) > len(header):
            parts.append({
                **block,
                "text": "\n".join(current_lines)
            })

        return parts

    def _make_chunk(self, blocks, heading):
        content = "\n\n".join(block["text"] for block in blocks)

        if heading and not content.startswith(heading):
            content = f"{heading}\n\n{content}"

        content_tokens = len(self.tokenizer.encode(content, add_special_tokens=False))
        print(f"CHUNK | tokens={content_tokens} | chars={len(content)} | heading={heading!r}")

        pages = []

        for block in blocks:
            for page in block["pages"]:
                if page not in pages:
                    pages.append(page)

        return {"content": content, "pages": pages}

    def _extract_section_number(self, title):
        if not title:
            return None

        parts = title.split()

        if parts and parts[0][0].isdigit():
            return parts[0]

        return None