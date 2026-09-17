import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_pdf_report(analysis_dict, output_pdf_path):
    """
    Generate an executive, professional PDF analysis report using ReportLab.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    header_title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=colors.HexColor('#0B2545'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'HeaderSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#134074'),
        spaceAfter=12
    )
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=colors.HexColor('#006699'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#222222')
    )
    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#444444')
    )
    
    story = []
    
    # Title & Branding
    story.append(Paragraph("SATQUERY AI — REMOTE SENSING ANALYSIS REPORT", header_title_style))
    story.append(Paragraph("Autonomous Vision-Language Remote Sensing Image Analysis Platform", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#006699'), spaceAfter=12))
    
    # Metadata Box
    analysis_id = analysis_dict.get('analysis_id', 'N/A')
    mode = analysis_dict.get('mode', 'single').upper()
    query = analysis_dict.get('query', 'N/A')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    meta_data = [
        [Paragraph("<b>Analysis ID:</b>", body_style), Paragraph(analysis_id, body_style),
         Paragraph("<b>Date/Time:</b>", body_style), Paragraph(timestamp, body_style)],
        [Paragraph("<b>Analysis Mode:</b>", body_style), Paragraph(mode, body_style),
         Paragraph("<b>Platform:</b>", body_style), Paragraph("SatQuery AI v1.0", body_style)],
        [Paragraph("<b>User Query:</b>", body_style), Paragraph(f'"{query}"', body_style), "", ""]
    ]
    meta_table = Table(meta_data, colWidths=[1.1*inch, 2.5*inch, 1.1*inch, 2.5*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F0F4F8')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('SPAN', (1, 2), (3, 2)),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))
    
    # Quantitative Summary Metrics
    story.append(Paragraph("1. EXECUTIVE QUANTITATIVE SUMMARY", section_title_style))
    res = analysis_dict.get('result', {})
    conf = res.get('confidence', {})
    bldgs = res.get('buildings', {})
    water = res.get('water_bodies', {})
    agri = res.get('land_cover', {}).get('agriculture', 0.0)
    
    metrics_data = [
        ["Metric", "Value", "Scientific Basis / Category"],
        ["Confidence Score", f"{conf.get('score', 0)} / 100 ({conf.get('level', 'N/A')})", "Dynamic multi-factor radiometric + detector consistency"],
        ["Built-up Structures", f"{bldgs.get('count', 0)} Buildings", "Roof spectral & structural boundary segmentation"],
        ["Water Bodies", f"{water.get('count', 0)} Features", f"{water.get('coverage_percentage', 0.0)}% surface water coverage"],
        ["Agriculture Area", f"{agri}%", "Vegetation canopy density & index mapping"],
        ["Water Coverage", f"{water.get('coverage_percentage', 0.0)}%", "Normalized Difference Water Index / HSV proxy"]
    ]
    metrics_table = Table(metrics_data, colWidths=[1.8*inch, 1.8*inch, 3.6*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0B2545')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0,1), (-1,-1), 4),
        ('BOTTOMPADDING', (0,1), (-1,-1), 4),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 10))
    
    # AI Interpretation
    story.append(Paragraph("2. AI INTERPRETATION & VISION-LANGUAGE FINDINGS", section_title_style))
    answer_text = res.get('answer', 'No interpretation available.')
    for para in answer_text.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.replace("\n", "<br/>"), body_style))
            story.append(Spacer(1, 4))
            
    story.append(Spacer(1, 8))
    
    # Visual Evidence Section
    story.append(Paragraph("3. VISUAL EVIDENCE & SPATIAL ANNOTATIONS", section_title_style))
    evidence_info = res.get('evidence', {})
    evidence_path = evidence_info.get('file_path')
    if evidence_path and os.path.exists(evidence_path):
        try:
            img_w = 4.8 * inch
            img_h = 3.6 * inch
            story.append(RLImage(evidence_path, width=img_w, height=img_h))
            story.append(Spacer(1, 4))
            story.append(Paragraph("<b>Figure 1:</b> AI Visual Evidence overlay showing detected building structures (red bounding boxes), segmented water regions (blue mask), vegetation canopy (green mask), and compass alignment grid.", callout_style))
        except Exception as e:
            story.append(Paragraph(f"[Evidence Image render error: {str(e)}]", callout_style))
    else:
        story.append(Paragraph("Visual evidence overlay image is saved in the SatQuery archive.", callout_style))
        
    story.append(Spacer(1, 10))
    
    # Agent Execution Trace & Specialists
    story.append(Paragraph("4. AGENTIC AI EXECUTION TRACE", section_title_style))
    agent_info = analysis_dict.get('agent', {})
    steps = agent_info.get('execution_steps', [])
    specialists = agent_info.get('specialists_used', [])
    
    steps_p = "<br/>".join([f"• {s}" for s in steps]) if steps else "Standard pipeline executed."
    specs_p = ", ".join(specialists) if specialists else "Specialist suite"
    
    story.append(Paragraph(f"<b>Specialists Activated:</b> {specs_p}", body_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>Execution Workflow:</b><br/>{steps_p}", body_style))
    story.append(Spacer(1, 10))
    
    # Scientific Honesty & Limitations Box
    story.append(Paragraph("5. SCIENTIFIC INTEGRITY & SENSOR LIMITATIONS", section_title_style))
    disclaimer = (
        "<b>Important Scientific Notice:</b> SatQuery AI calculates all metrics directly from actual input pixel data, "
        "optical reflectance, and radar backscatter signals without fabrication. Estimated coverage percentages are "
        "image-relative unless rigorous ground control points (GCPs) and sensor calibration files are provided. "
        "Confidence scores indicate multi-factor detection stability and should not be confused with surveyed ground-truth accuracy."
    )
    disc_table = Table([[Paragraph(disclaimer, callout_style)]], colWidths=[7.2*inch])
    disc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEF3C7')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#F59E0B')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(disc_table)
    
    doc.build(story)
    return output_pdf_path
