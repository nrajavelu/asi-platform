"""Structure-aware chunker for the ingestion layer.

Splits on paragraph boundaries first, then packs sentences into chunks up to
a target word budget so no chunk straddles an unrelated paragraph. This is
the real logic the platform's RAG Knowledge Pipeline would run on 10-Ks,
transcripts, and case PDFs -- it just runs on plain text here.
"""
import re


def chunk_text(text: str, target_words: int = 110) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    chunks: list[str] = []
    for para in paragraphs:
        sentences = re.split(r"(?<=[.!?])\s+", para)
        buf: list[str] = []
        buf_words = 0
        for sentence in sentences:
            w = len(sentence.split())
            if buf and buf_words + w > target_words:
                chunks.append(" ".join(buf))
                buf, buf_words = [], 0
            buf.append(sentence)
            buf_words += w
        if buf:
            chunks.append(" ".join(buf))
    return chunks


def estimate_tokens(s: str) -> int:
    # Cheap fallback estimate (~1.35 tokens/word for English prose). The
    # benchmark harness prefers the real usage.input_tokens the API returns
    # whenever a live call is made; this is only for the ingestion-only path.
    return round(len(s.split()) * 1.35)
