import io
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY, TA_LEFT


def generate_approval_certificate_pdf(organ_request):
    """
    Generates a formal legal Government Organ Transplant Approval Certificate in PDF format.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#0F2C59')
    )
    
    sub_title_style = ParagraphStyle(
        'CertSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#31304D')
    )

    cert_num_style = ParagraphStyle(
        'CertNum',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#C70039')
    )

    body_style = ParagraphStyle(
        'CertBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=15,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#1E2022')
    )
    
    label_style = ParagraphStyle(
        'CertLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.HexColor('#0F2C59')
    )

    val_style = ParagraphStyle(
        'CertVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.black
    )

    story = []
    
    # Header Banner
    story.append(Paragraph("GOVERNMENT OF THE NATIONAL CAPITAL TERRITORY", sub_title_style))
    story.append(Paragraph("DIRECTORATE GENERAL OF HEALTH SERVICES", sub_title_style))
    story.append(Paragraph("AUTHORIZATION COMMITTEE FOR ORGAN TRANSPLANTATION", title_style))
    story.append(Spacer(1, 8))
    
    cert_no = organ_request.govt_approval_number or f"GOV-AUTH-2026-{organ_request.id:04d}"
    story.append(Paragraph(f"<b>CERTIFICATE REF NO:</b> {cert_no}", cert_num_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0F2C59'), spaceBefore=5, spaceAfter=15))
    
    # Legal Preamble
    preamble = (
        "<b>CERTIFICATE OF STATUTORY APPROVAL FOR HUMAN ORGAN ALLOCATION</b><br/><br/>"
        "In exercise of the powers conferred under Section 9, subsection (5) and (6) of the "
        "Transplantation of Human Organs and Tissues Act, the Competent Authorization Committee "
        "has scrutinized the clinical dossiers, HLA screening records, donor-recipient compatibility reports, "
        "and legal declarations. The Committee hereby accords official Government clearance for the organ allocation listed below:"
    )
    story.append(Paragraph(preamble, body_style))
    story.append(Spacer(1, 15))
    
    # Patient & Request Details Table
    patient_user = organ_request.patient
    profile = getattr(patient_user, 'profile', None)
    patient_name = patient_user.get_full_name() or patient_user.username
    
    table_data = [
        [
            Paragraph("<b>Recipient Full Name:</b>", label_style),
            Paragraph(patient_name, val_style),
            Paragraph("<b>National ID / MRN:</b>", label_style),
            Paragraph(getattr(profile, 'national_id', 'N/A') or 'N/A', val_style)
        ],
        [
            Paragraph("<b>Required Organ:</b>", label_style),
            Paragraph(f"<b>{organ_request.get_organ_display()}</b>", val_style),
            Paragraph("<b>Blood Group:</b>", label_style),
            Paragraph(f"<b>{organ_request.blood_group}</b>", val_style)
        ],
        [
            Paragraph("<b>Priority Level:</b>", label_style),
            Paragraph(organ_request.get_priority_level_display(), val_style),
            Paragraph("<b>Admitting Hospital:</b>", label_style),
            Paragraph(organ_request.hospital.name, val_style)
        ],
        [
            Paragraph("<b>Medical Reviewer:</b>", label_style),
            Paragraph(f"Dr. {organ_request.doctor_verified_by.get_full_name() or organ_request.doctor_verified_by.username if organ_request.doctor_verified_by else 'Verified Panel'}", val_style),
            Paragraph("<b>Verification Date:</b>", label_style),
            Paragraph(organ_request.doctor_verified_at.strftime("%d %b %Y, %H:%M") if organ_request.doctor_verified_at else "Verified", val_style)
        ],
        [
            Paragraph("<b>Government Official:</b>", label_style),
            Paragraph(organ_request.govt_approved_by.get_full_name() or organ_request.govt_approved_by.username if organ_request.govt_approved_by else "Authorized Signatory", val_style),
            Paragraph("<b>Approval Timestamp:</b>", label_style),
            Paragraph(organ_request.govt_approved_at.strftime("%d %b %Y, %H:%M") if organ_request.govt_approved_at else "Approved", val_style)
        ],
    ]
    
    t = Table(table_data, colWidths=[130, 140, 130, 140])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8F9FA')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DDE6ED')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    
    # Official Findings
    findings = (
        f"<b>Official Committee Findings & Decision:</b><br/>"
        f"<i>\"{organ_request.govt_notes or 'All legal, ethical and medical criteria satisfied. Approved for priority organ registry matching.'}\"</i>"
    )
    story.append(Paragraph(findings, body_style))
    story.append(Spacer(1, 15))
    
    # Security Clause & Signatures
    statutory_text = (
        "<b>LEGAL VALIDITY & COMPLIANCE NOTICE:</b><br/>"
        "This certificate is digitally logged in the State Organ Allocation Central Ledger with cryptographic immutability. "
        "Any unauthorized alteration, procurement without registry match, or financial transaction is strictly punishable "
        "with imprisonment under the Penal Code."
    )
    story.append(Paragraph(statutory_text, ParagraphStyle('Legal', parent=body_style, fontSize=8, leading=11, textColor=colors.HexColor('#526D82'))))
    story.append(Spacer(1, 30))
    
    # Signatures
    sig_data = [
        [
            Paragraph("____________________________<br/><b>Medical Review Board</b><br/>Authorized Doctor Signatory", ParagraphStyle('sig1', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8)),
            Paragraph("____________________________<br/><b>Government State Authority</b><br/>Competent Committee Chairperson", ParagraphStyle('sig2', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8)),
            Paragraph("<b>[OFFICIAL STATE SEAL]</b><br/>VERIFIED & DIGITALLY STAMPED<br/>" + cert_no, ParagraphStyle('sig3', parent=styles['Normal'], alignment=TA_CENTER, fontSize=7, textColor=colors.HexColor('#0F2C59'))),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[180, 180, 180])
    story.append(sig_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer
