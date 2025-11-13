#!/usr/bin/env python3
"""
Generate a single PDF file containing all CV information for specified CV IDs.
Each candidate will have: Name, CV Summary (JSON), and Clean CV text.
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CV_PATH, CV_FMT, CV_ID_COL

# CV IDs to include
CV_IDS = [21, 29, 2, 152, 291]

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent.parent / "public" / "cvs" / "pdfs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Output filename
OUTPUT_FILE = OUTPUT_DIR / "all_candidates_combined.pdf"


def generate_candidate_name(cv_id: int) -> str:
    """
    Generate Arabic name in English letters based on cv_id.
    This matches the frontend name generation algorithm.
    """
    arabic_male_names = [
        "Saad", "Khalid", "Mohammed", "Ahmed", "Omar", "Yusuf", "Ibrahim", 
        "Hassan", "Ali", "Faisal", "Sultan", "Nasser", "Majed", "Turki", "Bandar",
        "Abdullah", "Fahad", "Saud", "Khalil", "Zaid", "Hamza", "Tariq", "Bader",
        "Mansour", "Raed", "Waleed", "Fares", "Yazeed", "Khaled", "Saeed", "Nawaf",
        "Mutaz", "Sami", "Hani", "Rami", "Fadi", "Tamer", "Yasser", "Bassam",
        "Tarek", "Wael", "Ziyad", "Hatem", "Majid", "Nader", "Osama", "Karim"
    ]
    arabic_female_names = [
        "Fatima", "Sara", "Noura", "Layla", "Amira", "Mariam", "Aisha", 
        "Hala", "Rania", "Lina", "Dina", "Yasmin", "Reem", "Hanan", "Nada",
        "Salma", "Rana", "Maya", "Leila", "Zeinab", "Hiba", "Rim", "Shaima",
        "Maha", "Noor", "Rahaf", "Lama", "Rawan", "Dana", "Tala", "Raghad",
        "Layan", "Jana", "Tara", "Yara", "Haya", "Nour", "Sana", "Hind",
        "Amina", "Lubna", "Noora", "Farah", "Sanaa", "Huda", "Mona", "Nadia"
    ]
    arabic_last_names = [
        "Alsaud", "Alotaibi", "Alharbi", "Alahmed", "Almutairi", "Alzahrani", 
        "Alshammari", "Alqarni", "Almalki", "Alghamdi", "Almousa", "Alrashid", 
        "Almazroa", "Alsharif", "Almuhanna", "Almawash", "Alshahrani", "Alqahtani", 
        "Aldosari", "Alhazmi", "Alfahad", "Almubarak", "Alkhaldi", "Almansoori",
        "Alhumaid", "Alsuwaidi", "Almazrouei", "Alshamsi", "Alnuaimi", "Aldhaheri",
        "Alblushi", "Alhosani", "Almazmi", "Alshahwi", "Alhinai", "Alraisi",
        "Alshukaili", "Almuhaimid", "Alhamdan", "Alshahri", "Almutawa", "Alshammasi",
        "Alkhatib", "Alshehri", "Alshahwan", "Almajed", "Alharbi", "Aldosari",
        "Alhazmi", "Alfahad", "Almubarak", "Alkhaldi", "Almansoori", "Alhumaid",
        "Alsuwaidi", "Alshamsi", "Alnuaimi", "Aldhaheri", "Alblushi", "Alhosani",
        "Alshahwan", "Almuhaimid", "Alhamdan", "Alshahri", "Almutawa", "Alshammasi",
        "Alkhatib", "Alshehri", "Almajed", "Alharbi", "Aldosari", "Alhazmi",
        "Alfahad", "Almubarak", "Alkhaldi", "Almansoori", "Alhumaid", "Alsuwaidi",
        "Alshamsi", "Alnuaimi", "Aldhaheri", "Alblushi", "Alhosani", "Almazmi"
    ]
    
    unique_last_names = list(dict.fromkeys(arabic_last_names))
    is_female = cv_id % 2 == 0
    first_names = arabic_female_names if is_female else arabic_male_names
    first_idx = (cv_id * 3) % len(first_names)
    last_idx = (cv_id * 5) % len(unique_last_names)
    
    return f"{first_names[first_idx]} {unique_last_names[last_idx]}"


def create_combined_pdf(candidates_data: list, output_path: Path):
    """
    Create a single PDF with all candidates' information.
    """
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Define custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#000000'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    candidate_header_style = ParagraphStyle(
        'CandidateHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#000000'),
        spaceAfter=8,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=colors.HexColor('#000000'),
        borderPadding=6
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#000000'),
        spaceAfter=6,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#000000'),
        spaceAfter=6,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )
    
    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Code'],
        fontSize=8,
        textColor=colors.HexColor('#000000'),
        spaceAfter=6,
        alignment=TA_LEFT,
        fontName='Courier',
        leftIndent=10,
        rightIndent=10,
        backColor=colors.HexColor('#F5F5F5')
    )
    
    # Title page
    story.append(Paragraph("CANDIDATE CV INFORMATION", title_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"Total Candidates: {len(candidates_data)}", normal_style))
    story.append(Paragraph(f"CV IDs: {', '.join(map(str, CV_IDS))}", normal_style))
    story.append(PageBreak())
    
    # Add each candidate
    for idx, candidate in enumerate(candidates_data, 1):
        cv_id = candidate["cv_id"]
        name = candidate["name"]
        
        # Candidate header
        story.append(Paragraph(f"CANDIDATE {idx}: CV ID {cv_id} - {name.upper()}", candidate_header_style))
        story.append(Spacer(1, 0.1*inch))
        
        # CV Summary Section
        story.append(Paragraph("CV SUMMARY (JSON)", section_style))
        cv_summary = candidate.get("cv_summary", "")
        if cv_summary and pd.notna(cv_summary):
            cv_summary_str = str(cv_summary).strip()
            # Try to format JSON nicely
            try:
                cv_json = json.loads(cv_summary_str)
                formatted_json = json.dumps(cv_json, indent=2, ensure_ascii=False)
                # Escape HTML special characters for ReportLab
                formatted_json = formatted_json.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(f"<font face='Courier' size='7'>{formatted_json}</font>", normal_style))
            except json.JSONDecodeError:
                # If JSON is malformed, show raw text
                cv_summary_escaped = cv_summary_str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(f"<font face='Courier' size='7'>{cv_summary_escaped}</font>", normal_style))
        else:
            story.append(Paragraph("No CV summary available", normal_style))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Clean CV Section
        story.append(Paragraph("CLEAN CV (Full Text)", section_style))
        clean_cv = candidate.get("clean_cv", "")
        if clean_cv and pd.notna(clean_cv):
            clean_cv_str = str(clean_cv).strip()
            # Escape HTML and break into paragraphs
            clean_cv_escaped = clean_cv_str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # Split into sentences/paragraphs for better readability
            paragraphs = clean_cv_escaped.split('\n')
            for para in paragraphs[:50]:  # Limit to first 50 paragraphs to avoid huge PDFs
                if para.strip():
                    story.append(Paragraph(f"<font size='8'>{para.strip()}</font>", normal_style))
            if len(paragraphs) > 50:
                story.append(Paragraph(f"<i><font size='7'>... (truncated, {len(paragraphs) - 50} more paragraphs)</font></i>", normal_style))
        else:
            story.append(Paragraph("No clean CV available", normal_style))
        
        # Add page break between candidates (except for the last one)
        if idx < len(candidates_data):
            story.append(PageBreak())
    
    # Build PDF
    doc.build(story)
    print(f"✓ Generated combined PDF: {output_path}")


def main():
    """Main function to generate combined PDF."""
    # Try multiple possible paths
    possible_paths = [
        os.path.expanduser(CV_PATH),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "Dataset", "final_summarized_cv.csv"),
        "Dataset/final_summarized_cv.csv",
    ]
    
    cv_file = None
    for path in possible_paths:
        if os.path.exists(path):
            cv_file = path
            break
    
    if not cv_file:
        print(f"Error: Could not find CV file. Tried: {possible_paths}")
        return
    
    print(f"Loading CV data from: {cv_file}")
    
    # Load CV data
    if CV_FMT.lower() == "csv":
        df = pd.read_csv(cv_file)
    elif CV_FMT.lower() == "parquet":
        df = pd.read_parquet(cv_file)
    else:
        raise ValueError(f"Unsupported format: {CV_FMT}")
    
    print(f"Loaded {len(df)} CVs")
    print(f"Generating combined PDF for CV IDs: {CV_IDS}")
    
    # Filter for requested CV IDs
    if CV_ID_COL not in df.columns:
        print(f"Error: Column '{CV_ID_COL}' not found in CSV")
        return
    
    # Collect data for all candidates
    candidates_data = []
    
    for cv_id in CV_IDS:
        cv_row = df[df[CV_ID_COL] == cv_id]
        
        if cv_row.empty:
            print(f"⚠ Skipping CV ID {cv_id}: Not found in dataset")
            continue
        
        r = cv_row.iloc[0]
        
        # Get all required data
        name = generate_candidate_name(cv_id)
        cv_summary = r.get('cv_summary', '')
        clean_cv = r.get('clean_cv', '')
        
        candidates_data.append({
            "cv_id": cv_id,
            "name": name,
            "cv_summary": cv_summary if pd.notna(cv_summary) else "",
            "clean_cv": clean_cv if pd.notna(clean_cv) else "",
        })
        
        print(f"✓ Collected data for CV ID {cv_id}: {name}")
    
    if not candidates_data:
        print("Error: No candidate data collected")
        return
    
    # Generate combined PDF
    try:
        create_combined_pdf(candidates_data, OUTPUT_FILE)
        print(f"\n✓ Combined PDF generation complete!")
        print(f"  File: {OUTPUT_FILE}")
        print(f"  Candidates included: {len(candidates_data)}")
    except Exception as e:
        print(f"✗ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

