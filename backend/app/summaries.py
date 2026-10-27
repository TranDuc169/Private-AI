"""Bounded topic coverage, independent of query-vector Top-K."""
import re
import unicodedata
from collections import defaultdict, deque

from sqlalchemy import select, func, or_

from app.models import Document, DocumentChunk, Workspace
from app.retrieval import candidate_filters
from app.schemas import RetrievalHit
from app.generation import generate_answer


def normalize(value):
    value = value.lower().replace('đ', 'd')
    return ''.join(c for c in unicodedata.normalize('NFD', value) if unicodedata.category(c) != 'Mn')


TOPICS = {
    'Mô hình quan hệ và ràng buộc': ('rang buoc', 'khoa chinh', 'khoa ngoai', 'quan he', 'primary key', 'foreign key'),
    'SQL và JOIN': ('sql', 'join', 'having', 'group by'),
    'ERD và chuẩn hóa': ('erd', 'chuan hoa', 'normalization', '1nf', '2nf', '3nf'),
    'Transaction': ('transaction', 'giao dich', 'commit', 'rollback', 'savepoint'),
    'Index và kế hoạch truy vấn': ('index', 'chi muc', 'explain', 'ke hoach truy van'),
}


def summary_topic(question):
    q = normalize(question)
    if not any(word in q for word in ('tom tat', 'tong hop', 'summary', 'summarize')):
        return False
    matches = [name for name, aliases in TOPICS.items() if any(re.search(r'\b' + re.escape(a) + r'\b', q) for a in aliases)]
    return matches[0] if len(matches) == 1 else None


def collect_topic(session, config, workspace_id, owner_id, topic):
    # Explicit scan bound; report incompleteness instead of claiming full coverage.
    unavailable = session.scalar(select(func.count()).select_from(Document).join(Workspace).where(
        Document.workspace_id == workspace_id, Workspace.owner_id == owner_id,
        or_(Document.status != 'ready', Document.index_status != 'ready',
            Document.embedding_model.is_(None), Document.embedding_model != config.embedding_model)))
    rows = session.execute(select(DocumentChunk, Document.filename).join(Document).join(Workspace)
        .where(*candidate_filters(workspace_id, owner_id, config.embedding_model))
        .order_by(Document.id, DocumentChunk.page_number, DocumentChunk.chunk_index).limit(3001)).all()
    truncated = len(rows) > 3000
    groups = defaultdict(list)
    for chunk, filename in rows[:3000]:
        content = normalize(chunk.text)
        if any(re.search(r'\b' + re.escape(a) + r'\b', content) for a in TOPICS[topic]):
            groups[(chunk.document_id, chunk.page_number)].append(RetrievalHit(
                chunk_id=chunk.id, document_id=chunk.document_id, filename=filename,
                page_number=chunk.page_number, chunk_index=chunk.chunk_index,
                start_char=chunk.start_char, end_char=chunk.end_char, text=chunk.text, score=0))
    matched = sum(map(len, groups.values()))
    # Round-robin across document/page groups; evenly spread groups when > 8.
    buckets = list(groups.values())
    if len(buckets) > 8:
        buckets = [buckets[round(i * (len(buckets)-1) / 7)] for i in range(8)]
    queues = deque(deque(group) for group in buckets)
    selected = []
    while queues and len(selected) < 8:
        queue = queues.popleft(); selected.append(queue.popleft())
        if queue: queues.append(queue)
    session.rollback()
    return selected, dict(topic=topic, matched_chunks=matched, selected_chunks=len(selected),
        unavailable_documents=unavailable, selected_pages=len({(h.document_id, h.page_number) for h in selected}), scan_truncated=truncated,
        partial=truncated or len(selected) < matched,
        limitation='Chọn theo từ khóa và trải theo tài liệu/trang, tối đa 8 đoạn; có thể bỏ sót cách diễn đạt khác. Không phải tóm tắt toàn bộ giáo trình.')


def summarize(config, question, hits):
    paragraphs, used = [], set()
    for offset in range(0, len(hits), 4):
        result = generate_answer(config,
            'Tóm tắt chủ đề theo các đoạn được cung cấp, chia ý ngắn bằng gạch đầu dòng. '
            'Chỉ nêu kiến thức có căn cứ; nói rõ phần không đủ thông tin. Yêu cầu: ' + question,
            hits[offset:offset+4])
        content = re.sub(r'\[(\d+)\]', lambda m: f'[{int(m[1])+offset}]', result.answer)
        paragraphs.append(content)
        used.update(i+offset for i in result.source_ids)
    return '\n\n'.join(paragraphs), sorted(used)
