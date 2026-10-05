"""Deterministic page-aware character chunks and a bounded local Ollama client."""
import math
import httpx

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
DIMENSIONS = 1024


class EmbeddingError(Exception):
    """A safe, actionable message that can be returned to the browser."""


def chunk_pages(pages, maximum=3000):
    chunks = []
    for page in pages:
        text = page.text
        start = 0
        while start < len(text):
            end = min(start + CHUNK_SIZE, len(text))
            value = text[start:end]
            if value.strip():
                chunks.append(dict(chunk_index=len(chunks), page_number=page.page_number,
                                   start_char=start, end_char=end, text=value))
                if len(chunks) > maximum:
                    raise EmbeddingError("Tài liệu có quá nhiều đoạn. Hãy chia nhỏ PDF.")
            if end == len(text):
                break
            start = end - CHUNK_OVERLAP
    if not chunks:
        raise EmbeddingError("Tài liệu chưa có văn bản để tạo vector.")
    return chunks


def embed_batch(config, texts, timeout=None):
    try:
        with httpx.Client(timeout=timeout or config.embedding_timeout_seconds, trust_env=False) as client:
            response = client.post(config.ollama_base_url.rstrip('/') + '/api/embed', json={
                'model': config.embedding_model, 'input': texts, 'truncate': False,
            })
        if response.status_code == 404:
            raise EmbeddingError("Chưa có model BGE-M3. Chạy ollama pull bge-m3 rồi thử lại.")
        response.raise_for_status()
        data = response.json()
        vectors = data.get('embeddings') if isinstance(data, dict) else None
        if not isinstance(vectors, list) or len(vectors) != len(texts):
            raise ValueError('embedding count')
        normalized = []
        for vector in vectors:
            if not isinstance(vector, list) or len(vector) != DIMENSIONS:
                raise ValueError('embedding dimension')
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in vector):
                raise ValueError('non-finite embedding')
            norm = math.hypot(*vector)
            if not math.isfinite(norm) or norm == 0:
                raise ValueError('zero embedding')
            normalized.append([v / norm for v in vector])
        return normalized
    except httpx.TimeoutException:
        raise EmbeddingError("Ollama trả lời quá lâu. Kiểm tra model, chia nhỏ PDF hoặc thử lại.") from None
    except httpx.HTTPError:
        raise EmbeddingError("Không tạo được vector qua Ollama. Kiểm tra Ollama đang chạy và model BGE-M3.") from None
    except (ValueError, TypeError, OverflowError):
        raise EmbeddingError("Ollama trả vector không hợp lệ; cần BGE-M3 với 1024 chiều.") from None
