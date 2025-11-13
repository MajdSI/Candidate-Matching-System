#!/usr/bin/env python3
"""
Generate professional black and white PDF resumes for specific CV IDs.
This script creates formatted PDFs that look like real resumes.
"""

import os
import sys
import re
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CV_PATH, CV_FMT, CV_ID_COL

# CV IDs to generate PDFs for
CV_IDS = [21, 29, 2, 152, 291]

# Output directory - save in a location that looks pre-generated
# Go up from app/ -> python-api/ -> server/ -> then to server/public/cvs/pdfs
OUTPUT_DIR = Path(__file__).parent.parent.parent / "public" / "cvs" / "pdfs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_candidate_name(cv_id: int) -> str:
    """
    Generate Arabic name in English letters based on cv_id.
    This matches the frontend name generation algorithm in client/src/lib/utils.ts
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
    
    # Remove duplicates while preserving order
    unique_last_names = list(dict.fromkeys(arabic_last_names))
    
    # Alternate between male and female names (cv_id % 2 === 0 is female)
    is_female = cv_id % 2 == 0
    first_names = arabic_female_names if is_female else arabic_male_names
    
    # Use same algorithm as frontend: (cv_id * 3) % len(first_names) and (cv_id * 5) % len(last_names)
    first_idx = (cv_id * 3) % len(first_names)
    last_idx = (cv_id * 5) % len(unique_last_names)
    
    return f"{first_names[first_idx]} {unique_last_names[last_idx]}"


def parse_cv_summary_json(cv_summary: str, cv_id: int, clean_cv: str = "", normalized_cv: str = "") -> Dict[str, Any]:
    """
    Parse CV summary JSON schema to extract structured information.
    The cv_summary column contains JSON with sections like:
    - title
    - years_experience
    - education (array)
    - key_skills (array)
    - tools_software (array)
    - achievements (array)
    - strengths (array)
    """
    result = {
        "name": generate_candidate_name(cv_id),  # Generate name using same algorithm as frontend
        "email": "",
        "phone": "",
        "location": "",
        "title": "",
        "years_experience": None,
        "education": [],
        "key_skills": [],
        "tools_software": [],
        "achievements": [],
        "strengths": [],
        "work_experience": [],
        "certifications": [],
    }
    
    # Try to extract contact info from clean_cv or normalized_cv
    contact_text = (clean_cv or normalized_cv or "").strip()
    if contact_text:
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, contact_text)
        if emails:
            result["email"] = emails[0]
        
        # Extract phone
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+966\s?\d{1,2}\s?\d{3}\s?\d{4}',
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, contact_text)
            if phones:
                result["phone"] = phones[0]
                break
    
    # Parse JSON from cv_summary
    if not cv_summary or pd.isna(cv_summary):
        return result
    
    cv_summary_str = str(cv_summary).strip()
    if not cv_summary_str.startswith('{'):
        return result
    
    try:
        cv_json = json.loads(cv_summary_str)
        
        # Extract all sections from JSON
        result["title"] = cv_json.get("title", "")
        result["years_experience"] = cv_json.get("years_experience")
        
        if isinstance(cv_json.get("education"), list):
            result["education"] = cv_json["education"]
        
        if isinstance(cv_json.get("key_skills"), list):
            result["key_skills"] = cv_json["key_skills"]
        
        if isinstance(cv_json.get("tools_software"), list):
            result["tools_software"] = cv_json["tools_software"]
        
        if isinstance(cv_json.get("achievements"), list):
            result["achievements"] = cv_json["achievements"]
        
        if isinstance(cv_json.get("strengths"), list):
            result["strengths"] = cv_json["strengths"]
        
        # Check for other possible sections
        if isinstance(cv_json.get("work_experience"), list):
            result["work_experience"] = cv_json["work_experience"]
        
        if isinstance(cv_json.get("certifications"), list):
            result["certifications"] = cv_json["certifications"]
        
        if isinstance(cv_json.get("experience"), list):
            result["work_experience"] = cv_json["experience"]
        
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse JSON from cv_summary: {e}")
        # Try to fix common JSON issues
        try:
            # Remove trailing commas or other issues
            fixed_json = re.sub(r',\s*}', '}', cv_summary_str)
            fixed_json = re.sub(r',\s*]', ']', fixed_json)
            cv_json = json.loads(fixed_json)
            # Apply same extraction logic as above
            result["title"] = cv_json.get("title", "")
            result["years_experience"] = cv_json.get("years_experience")
            if isinstance(cv_json.get("education"), list):
                result["education"] = cv_json["education"]
            if isinstance(cv_json.get("key_skills"), list):
                result["key_skills"] = cv_json["key_skills"]
            if isinstance(cv_json.get("tools_software"), list):
                result["tools_software"] = cv_json["tools_software"]
            if isinstance(cv_json.get("achievements"), list):
                result["achievements"] = cv_json["achievements"]
            if isinstance(cv_json.get("strengths"), list):
                result["strengths"] = cv_json["strengths"]
        except:
            pass
    
    return result


def create_pdf(cv_id: int, cv_data: Dict, output_path: Path):
    """
    Create a professional black and white PDF resume.
    """
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for the 'Flowable' objects
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles for professional resume
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#000000'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#000000'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#000000'),
        spaceAfter=18,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#000000'),
        spaceAfter=6,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=colors.HexColor('#000000'),
        borderPadding=4
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#000000'),
        spaceAfter=6,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )
    
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#000000'),
        leftIndent=20,
        spaceAfter=4,
        fontName='Helvetica'
    )
    
    # Header: Name
    name = cv_data.get("name", f"Candidate {cv_id}").strip()
    if not name or name == "":
        name = f"Candidate {cv_id}"
    
    story.append(Paragraph(name.upper(), title_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Title/Position
    title = cv_data.get("title", "")
    if title:
        story.append(Paragraph(title, subtitle_style))
    
    # Contact Information
    contact_info = []
    if cv_data.get("email"):
        contact_info.append(cv_data["email"])
    if cv_data.get("phone"):
        contact_info.append(cv_data["phone"])
    if cv_data.get("location"):
        contact_info.append(cv_data["location"])
    
    if contact_info:
        contact_text = " | ".join(contact_info)
        story.append(Paragraph(contact_text, contact_style))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Years of Experience (if available)
    years_exp = cv_data.get("years_experience")
    if years_exp:
        exp_text = f"{years_exp} years of experience" if isinstance(years_exp, (int, float)) else str(years_exp)
        story.append(Paragraph(exp_text, normal_style))
        story.append(Spacer(1, 0.15*inch))
    
    # Key Skills
    if cv_data.get("key_skills"):
        story.append(Paragraph("KEY SKILLS", section_style))
        skills = cv_data["key_skills"]
        # Format skills in a readable way (3-4 per line)
        skills_text = " • ".join(skills[:20])  # Limit to 20 skills
        story.append(Paragraph(skills_text, normal_style))
        story.append(Spacer(1, 0.15*inch))
    
    # Tools & Software
    if cv_data.get("tools_software"):
        story.append(Paragraph("TOOLS & SOFTWARE", section_style))
        tools = cv_data["tools_software"]
        tools_text = " • ".join(tools)
        story.append(Paragraph(tools_text, normal_style))
        story.append(Spacer(1, 0.15*inch))
    
    # Work Experience
    if cv_data.get("work_experience"):
        story.append(Paragraph("PROFESSIONAL EXPERIENCE", section_style))
        for exp in cv_data["work_experience"][:5]:  # Limit to 5 experiences
            if isinstance(exp, dict):
                exp_text = f"<b>{exp.get('title', exp.get('position', 'Position'))}</b>"
                if exp.get('company'):
                    exp_text += f" | {exp['company']}"
                if exp.get('period') or exp.get('duration'):
                    exp_text += f" | {exp.get('period', exp.get('duration', ''))}"
                story.append(Paragraph(exp_text, normal_style))
                if exp.get('description'):
                    desc = exp['description'][:200] + "..." if len(exp['description']) > 200 else exp['description']
                    story.append(Paragraph(desc, bullet_style))
            elif isinstance(exp, str):
                story.append(Paragraph(f"• {exp}", bullet_style))
            story.append(Spacer(1, 0.1*inch))
        story.append(Spacer(1, 0.15*inch))
    
    # Education
    if cv_data.get("education"):
        story.append(Paragraph("EDUCATION", section_style))
        for edu in cv_data["education"]:
            if isinstance(edu, str):
                story.append(Paragraph(f"• {edu}", bullet_style))
            elif isinstance(edu, dict):
                edu_text = edu.get("degree", edu.get("title", ""))
                if edu.get("school"):
                    edu_text += f" - {edu['school']}"
                if edu.get("year"):
                    edu_text += f" ({edu['year']})"
                story.append(Paragraph(f"• {edu_text}", bullet_style))
        story.append(Spacer(1, 0.15*inch))
    
    # Achievements
    if cv_data.get("achievements"):
        story.append(Paragraph("KEY ACHIEVEMENTS", section_style))
        for achievement in cv_data["achievements"][:8]:  # Limit to 8 achievements
            story.append(Paragraph(f"• {achievement}", bullet_style))
        story.append(Spacer(1, 0.15*inch))
    
    # Strengths
    if cv_data.get("strengths"):
        story.append(Paragraph("KEY STRENGTHS", section_style))
        strengths_text = " • ".join(cv_data["strengths"][:10])  # Limit to 10 strengths
        story.append(Paragraph(strengths_text, normal_style))
        story.append(Spacer(1, 0.15*inch))
    
    # Certifications
    if cv_data.get("certifications"):
        story.append(Paragraph("CERTIFICATIONS & QUALIFICATIONS", section_style))
        for cert in cv_data["certifications"][:6]:  # Limit to 6 certifications
            story.append(Paragraph(f"• {cert}", bullet_style))
        story.append(Spacer(1, 0.15*inch))
    
    # Build PDF
    doc.build(story)
    print(f"✓ Generated PDF for CV ID {cv_id}: {output_path}")


def main():
    """Main function to generate PDFs for specified CV IDs."""
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
        df = pd.read_parquet(os.path.expanduser(CV_PATH))
    else:
        raise ValueError(f"Unsupported format: {CV_FMT}")
    
    print(f"Loaded {len(df)} CVs")
    print(f"Generating PDFs for CV IDs: {CV_IDS}")
    
    # Filter for requested CV IDs
    if CV_ID_COL not in df.columns:
        print(f"Error: Column '{CV_ID_COL}' not found in CSV")
        return
    
    filtered_df = df[df[CV_ID_COL].isin(CV_IDS)]
    
    if len(filtered_df) < len(CV_IDS):
        found_ids = set(filtered_df[CV_ID_COL].tolist())
        missing_ids = set(CV_IDS) - found_ids
        print(f"Warning: Some CV IDs not found: {missing_ids}")
    
    # Generate PDF for each CV
    for cv_id in CV_IDS:
        cv_row = df[df[CV_ID_COL] == cv_id]
        
        if cv_row.empty:
            print(f"⚠ Skipping CV ID {cv_id}: Not found in dataset")
            continue
        
        # Get CV data from different columns
        cv_summary = None
        clean_cv = None
        normalized_cv = None
        
        if 'cv_summary' in cv_row.columns:
            cv_summary = cv_row['cv_summary'].iloc[0]
        if 'clean_cv' in cv_row.columns:
            clean_cv = cv_row['clean_cv'].iloc[0]
        if 'normalized_cv' in cv_row.columns:
            normalized_cv = cv_row['normalized_cv'].iloc[0]
        
        if not cv_summary or pd.isna(cv_summary):
            print(f"⚠ Skipping CV ID {cv_id}: No cv_summary available")
            continue
        
        # Parse CV summary JSON and extract contact info from other columns
        print(f"Parsing CV ID {cv_id}...")
        cv_data = parse_cv_summary_json(
            cv_summary=cv_summary,
            cv_id=cv_id,  # Pass cv_id for name generation
            clean_cv=str(clean_cv) if clean_cv and not pd.isna(clean_cv) else "",
            normalized_cv=str(normalized_cv) if normalized_cv and not pd.isna(normalized_cv) else ""
        )
        cv_data["cv_id"] = cv_id
        
        # Generate PDF filename
        name_slug = cv_data.get("name", f"candidate_{cv_id}").lower().replace(" ", "-")
        name_slug = re.sub(r'[^a-z0-9\-]', '', name_slug)
        if not name_slug:
            name_slug = f"candidate_{cv_id}"
        
        output_path = OUTPUT_DIR / f"{name_slug}_cv_{cv_id}.pdf"
        
        # Create PDF
        try:
            create_pdf(cv_id, cv_data, output_path)
        except Exception as e:
            print(f"✗ Error generating PDF for CV ID {cv_id}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✓ PDF generation complete! Files saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

