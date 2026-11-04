"""
Chapter 2: CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ LIÊN QUAN
Loaded and parsed directly from docs/reports/Chương 2 - Cơ sở lý thuyết và công nghệ liên quan.md
"""

import re
from pathlib import Path

def get_chapter_2_data():
    md_path = Path("docs/reports/Chương 2 - Cơ sở lý thuyết và công nghệ liên quan.md")
    text = md_path.read_text(encoding="utf-8")
    
    # Split by H2
    h2_pattern = re.compile(r"^## (2\.\d+\..*)$", re.M)
    h2_matches = list(h2_pattern.finditer(text))
    
    sections = []
    
    for i, match in enumerate(h2_matches):
        sec_title = match.group(1).strip()
        sec_id = sec_title.split()[0].rstrip(".")
        start_idx = match.end()
        end_idx = h2_matches[i+1].start() if i + 1 < len(h2_matches) else len(text)
        sec_body = text[start_idx:end_idx].strip()
        
        # Subsections under this H2
        h3_pattern = re.compile(r"^### (2\.\d+\.\d+\..*)$", re.M)
        h3_matches = list(h3_pattern.finditer(sec_body))
        
        subsections = []
        if h3_matches:
            for j, h3_m in enumerate(h3_matches):
                sub_title = h3_m.group(1).strip()
                sub_id = sub_title.split()[0].rstrip(".")
                sub_start = h3_m.end()
                sub_end = h3_matches[j+1].start() if j + 1 < len(h3_matches) else len(sec_body)
                sub_body = sec_body[sub_start:sub_end].strip()
                
                # Split body into paragraphs
                raw_paras = [p.strip() for p in sub_body.split("\n\n") if p.strip()]
                cleaned_paras = []
                for p in raw_paras:
                    # Clean markdown formatting like bold/bullet
                    cleaned_paras.append(p)
                    
                subsections.append({
                    "id": sub_id,
                    "title": sub_title,
                    "paragraphs": cleaned_paras
                })
        else:
            raw_paras = [p.strip() for p in sec_body.split("\n\n") if p.strip()]
            subsections.append({
                "id": sec_id + ".1",
                "title": sec_title,
                "paragraphs": raw_paras
            })
            
        sections.append({
            "id": sec_id,
            "title": sec_title,
            "subsections": subsections
        })
        
    return {
        "title": "CHƯƠNG 2: CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ LIÊN QUAN",
        "sections": sections
    }

CHAPTER_2_DATA = get_chapter_2_data()
