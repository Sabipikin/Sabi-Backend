from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from io import BytesIO
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class InvoiceGenerator:
    """Service for generating PDF invoices"""

    def __init__(self):
        self.company_name = os.getenv("COMPANY_NAME", "Sabi Educate")
        self.company_email = os.getenv("SUPPORT_EMAIL", "support@sabieducate.com")
        self.company_address = os.getenv("COMPANY_ADDRESS", "Online Platform")
        self.company_phone = os.getenv("COMPANY_PHONE", "+1 (555) 000-0000")

    def generate_payment_invoice(self, payment_data: dict, user_data: dict) -> Optional[bytes]:
        """
        Generate a PDF invoice for a payment

        Args:
            payment_data: Payment details (id, amount, currency, item_type, item_name, etc.)
            user_data: User details (email, full_name, region, etc.)

        Returns:
            PDF bytes or None if generation fails
        """
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#667eea"),
                spaceAfter=30,
                alignment=TA_CENTER,
            )
            heading_style = ParagraphStyle(
                "CustomHeading",
                parent=styles["Heading2"],
                fontSize=12,
                textColor=colors.HexColor("#667eea"),
                spaceAfter=10,
                spaceBefore=10,
            )
            normal_style = ParagraphStyle(
                "CustomNormal",
                parent=styles["Normal"],
                fontSize=10,
                spaceAfter=6,
            )

            # Header with company info
            header_data = [
                [
                    Paragraph(
                        f"<b>{self.company_name}</b>",
                        ParagraphStyle(
                            "HeaderTitle",
                            parent=styles["Normal"],
                            fontSize=16,
                            textColor=colors.HexColor("#667eea"),
                            fontName="Helvetica-Bold",
                        ),
                    ),
                    Paragraph(
                        "<b>INVOICE</b>",
                        ParagraphStyle(
                            "InvoiceTitle",
                            parent=styles["Normal"],
                            fontSize=14,
                            alignment=TA_RIGHT,
                            fontName="Helvetica-Bold",
                        ),
                    ),
                ]
            ]
            header_table = Table(header_data, colWidths=[3.5 * inch, 3.5 * inch])
            header_table.setStyle(
                TableStyle([("ALIGN", (0, 0), (0, 0), "LEFT"), ("ALIGN", (1, 0), (1, 0), "RIGHT")])
            )
            elements.append(header_table)
            elements.append(Spacer(1, 0.3 * inch))

            # Invoice details
            invoice_num = f"INV-{payment_data.get('id', '0000')}"
            invoice_date = datetime.fromisoformat(
                payment_data.get("created_at", datetime.now().isoformat())
            ).strftime("%B %d, %Y")
            completed_date = (
                datetime.fromisoformat(payment_data.get("completed_at")).strftime("%B %d, %Y")
                if payment_data.get("completed_at")
                else "Pending"
            )

            details_data = [
                [
                    Paragraph(f"<b>Invoice #:</b> {invoice_num}", normal_style),
                    Paragraph(
                        f"<b>Invoice Date:</b> {invoice_date}",
                        ParagraphStyle("Normal", parent=styles["Normal"], alignment=TA_RIGHT),
                    ),
                ],
                [
                    Paragraph(f"<b>Status:</b> {payment_data.get('status', 'Pending').upper()}", normal_style),
                    Paragraph(
                        f"<b>Completed:</b> {completed_date}",
                        ParagraphStyle("Normal", parent=styles["Normal"], alignment=TA_RIGHT),
                    ),
                ],
            ]
            details_table = Table(details_data, colWidths=[3.5 * inch, 3.5 * inch])
            details_table.setStyle(
                TableStyle([("ALIGN", (0, 0), (0, 1), "LEFT"), ("ALIGN", (1, 0), (1, 1), "RIGHT")])
            )
            elements.append(details_table)
            elements.append(Spacer(1, 0.3 * inch))

            # Bill to
            elements.append(Paragraph("<b>BILL TO:</b>", heading_style))
            bill_to_data = [
                [Paragraph(user_data.get("full_name", "N/A"), normal_style)],
                [Paragraph(user_data.get("email", "N/A"), normal_style)],
                [Paragraph(user_data.get("region", ""), normal_style)] if user_data.get("region") else [],
            ]
            bill_to_data = [row for row in bill_to_data if row]  # Remove empty rows
            bill_to_table = Table(bill_to_data)
            elements.append(bill_to_table)
            elements.append(Spacer(1, 0.3 * inch))

            # Item details
            elements.append(Paragraph("<b>PURCHASE DETAILS:</b>", heading_style))

            item_data = [
                ["Description", "Qty", "Amount"],
                [
                    payment_data.get("item_name", "N/A"),
                    "1",
                    f"{payment_data.get('currency', 'GBP').upper()} {payment_data.get('amount', 0) / 100:.2f}",
                ],
            ]
            item_table = Table(item_data, colWidths=[4 * inch, 1 * inch, 1.5 * inch])
            item_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#667eea")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                    ]
                )
            )
            elements.append(item_table)
            elements.append(Spacer(1, 0.3 * inch))

            # Total
            total_data = [
                ["", "Subtotal:", f"{payment_data.get('currency', 'GBP').upper()} {payment_data.get('amount', 0) / 100:.2f}"],
                ["", "Tax:", "GBP 0.00"],
                [
                    "",
                    Paragraph("<b>TOTAL:</b>", ParagraphStyle("Bold", parent=styles["Normal"], fontName="Helvetica-Bold")),
                    Paragraph(
                        f"<b>{payment_data.get('currency', 'GBP').upper()} {payment_data.get('amount', 0) / 100:.2f}</b>",
                        ParagraphStyle("Bold", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=12),
                    ),
                ],
            ]
            total_table = Table(total_data, colWidths=[4.5 * inch, 1 * inch, 1.5 * inch])
            total_table.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                        ("FONTNAME", (2, 2), (2, 2), "Helvetica-Bold"),
                        ("FONTSIZE", (2, 2), (2, 2), 12),
                        ("BACKGROUND", (0, 2), (-1, 2), colors.lightgrey),
                    ]
                )
            )
            elements.append(total_table)
            elements.append(Spacer(1, 0.4 * inch))

            # Footer
            footer_data = [
                [
                    Paragraph(
                        f"<b>Transaction ID:</b> {payment_data.get('payoneer_order_id', 'N/A')}",
                        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=9),
                    )
                ]
            ]
            footer_table = Table(footer_data)
            footer_table.setStyle(TableStyle([("ALIGN", (0, 0), (0, 0), "CENTER")]))
            elements.append(footer_table)
            elements.append(Spacer(1, 0.2 * inch))

            # Notes
            elements.append(
                Paragraph(
                    f"<i>Thank you for your purchase! If you have any questions, please contact us at {self.company_email}</i>",
                    ParagraphStyle("Footer", parent=styles["Normal"], fontSize=9, alignment=TA_CENTER),
                )
            )

            # Build PDF
            doc.build(elements)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Failed to generate invoice: {str(e)}")
            return None

    def save_invoice(self, payment_data: dict, user_data: dict, output_path: str) -> bool:
        """Save invoice PDF to file"""
        try:
            pdf_bytes = self.generate_payment_invoice(payment_data, user_data)
            if pdf_bytes:
                with open(output_path, "wb") as f:
                    f.write(pdf_bytes)
                logger.info(f"Invoice saved to {output_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to save invoice: {str(e)}")
            return False
