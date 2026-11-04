"""
Master Builder Script to Generate Complete Graduation Thesis in Microsoft Word (.docx)
Author: Nguyen Hai Nam (Student ID: 2221050693)
Faculty of Information Technology - Hanoi University of Mining and Geology
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path to import thesis_data
sys.path.insert(0, str(Path(__file__).parent))

DEFAULT_OUTPUT_PATH = Path("/Users/huongnguyen/Desktop/Đồ án tốt nghiệp/2221050693_Nguyen_Hai_Nam_DATN_V2.docx")

import docx
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

from thesis_data.front_matter import FRONT_MATTER_DATA
from thesis_data.chapter_1 import CHAPTER_1_DATA
from thesis_data.chapter_2 import CHAPTER_2_DATA
from thesis_data.chapter_3 import CHAPTER_3_DATA
from thesis_data.chapter_4 import CHAPTER_4_DATA
from thesis_data.chapter_5 import CHAPTER_5_DATA
from thesis_data.back_matter import BACK_MATTER_DATA
from thesis_data.tables_data import TABLES_DATA


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set cell padding in dxa (1 pt = 20 dxa)"""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_background(cell, color_hex="E5E7EB"):
    """Set cell background color"""
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)


set_cell_shading = set_cell_background


def add_page_number_to_footer(section):
    """Add dynamic page number to footer centered"""
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.font.name = 'Times New Roman'
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(100, 100, 100)

    fldChar1 = parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls('w'))
    instrText = parse_xml(r'<w:instrText %s xml:space="preserve"> PAGE </w:instrText>' % nsdecls('w'))
    fldChar2 = parse_xml(r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls('w'))
    fldChar3 = parse_xml(r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls('w'))
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)


def add_styled_paragraph(doc, text, style='body', space_before=0, space_after=6, indent=1.0, align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False, italic=False, size=13, color=RGBColor(0,0,0)):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.35
    
    if indent > 0 and align == WD_ALIGN_PARAGRAPH.JUSTIFY:
        p.paragraph_format.first_line_indent = Cm(indent)
    else:
        p.paragraph_format.first_line_indent = Cm(0)
        
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = color
    return p


def add_chapter_heading(doc, title):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(14)
    p.paragraph_format.line_spacing = 1.35
    p.paragraph_format.first_line_indent = Cm(0)
    
    run = p.add_run(title)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(16)
    run.bold = True
    run.font.color.rgb = RGBColor(15, 23, 42)
    return p


def add_heading_level_1(doc, title):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.35
    p.paragraph_format.first_line_indent = Cm(0)
    
    run = p.add_run(title)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(14)
    run.bold = True
    run.font.color.rgb = RGBColor(30, 41, 59)
    return p


def add_heading_level_2(doc, title):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.35
    p.paragraph_format.first_line_indent = Cm(0)
    
    run = p.add_run(title)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(13)
    run.bold = True
    run.italic = True
    run.font.color.rgb = RGBColor(51, 65, 85)
    return p


