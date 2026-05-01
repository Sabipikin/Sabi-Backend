"""Certificate generator service for creating PDF certificates"""

from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageTemplate, Frame
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
import uuid


class CertificateGenerator:
    """Generate professional PDF certificates for course/program/diploma completion"""
    
    COMPANY_NAME = "Sabikin"
    COMPANY_TAGLINE = "A subsidiary of Celgroup"
    CEO_NAME = "Caleb Ezidi Leo"
    
    # Certificate types and their display text
    CERTIFICATE_TYPES = {
        "course": "Certificate of Participation",
        "program": "Certification",
        "diploma": "Diploma"
    }
    
    @staticmethod
    def generate_certificate(
        student_name: str,
        item_type: str,  # 'course', 'program', 'diploma'
        item_name: str,
        completion_date: datetime,
        certificate_number: str,
        verification_code: str
    ) -> bytes:
        """
        Generate a professional PDF certificate
        
        Args:
            student_name: Name of the student
            item_type: Type of certificate ('course', 'program', 'diploma')
            item_name: Name of the course/program/diploma
            completion_date: Date of completion
            certificate_number: Unique certificate number
            verification_code: Verification/QR code data
            
        Returns:
            PDF as bytes
        """
        buffer = BytesIO()
        
        # Create PDF with landscape orientation
        pdf = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1*cm,
            bottomMargin=1*cm,
            title="Certificate of Achievement"
        )
        
        elements = []
        
        # Define styles
        title_style = ParagraphStyle(
            'CertificateTitle',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=32,
            textColor=colors.HexColor('#1F2937'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#6B7280'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        cert_type_style = ParagraphStyle(
            'CertType',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=28,
            textColor=colors.HexColor('#0369A1'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        student_name_style = ParagraphStyle(
            'StudentName',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=26,
            textColor=colors.HexColor('#1F2937'),
            spaceAfter=15,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'Body',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#374151'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#9CA3AF'),
            spaceAfter=2,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        # Header with company info
        header_text = f"<b>{CertificateGenerator.COMPANY_NAME}</b><br/>{CertificateGenerator.COMPANY_TAGLINE}"
        elements.append(Paragraph(header_text, title_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Certificate type line
        cert_label = "This is to certify that"
        elements.append(Paragraph(cert_label, body_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Student name
        elements.append(Paragraph(student_name.upper(), student_name_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Certificate message
        cert_type = CertificateGenerator.CERTIFICATE_TYPES.get(item_type, "Certificate")
        if item_type == "diploma":
            message = f"Has successfully completed and been awarded a<br/><b>{cert_type} in {item_name}</b>"
        else:
            message = f"Has successfully completed<br/><b>{cert_type} in {item_name}</b>"
        
        elements.append(Paragraph(message, cert_type_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Completion details
        completion_text = f"Completed on <b>{completion_date.strftime('%d %B %Y')}</b>"
        elements.append(Paragraph(completion_text, body_style))
        elements.append(Spacer(1, 0.8*cm))
        
        # Signature section (table layout)
        signature_data = [
            [
                "Caleb Ezidi Leo\nChief Executive Officer\nSabikin",
                "",
                "Certificate Number:\n" + certificate_number
            ],
            [
                "___________________",
                "",
                "Verification Code:\n" + verification_code
            ]
        ]
        
        signature_table = Table(
            signature_data,
            colWidths=[4.5*cm, 2*cm, 4.5*cm],
            rowHeights=[1.2*cm, 0.8*cm]
        )
        
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (2, 1), 'CENTER'),
            ('VALIGN', (0, 0), (2, 1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (2, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (2, 0), 10),
            ('FONTNAME', (2, 1), (2, 1), 'Helvetica'),
            ('FONTSIZE', (2, 1), (2, 1), 9),
            ('FONTCOLOR', (2, 1), (2, 1), colors.HexColor('#6B7280')),
            ('LEFTPADDING', (0, 0), (2, 1), 5),
            ('RIGHTPADDING', (0, 0), (2, 1), 5),
            ('TOPPADDING', (0, 0), (2, 1), 5),
            ('BOTTOMPADDING', (0, 0), (2, 1), 5),
        ]))
        
        elements.append(signature_table)
        elements.append(Spacer(1, 1*cm))
        
        # Footer
        footer_text = f"Issued on {datetime.now().strftime('%d %B %Y')} | This certificate verifies completion of the course/program/diploma listed above"
        elements.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        pdf.build(elements)
        
        # Get bytes and return
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def generate_verification_code() -> str:
        """Generate a unique verification code for certificate verification"""
        return str(uuid.uuid4())[:12].upper()
    
    @staticmethod
    def generate_certificate_number() -> str:
        """Generate a unique certificate number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = str(uuid.uuid4())[:8].upper()
        return f"SABIKIN-CERT-{timestamp}-{random_part}"
