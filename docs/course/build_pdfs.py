"""Rebuild the authored demo PDFs (optional authoring dependency: reportlab)."""
import hashlib
import json
import os
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

ROOT = Path(__file__).resolve().parent
LICENSE = """PostgreSQL Database Management System
Portions Copyright (c) 1996-2026, The PostgreSQL Global Development Group
Portions Copyright (c) 1994, The Regents of the University of California

Permission to use, copy, modify, and distribute this software and its documentation for any purpose, without fee, and without a written agreement is hereby granted, provided that the above copyright notice and this paragraph and the following two paragraphs appear in all copies.

IN NO EVENT SHALL THE UNIVERSITY OF CALIFORNIA BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF THE UNIVERSITY OF CALIFORNIA HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

THE UNIVERSITY OF CALIFORNIA SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE SOFTWARE PROVIDED HEREUNDER IS ON AN "AS IS" BASIS, AND THE UNIVERSITY OF CALIFORNIA HAS NO OBLIGATIONS TO PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS."""


def main():
    font = Path(os.environ.get('COURSE_FONT', 'C:/Windows/Fonts/arial.ttf'))
    if not font.exists():
        raise SystemExit('Set COURSE_FONT to a Unicode TrueType font file (for example DejaVuSans.ttf).')
    pdfmetrics.registerFont(TTFont('Course', str(font)))
    body = ParagraphStyle('body', fontName='Course', fontSize=12, leading=20, spaceAfter=14)
    title = ParagraphStyle('title', parent=body, fontSize=23, leading=30, textColor=colors.HexColor('#204a78'), spaceAfter=24)
    small = ParagraphStyle('small', parent=body, fontSize=8, leading=12, spaceAfter=6, wordWrap='CJK')
    def footer(canvas, doc):
        canvas.setFont('Course', 9); canvas.setFillColor(colors.HexColor('#556070'))
        canvas.drawString(48, 28, 'Trợ lý CSDL | Phiếu demo v1 | 27/10/2026')
        canvas.drawRightString(A4[0]-48, 28, str(doc.page))
    corpus = json.loads((ROOT/'corpus.json').read_text(encoding='utf-8'))
    output = ROOT/'pdfs'; output.mkdir(exist_ok=True)
    manifest = {'version':corpus['version'], 'accessed_on':'2026-10-27',
                'review_status':'AI-assisted draft; source-checked, pending student/instructor review', 'documents':[]}
    for document in corpus['documents']:
        story=[]
        for index,page in enumerate(document['pages']):
            if index: story.append(PageBreak())
            story.append(Paragraph(escape(document['topic']).upper(),small))
            story.append(Paragraph(escape(page['title']),title))
            for paragraph in page['text'].split('\n\n'):
                story.append(Paragraph(escape(paragraph),body))
            story.append(Spacer(1,16))
            story.append(Paragraph('Tài liệu demo được biên soạn có hỗ trợ AI, đã đối chiếu nguồn; cần nhóm/giảng viên rà soát trước khi dùng làm giáo trình. Không thực thi SQL trong ứng dụng.',small))
        story.extend([PageBreak(),Paragraph('Nguồn và quyền sử dụng',title)])
        story.append(Paragraph('Bản tóm lược tiếng Việt và ví dụ được biên soạn cho dự án; không phải bản dịch chính thức. Thay đổi: rút gọn, diễn giải và thêm ví dụ sinh viên/môn học. Tra cứu nguồn ngày 27/10/2026.',small))
        for reference in document['references']:
            story.append(Paragraph(escape(f"{reference['title']} | {reference['author']} | {reference['version']} | {reference['license']}"),small))
            story.append(Paragraph(escape(reference['url']),small))
        if any(r['license']=='CC BY 4.0' for r in document['references']):
            story.append(Paragraph('Database Design - 2nd Edition, Copyright 2014 Adrienne Watt and Nelson Eng. Adapted under CC BY 4.0: https://creativecommons.org/licenses/by/4.0/. No endorsement is implied. This adaptation is shared under CC BY 4.0.',small))
        else:
            for paragraph in LICENSE.split('\n\n'): story.append(Paragraph(escape(paragraph).replace('\n','<br/>'),small))
        target=output/document['filename']
        SimpleDocTemplate(str(target),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=48,bottomMargin=48,
                          title=document['topic'],author='Private-AI project - AI-assisted study notes').build(story,onFirstPage=footer,onLaterPages=footer)
        manifest['documents'].append({**{k:v for k,v in document.items() if k!='pages'},
                                      'path':'pdfs/'+document['filename'], 'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    (ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Built 5 demo PDFs and manifest.json')


if __name__ == '__main__': main()
