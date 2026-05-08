from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.core.config import settings


class MarkdownChunker:
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        self.headers_to_split_on = [
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
        ]

        self.md_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False,
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", ".", "，", ",", " ", ""],
        )

    def split(self, documents: list[Document]) -> list[Document]:
        chunks = []
        for doc in documents:
            doc_chunks = self._split_single(doc)
            chunks.extend(doc_chunks)
        return chunks

    def _split_single(self, doc: Document) -> list[Document]:
        try:
            md_splits = self.md_splitter.split_text(doc.page_content)
        except Exception:
            return self.text_splitter.split_documents([doc])

        result = []
        for split in md_splits:
            subs = self.text_splitter.split_documents([split])
            for sub in subs:
                h1 = split.metadata.get("h1", "")
                h2 = split.metadata.get("h2", "")
                section = h2 or h1 or ""
                sub.metadata.update({
                    **doc.metadata,
                    "section_title": section,
                    "doc_name": doc.metadata.get("doc_name", ""),
                })
                result.append(sub)
        return result