def add_custom_table(doc, table_data):
    """Add a beautifully formatted table into the docx document"""
    # Caption above table
    add_styled_paragraph(
        doc,
        table_data["title"],
        space_before=8,
        space_after=4,
        indent=0,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        bold=True,
        italic=True,
        size=12,
        color=RGBColor(30, 41, 59)
    )
    
    headers = table_data["headers"]
    rows = table_data["rows"]
    
    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # Format Header Row
    hdr_cells = table.rows[0].cells
    for i, h_text in enumerate(headers):
        hdr_cells[i].text = ""
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.first_line_indent = Cm(0)
        
        run = p.add_run(h_text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(11)
        run.bold = True
        run.font.color.rgb = RGBColor(15, 23, 42)
        
        set_cell_background(hdr_cells[i], "E2E8F0") # Slate-200
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=160, right=160)
        hdr_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    # Format Data Rows
    for r_idx, row_data in enumerate(rows):
        row_cells = table.rows[r_idx + 1].cells
        # Alternate zebra background
        row_bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, cell_value in enumerate(row_data):
            row_cells[c_idx].text = ""
            p = row_cells[c_idx].paragraphs[0]
            
            # Align: first col left, numbers center/right
            if c_idx == 0 and len(cell_value) > 20:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            elif any(char.isdigit() for char in cell_value) and len(cell_value) < 25:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.first_line_indent = Cm(0)
            
            run = p.add_run(str(cell_value))
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10.5)
            run.font.color.rgb = RGBColor(30, 41, 59)
            
            if row_bg != "FFFFFF":
                set_cell_background(row_cells[c_idx], row_bg)
            set_cell_margins(row_cells[c_idx], top=100, bottom=100, left=140, right=140)
            row_cells[c_idx].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            
    # Add spacing after table
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def build_thesis_docx(output_path: Path | str | None = None):
    target_path = Path(output_path) if output_path else DEFAULT_OUTPUT_PATH
    print("🚀 Bắt đầu quá trình biên soạn và đóng gói Báo cáo Đồ án Tốt nghiệp (.docx)...")
    print(f"🎯 Đường dẫn tệp đích: {target_path}")
    doc = docx.Document()
    
    # Configure A4 & Margins
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(3.5)
    section.right_margin = Cm(2.5)
    
    add_page_number_to_footer(section)
    
    # -------------------------------------------------------------
    # 1. TRANG BÌA CHÍNH
    # -------------------------------------------------------------
    print("📝 Đang tạo Trang bìa chính...")
    add_styled_paragraph(doc, FRONT_MATTER_DATA["university"], space_before=10, space_after=2, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=15)
    add_styled_paragraph(doc, f"{FRONT_MATTER_DATA['faculty']} - {FRONT_MATTER_DATA['department']}", space_before=0, space_after=20, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)
    
    add_styled_paragraph(doc, "---o0o---", space_before=10, space_after=30, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, size=12)
    
    add_styled_paragraph(doc, "BÁO CÁO ĐỒ ÁN TỐT NGHIỆP", space_before=20, space_after=15, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=18, color=RGBColor(30, 58, 138))
    
    add_styled_paragraph(doc, "ĐỀ TÀI:", space_before=10, space_after=6, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14)
    add_styled_paragraph(doc, FRONT_MATTER_DATA["thesis_title"], space_before=4, space_after=60, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=15, color=RGBColor(15, 23, 42))
    
    add_styled_paragraph(doc, f"Sinh viên thực hiện: {FRONT_MATTER_DATA['student_name']}", space_before=10, space_after=4, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)
    add_styled_paragraph(doc, f"Mã số sinh viên: {FRONT_MATTER_DATA['student_id']}", space_before=2, space_after=4, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, size=13)
    add_styled_paragraph(doc, f"Lớp: {FRONT_MATTER_DATA['class_name']}", space_before=2, space_after=10, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, size=13)
    add_styled_paragraph(doc, f"Giảng viên hướng dẫn: {FRONT_MATTER_DATA['supervisor']}", space_before=4, space_after=80, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)
    
    add_styled_paragraph(doc, FRONT_MATTER_DATA["location_year"], space_before=40, space_after=0, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=13)
    doc.add_page_break()

    # -------------------------------------------------------------
    # 2. TRANG PHỤ BÌA
    # -------------------------------------------------------------
    print("📝 Đang tạo Trang phụ bìa...")
    add_styled_paragraph(doc, FRONT_MATTER_DATA["university"], space_before=10, space_after=2, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14)
    add_styled_paragraph(doc, f"{FRONT_MATTER_DATA['faculty']} - {FRONT_MATTER_DATA['department']}", space_before=0, space_after=25, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=12)
    
    add_styled_paragraph(doc, "BÁO CÁO ĐỒ ÁN TỐT NGHIỆP", space_before=20, space_after=10, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16)
    add_styled_paragraph(doc, FRONT_MATTER_DATA["thesis_title"], space_before=4, space_after=50, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14)
    
    # Table for Signatures
    sig_table = doc.add_table(rows=3, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sig_cells = sig_table.rows[0].cells
    
    p1 = sig_cells[0].paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p1.add_run("GIẢNG VIÊN HƯỚNG DẪN\n(Ký và ghi rõ họ tên)\n\n\n\n\n")
    r1.font.name = 'Times New Roman'
    r1.bold = True
    r1_sub = p1.add_run(f"\n{FRONT_MATTER_DATA['supervisor']}")
    r1_sub.font.name = 'Times New Roman'
    r1_sub.bold = True

    p2 = sig_cells[1].paragraphs[0]
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("SINH VIÊN THỰC HIỆN\n(Ký và ghi rõ họ tên)\n\n\n\n\n")
    r2.font.name = 'Times New Roman'
    r2.bold = True
    r2_sub = p2.add_run(f"\n{FRONT_MATTER_DATA['student_name']}")
    r2_sub.font.name = 'Times New Roman'
    r2_sub.bold = True
    
    for row in sig_table.rows:
        for cell in row.cells:
            cell.width = Cm(7.5)
            
    doc.add_page_break()

    # -------------------------------------------------------------
    # 3. LỜI CAM ĐOAN & LỜI CẢM ƠN
    # -------------------------------------------------------------
    print("📝 Đang tạo Lời cam đoan và Lời cảm ơn...")
    add_chapter_heading(doc, "LỜI CAM ĐOAN")
    for para in FRONT_MATTER_DATA["commitment"]:
        add_styled_paragraph(doc, para)
    doc.add_page_break()

    add_chapter_heading(doc, "LỜI CẢM ƠN")
    for para in FRONT_MATTER_DATA["acknowledgments"]:
        add_styled_paragraph(doc, para)
    doc.add_page_break()

    # -------------------------------------------------------------
    # 4. TÓM TẮT ĐỒ ÁN (TIẾNG VIỆT & TIẾNG ANH)
    # -------------------------------------------------------------
    print("📝 Đang tạo Tóm tắt đồ án (Abstract)...")
    add_chapter_heading(doc, "TÓM TẮT ĐỒ ÁN")
    for para in FRONT_MATTER_DATA["abstract_vi"]:
        add_styled_paragraph(doc, para)
        
    add_styled_paragraph(doc, "Từ khóa: Dự báo xu hướng chứng khoán, LightGBM, PyTorch LSTM, Walk-Forward Purged Boundary, Backtesting T+2, Mô phỏng Monte Carlo, DNSE EnTrade X, Monorepo.", bold=True, italic=True)
    doc.add_page_break()

    add_chapter_heading(doc, "ABSTRACT")
    for para in FRONT_MATTER_DATA["abstract_en"]:
        add_styled_paragraph(doc, para)
        
    add_styled_paragraph(doc, "Keywords: Stock Trend Prediction, LightGBM GBDT, PyTorch Global LSTM, Walk-Forward Purged Boundary, T+2 Settlement Backtesting, Monte Carlo Permutation Test, DNSE EnTrade X, Monorepo Architecture.", bold=True, italic=True)
    doc.add_page_break()

    # -------------------------------------------------------------
    # 5. DANH MỤC TỪ VIẾT TẮT
    # -------------------------------------------------------------
    print("📝 Đang tạo Danh mục từ viết tắt...")
    add_chapter_heading(doc, "DANH MỤC CÁC TỪ VIẾT TẮT")
    
    acronym_table = doc.add_table(rows=len(FRONT_MATTER_DATA["acronyms"]) + 1, cols=3)
    acronym_table.style = 'Table Grid'
    acronym_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # Headers
    h_cells = acronym_table.rows[0].cells
    for i, title in enumerate(["Từ viết tắt", "Thuật ngữ tiếng Anh (Đầy đủ)", "Ý nghĩa giải thích tiếng Việt"]):
        h_cells[i].text = ""
        p = h_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(title)
        run.font.name = 'Times New Roman'
        run.bold = True
        run.font.size = Pt(11)
        set_cell_background(h_cells[i], "E2E8F0")
        set_cell_margins(h_cells[i], top=100, bottom=100, left=120, right=120)
        
    for idx, (abbr, en, vi) in enumerate(FRONT_MATTER_DATA["acronyms"]):
        r_cells = acronym_table.rows[idx + 1].cells
        for col_i, val in enumerate([abbr, en, vi]):
            r_cells[col_i].text = ""
            p = r_cells[col_i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_i == 0 else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(val)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10.5)
            if col_i == 0:
                run.bold = True
            set_cell_margins(r_cells[col_i], top=80, bottom=80, left=100, right=100)
            
    doc.add_page_break()

    # -------------------------------------------------------------
    # 6. DANH MỤC BẢNG BIỂU & HÌNH VẼ
    # -------------------------------------------------------------
    print("📝 Đang tạo Danh mục bảng biểu và hình vẽ...")
    add_chapter_heading(doc, "DANH MỤC CÁC BẢNG BIỂU")
    table_list = [
        "Bảng 1.1: So sánh đối chiếu các công trình nghiên cứu trong và ngoài nước",
        "Bảng 1.2: Danh mục 5 mã cổ phiếu VN30 nghiên cứu trọng điểm",
        "Bảng 2.1: Tổng hợp công thức toán học và ý nghĩa kinh tế các chỉ báo kỹ thuật cốt lõi",
        "Bảng 2.2: So sánh lý thuyết giữa mô hình dạng cây GBDT và Học sâu Deep Learning trên dữ liệu bảng",
        "Bảng 2.3: Ma trận lựa chọn và Luận giải Stack Công nghệ Monorepo",
        "Bảng 3.1: Ma trận 13 đặc trưng kỹ thuật tương đối không thứ nguyên trong features.py",
        "Bảng 3.2: Danh mục yêu cầu chức năng thực chiến (FR-01 đến FR-07)",
        "Bảng 3.3: Danh mục tiêu chuẩn nghiệm thu yêu cầu phi chức năng (NFR-01 đến NFR-04)",
        "Bảng 4.1: Cấu hình phân chia 3 cửa sổ Walk-Forward Expanding Windows trong khâu nghiên cứu",
        "Bảng 4.2: Danh mục các REST API Endpoints chính của hệ thống Backend FastAPI",
        "Bảng 5.1: Kết quả thực nghiệm mô hình cơ sở không tham số Naive Heuristic Baseline",
        "Bảng 5.2: Kết quả thực nghiệm mô hình học máy dạng bảng LightGBM GBDT Classifier",
        "Bảng 5.3: Kết quả thực nghiệm mô hình học sâu chuỗi thời gian PyTorch Global LSTM Classifier",
        "Bảng 5.4: Bảng tổng hợp 25 chỉ số định lượng tài chính Backtest Out-of-Sample trên 5 mã VN30",
        "Bảng 5.5: Kết quả thực nghiệm kiểm định Monte Carlo 100 lần trên cổ phiếu VIC",
        "Bảng 5.6: Kết quả đo kiểm hiệu năng mô hình thực chiến T+3 trên 4.425 mẫu (production_training_info_t3.json)",
        "Bảng 5.7: Đo kiểm độ trễ và thời gian phản hồi API thực chiến (Latency Benchmarks)",
        "Bảng 5.8: Tổng hợp kết quả 170 unit & integration tests tự động trên Monorepo"
    ]
    for t_item in table_list:
        add_styled_paragraph(doc, t_item, space_before=2, space_after=3, indent=0, align=WD_ALIGN_PARAGRAPH.LEFT, size=12)
        
    doc.add_page_break()

    # -------------------------------------------------------------
    # 7. CHƯƠNG 1: TỔNG QUAN ĐỀ TÀI
    # -------------------------------------------------------------
    print("📖 Đang biên soạn Chương 1: Tổng quan đề tài...")
    add_chapter_heading(doc, CHAPTER_1_DATA["title"])
    for sec in CHAPTER_1_DATA["sections"]:
        add_heading_level_1(doc, sec["title"])
        for sub in sec["subsections"]:
            add_heading_level_2(doc, sub["title"])
            for para in sub["paragraphs"]:
                add_styled_paragraph(doc, para)
                
            # Insert Tables at right subsections
            if sub["id"] == "1.1.2":
                add_custom_table(doc, TABLES_DATA["table_1_1"])
            elif sub["id"] == "1.3.2":
                add_custom_table(doc, TABLES_DATA["table_1_2"])
                
    doc.add_page_break()

    # -------------------------------------------------------------
    # 8. CHƯƠNG 2: CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ LIÊN QUAN
    # -------------------------------------------------------------
    print("📖 Đang biên soạn Chương 2: Cơ sở lý thuyết và công nghệ liên quan...")
    add_chapter_heading(doc, CHAPTER_2_DATA["title"])
    for sec in CHAPTER_2_DATA["sections"]:
        add_heading_level_1(doc, sec["title"])
        for sub in sec["subsections"]:
            add_heading_level_2(doc, sub["title"])
            for para in sub["paragraphs"]:
                add_styled_paragraph(doc, para)
                
            if sub["id"] == "2.1.3":
                add_custom_table(doc, TABLES_DATA["table_2_1"])
            elif sub["id"] == "2.2.2":
                add_custom_table(doc, TABLES_DATA["table_2_2"])
                
    doc.add_page_break()

    # -------------------------------------------------------------
    # 9. CHƯƠNG 3: KHẢO SÁT, PHÂN TÍCH YÊU CẦU VÀ THIẾT KẾ DỮ LIỆU
    # -------------------------------------------------------------
    print("📖 Đang biên soạn Chương 3: Khảo sát, phân tích yêu cầu và thiết kế dữ liệu...")
    add_chapter_heading(doc, CHAPTER_3_DATA["title"])
    for sec in CHAPTER_3_DATA["sections"]:
        add_heading_level_1(doc, sec["title"])
        for sub in sec["subsections"]:
            add_heading_level_2(doc, sub["title"])
            for para in sub["paragraphs"]:
                add_styled_paragraph(doc, para)
                
            if sub["id"] == "3.4.1":
                add_custom_table(doc, TABLES_DATA["table_3_1"])
            elif sub["id"] == "3.5.1":
                add_custom_table(doc, TABLES_DATA["table_3_2"])
                
    doc.add_page_break()

    # -------------------------------------------------------------
    # 10. CHƯƠNG 4: THIẾT KẾ VÀ HIỆN THỰC HÓA HỆ THỐNG
    # -------------------------------------------------------------
    print("📖 Đang biên soạn Chương 4: Thiết kế và hiện thực hóa hệ thống...")
    add_chapter_heading(doc, CHAPTER_4_DATA["title"])
    for sec in CHAPTER_4_DATA["sections"]:
        add_heading_level_1(doc, sec["title"])
        for sub in sec["subsections"]:
            add_heading_level_2(doc, sub["title"])
            for para in sub["paragraphs"]:
                add_styled_paragraph(doc, para)
                
            if sub["id"] == "4.3.1":
                add_custom_table(doc, TABLES_DATA["table_4_1"])
            elif sub["id"] == "4.7.2":
                add_custom_table(doc, TABLES_DATA["table_4_2"])
                
    doc.add_page_break()

    # -------------------------------------------------------------
    # 11. CHƯƠNG 5: KẾT QUẢ THỰC NGHIỆM VÀ ĐÁNH GIÁ HỆ THỐNG
    # -------------------------------------------------------------
    print("📖 Đang biên soạn Chương 5: Kết quả thực nghiệm và đánh giá hệ thống...")
    add_chapter_heading(doc, CHAPTER_5_DATA["title"])
    for sec in CHAPTER_5_DATA["sections"]:
        add_heading_level_1(doc, sec["title"])
        for sub in sec["subsections"]:
            add_heading_level_2(doc, sub["title"])
            for para in sub["paragraphs"]:
                add_styled_paragraph(doc, para)
                
            if sub["id"] == "5.2.1":
                add_custom_table(doc, TABLES_DATA["table_5_1"])
                add_custom_table(doc, TABLES_DATA["table_5_2"])
                add_custom_table(doc, TABLES_DATA["table_5_3"])
            elif sub["id"] == "5.4.1":
                add_custom_table(doc, TABLES_DATA["table_5_4"])
            elif sub["id"] == "5.5.1":
                add_custom_table(doc, TABLES_DATA["table_5_5"])
            elif sub["id"] == "5.6.1":
                add_custom_table(doc, TABLES_DATA["table_5_6"])
            elif sub["id"] == "5.6.2":
                add_custom_table(doc, TABLES_DATA["table_5_7"])
            elif sub["id"] == "5.7.2":
                add_custom_table(doc, TABLES_DATA["table_5_8"])
                
    doc.add_page_break()

    # -------------------------------------------------------------
    # 12. PHẦN KẾT: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN
    # -------------------------------------------------------------
    print("📖 Đang biên soạn Kết luận và Hướng phát triển...")
    add_chapter_heading(doc, BACK_MATTER_DATA["conclusion"]["title"])
    
    add_heading_level_1(doc, "1. KẾT LUẬN (NHỮNG KẾT QUẢ ĐÃ ĐẠT ĐƯỢC)")
    for p_acc in BACK_MATTER_DATA["conclusion"]["accomplishments"]:
        add_styled_paragraph(doc, p_acc)
        
    add_heading_level_1(doc, "2. HẠN CHẾ CÒN TỒN TẠI (TÍNH TRUNG THỰC HỌC THUẬT)")
    for p_lim in BACK_MATTER_DATA["conclusion"]["limitations"]:
        add_styled_paragraph(doc, p_lim)

    add_heading_level_1(doc, "3. HƯỚNG PHÁT TRIỂN MỞ RỘNG TIẾP THEO")
    for p_fw in BACK_MATTER_DATA["conclusion"]["future_work"]:
        add_styled_paragraph(doc, p_fw)
        
    doc.add_page_break()

    # -------------------------------------------------------------
    # 13. TÀI LIỆU THAM KHẢO (19 IEEE REFERENCES)
    # -------------------------------------------------------------
    print("📚 Đang lập Danh mục Tài liệu tham khảo chuẩn IEEE...")
    add_chapter_heading(doc, "DANH MỤC TÀI LIỆU THAM KHẢO")
    for ref in BACK_MATTER_DATA["references"]:
        add_styled_paragraph(doc, ref, space_before=3, space_after=4, indent=0, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=11.5)
        
    doc.add_page_break()

    # -------------------------------------------------------------
    # 14. PHỤ LỤC
    # -------------------------------------------------------------
    print("📎 Đang biên soạn Phụ lục...")
    add_chapter_heading(doc, "PHỤ LỤC")
    for app in BACK_MATTER_DATA["appendix"]:
        add_heading_level_1(doc, app["title"])
        for c in app["content"]:
            add_styled_paragraph(doc, c, space_before=2, space_after=3, indent=0.5, size=12)

    # -------------------------------------------------------------
    # SAVE FILE
    # -------------------------------------------------------------
    target_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(target_path))

    # Đồng bộ bộ phông nhúng (Embedded Fonts) từ bản mẫu V1 backup nếu tồn tại để bảo đảm chuẩn typography và dung lượng
    backup_v1 = Path("docs/backups/2221050693_Nguyen_Hai_Nam_DATN_V1_backup.docx")
    if backup_v1.exists():
        try:
            import zipfile
            with zipfile.ZipFile(target_path, "r") as z_in:
                target_entries = {item.filename: (z_in.read(item.filename), item.compress_type) for item in z_in.infolist()}
            with zipfile.ZipFile(backup_v1, "r") as z_v1:
                for item in z_v1.infolist():
                    if item.filename.startswith("word/fonts/") or item.filename in ("word/fontTable.xml",):
                        target_entries[item.filename] = (z_v1.read(item.filename), item.compress_type)
            with zipfile.ZipFile(target_path, "w") as z_out:
                for filename, (data, comp) in target_entries.items():
                    # Lưu trữ fonts bằng ZIP_STORED để phù hợp định dạng nhúng font của Microsoft Word
                    c_type = zipfile.ZIP_STORED if filename.startswith("word/fonts/") else comp
                    z_out.writestr(filename, data, compress_type=c_type)
            print("✨ Đã bảo tồn bộ phông chữ nhúng (Embedded Fonts) chuẩn typography từ bản mẫu.")
        except Exception as e:
            print(f"Lưu ý: Không thể đồng bộ phông nhúng: {e}")

    print(f"🎉 THÀNH CÔNG! Đã đóng gói hoàn chỉnh Báo cáo ĐATN tại:\n👉 {target_path.resolve()}")
    return target_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build complete graduation thesis DOCX")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_PATH),
        help=f"Output DOCX file path (default: {DEFAULT_OUTPUT_PATH})",
    )
    args = parser.parse_args()
    build_thesis_docx(args.output)
