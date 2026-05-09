import pytest
from langchain_core.documents import Document
from app.rag.chunker import MarkdownChunker


class TestMarkdownChunker:
    def setup_method(self):
        self.chunker = MarkdownChunker(chunk_size=512, chunk_overlap=64)

    def test_empty_documents(self):
        result = self.chunker.split([])
        assert result == []

    def test_single_short_document(self):
        doc = Document(page_content="港口安全操作规程简要说明。", metadata={"doc_name": "test.md"})
        result = self.chunker.split([doc])
        assert len(result) >= 1
        # Each chunk should have doc_name metadata
        assert all(c.metadata.get("doc_name") == "test.md" for c in result)

    def test_document_with_markdown_headers(self):
        doc = Document(
            page_content="# 安全规程\n\n## 进入堆场\n\n必须佩戴安全帽。\n\n## 紧急情况\n\n立即报告值班人员。",
            metadata={"doc_name": "safety.md"},
        )
        result = self.chunker.split([doc])
        assert len(result) >= 1
        # At least one chunk should have a section title
        sections = [c.metadata.get("section_title", "") for c in result]
        assert any("安全规程" in s or "进入堆场" in s or "紧急情况" in s for s in sections)

    def test_document_without_headers(self):
        doc = Document(
            page_content="这是一段没有markdown标题的普通文本。" * 20,
            metadata={"doc_name": "plain.md"},
        )
        result = self.chunker.split([doc])
        assert len(result) >= 1
        for chunk in result:
            assert chunk.metadata.get("doc_name") == "plain.md"

    def test_multiple_documents(self):
        docs = [
            Document(page_content="文档一：" + "内容。" * 50, metadata={"doc_name": "doc1.md"}),
            Document(page_content="文档二：" + "数据。" * 50, metadata={"doc_name": "doc2.md"}),
        ]
        result = self.chunker.split(docs)
        assert len(result) >= 2
        doc_names = {c.metadata.get("doc_name") for c in result}
        assert "doc1.md" in doc_names
        assert "doc2.md" in doc_names

    def test_chunks_preserve_original_metadata(self):
        doc = Document(
            page_content="港口安全操作内容。" * 30,
            metadata={"doc_name": "ops.md", "doc_category": "safety"},
        )
        result = self.chunker.split([doc])
        for chunk in result:
            assert chunk.metadata.get("doc_category") == "safety"
            assert chunk.metadata.get("doc_name") == "ops.md"

    def test_chunk_size_respected(self):
        chunker = MarkdownChunker(chunk_size=200, chunk_overlap=20)
        doc = Document(page_content="X" * 1000, metadata={"doc_name": "big.md"})
        result = chunker.split([doc])
        for chunk in result:
            assert len(chunk.page_content) <= 220  # chunk_size + some tolerance

    def test_custom_chunk_params(self):
        chunker = MarkdownChunker(chunk_size=256, chunk_overlap=32)
        assert chunker.chunk_size == 256
        assert chunker.chunk_overlap == 32

    def test_chinese_content_splitting(self):
        doc = Document(
            page_content="## 第一章\n\n这是第一章的内容。" * 40,
            metadata={"doc_name": "chinese.md"},
        )
        result = self.chunker.split([doc])
        assert len(result) >= 1
        for chunk in result:
            assert isinstance(chunk.page_content, str)

    def test_section_title_metadata_set(self):
        doc = Document(
            page_content="### 危险品管理\n\n危险品必须单独存放并做好标识。",
            metadata={"doc_name": "hazmat.md"},
        )
        result = self.chunker.split([doc])
        for chunk in result:
            assert "section_title" in chunk.metadata
            assert "doc_name" in chunk.metadata
