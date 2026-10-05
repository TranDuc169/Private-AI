import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from './api.js';
import { extractionNotice, uploadFailureNotice } from './pdfStatus.js';

export function UploadNotice({ notice }) {
  if (!notice) return null;
  return <div className={`upload-notice ${notice.kind}`} role={notice.kind === 'error' ? 'alert' : 'status'} aria-live={notice.kind === 'error' ? 'assertive' : 'polite'}>
    <strong>{notice.title}</strong><p>{notice.message}</p>
  </div>;
}

export default function PdfUpload({ token, workspace, onUnauthorized, onDocument, onBusy, compact = false, disabled = false }) {
  const [file, setFile] = useState(null);
  const [notice, setNotice] = useState(null);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const input = useRef(null);
  const active = useRef(null);
  useEffect(() => () => { active.current?.abort(); active.current = null; }, []);
  const blocked = disabled || !workspace || busy;

  function choose(files) {
    if (blocked || !files?.length) return;
    if (files.length > 1 || !files[0].name.toLowerCase().endsWith('.pdf')) {
      setNotice({ kind: 'error', title: 'Chưa chọn được file', message: 'Mỗi lần chọn một file có đuôi .pdf.' });
      setFile(null); return;
    }
    setFile(files[0]); setNotice(null);
  }

  async function upload() {
    if (!file || blocked || active.current) return;
    const controller = new AbortController(); active.current = controller;
    let saved = null;
    const current = () => active.current === controller && !controller.signal.aborted;
    const options = { token, signal: controller.signal, method: 'POST' };
    const base = `/workspaces/${workspace.id}/documents`;
    setBusy(true); onBusy?.(true);
    setNotice({ kind: 'progress', title: 'Đang tải PDF lên…', message: `“${file.name}” → workspace “${workspace.name}”.` });
    try {
      const body = new FormData(); body.append('file', file);
      saved = await apiRequest(base, { ...options, body });
      if (!current()) return;
      onDocument?.(saved); setFile(null);
      setNotice({ kind: 'progress', title: 'Tải lên thành công · đang đọc văn bản…', message: `File “${saved.filename}” đã được lưu. Vui lòng chờ kết quả trích xuất.` });
      const result = await apiRequest(`${base}/${saved.id}/process`, options);
      if (!current()) return;
      onDocument?.(result); setNotice(extractionNotice(result));
    } catch (error) {
      if (current()) {
        setNotice(uploadFailureNotice(error, saved));
        if (error.status === 401) onUnauthorized();
      }
    } finally {
      if (current()) { active.current = null; setBusy(false); onBusy?.(false); }
    }
  }

  return <div className={`pdf-upload ${compact ? 'compact' : 'upload-panel'} ${dragging ? 'dragging' : ''}`}
    onDragOver={e => { e.preventDefault(); if (!blocked) setDragging(true); }}
    onDragLeave={e => { if (!e.currentTarget.contains(e.relatedTarget)) setDragging(false); }}
    onDrop={e => { e.preventDefault(); setDragging(false); choose(e.dataTransfer.files); }}>
    <label className="sr-only">Chọn PDF<input ref={input} type="file" accept=".pdf,application/pdf" disabled={blocked} onChange={e => { choose(e.target.files); e.target.value = ''; }} /></label>
    <div className="attachment-controls"><button type="button" className="secondary attach-button" disabled={blocked} onClick={() => input.current.click()}>{compact ? '+ Đính kèm PDF' : 'Chọn PDF'}</button>
      <small>{workspace ? `Lưu vào: ${workspace.name}` : 'Chọn workspace trước khi đính kèm.'}</small>
    </div>
    {file && <div className="selected-file"><span>📄 {file.name} · {(file.size / 1024).toFixed(1)} KB</span><button type="button" className="secondary" disabled={busy} onClick={() => setFile(null)}>Bỏ chọn</button><button type="button" disabled={blocked} onClick={upload}>Tải lên và trích xuất</button></div>}
    {workspace && <small>Kéo thả một PDF vào đây hoặc bấm chọn. Giới hạn mặc định 20 MB; chưa hỗ trợ OCR.</small>}
    <UploadNotice notice={notice} />
    {compact && notice && !busy && <Link className="document-link" to="/documents">Mở Tài liệu để kiểm tra →</Link>}
  </div>;
}
