import re
from io import BytesIO

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.colors import HexColor
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

def clean_html(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    return ' '.join(text.split()).strip()

def create_pdf_from_resume(resume_data: dict) -> bytes:
    if not PDF_AVAILABLE:
        return b""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=50, bottomMargin=50)
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#1f2937'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=HexColor('#667eea'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        borderWidth=2,
        borderColor=HexColor('#667eea'),
        borderPadding=5,
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=HexColor('#374151'),
        spaceAfter=8,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=HexColor('#374151'),
        spaceAfter=8,
        leading=14,
        fontName='Helvetica'
    )
    
    personal_info = resume_data.get('personal_info', {})
    if personal_info.get('full_name'):
        elements.append(Paragraph(personal_info['full_name'], title_style))
        contact_parts = []
        if personal_info.get('email_address'):
            contact_parts.append(personal_info['email_address'])
        if personal_info.get('phone_number'):
            contact_parts.append(personal_info['phone_number'])
        if contact_parts:
            elements.append(Paragraph(' | '.join(contact_parts), body_style))
        elements.append(Spacer(1, 0.2 * inch))
    
    if resume_data.get('summary'):
        elements.append(Paragraph("Professional Summary", heading1_style))
        elements.append(Paragraph(resume_data['summary'], body_style))
    
    experiences = resume_data.get('experiences', [])
    if experiences:
        elements.append(Paragraph("Work Experience", heading1_style))
        for exp in experiences:
            title_company = f"{exp.get('role_title', '')} - {exp.get('company_name', '')}"
            elements.append(Paragraph(title_company, heading2_style))
            date_str = f"{exp.get('start_date', '')} - {exp.get('end_date', 'Present')}"
            elements.append(Paragraph(date_str, body_style))
            for desc in exp.get('description', []):
                elements.append(Paragraph(f"• {desc}", body_style))
    
    educations = resume_data.get('educations', [])
    if educations:
        elements.append(Paragraph("Education", heading1_style))
        for edu in educations:
            degree_major = f"{edu.get('degree', '')} in {edu.get('major', '')}"
            elements.append(Paragraph(degree_major, heading2_style))
            university = edu.get('university_name', '')
            if university:
                elements.append(Paragraph(university, body_style))
    
    skills = resume_data.get('skills', [])
    if skills:
        elements.append(Paragraph("Skills", heading1_style))
        skill_names = [s.get('skill_name', '') for s in skills if s.get('skill_name')]
        if skill_names:
            elements.append(Paragraph(', '.join(skill_names), body_style))
    
    certifications = resume_data.get('certifications', [])
    if certifications:
        elements.append(Paragraph("Certifications", heading1_style))
        for cert in certifications:
            cert_text = cert.get('certification_name', '')
            if cert.get('issuing_organization'):
                cert_text += f" - {cert['issuing_organization']}"
            elements.append(Paragraph(f"• {cert_text}", body_style))
    
    projects = resume_data.get('projects', [])
    if projects:
        elements.append(Paragraph("Projects", heading1_style))
        for proj in projects:
            elements.append(Paragraph(proj.get('project_name', ''), heading2_style))
            for desc in proj.get('description', []):
                elements.append(Paragraph(f"• {desc}", body_style))
    
    try:
        doc.build(elements)
        return buffer.getvalue()
    except Exception:
        return b""
    finally:
        buffer.close()
