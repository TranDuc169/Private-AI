"""One PDF per subprocess, with a parent-enforced deadline. No network or DB."""
import json
import sys

from pypdf import PdfReader


def extract(path, max_pages, max_characters):
    reader = PdfReader(path, strict=False)
    if reader.is_encrypted:
        return {"error": "PDF có mật khẩu. Hãy tải bản không mã hóa."}
    count = len(reader.pages)
    if count == 0 or count > max_pages:
        return {"error": f"PDF phải có từ 1 đến {max_pages} trang."}
    pages = []
    characters = 0
    for number, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").replace("\x00", "").strip()
        characters += len(text)
        if characters > max_characters:
            return {"error": "Văn bản PDF vượt giới hạn xử lý. Hãy chia nhỏ tài liệu."}
        pages.append({"page_number": number, "text": text})
    if not characters:
        return {"error": "Không tìm thấy văn bản. PDF có thể là bản scan; hiện chưa hỗ trợ OCR.", "page_count": count}
    return {"pages": pages, "page_count": count}


if __name__ == "__main__":
    try:
        result = extract(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
    except Exception:
        # Never return parser traces, local paths or PDF contents in errors.
        result = {"error": "Không đọc được PDF. File có thể bị hỏng hoặc không được hỗ trợ."}
    print(json.dumps(result, ensure_ascii=True))
