"""
Script to generate synthetic multi-page invoice PDFs for testing.
Run this from the backend directory.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def create_multipage_invoice(output_path: str | Path) -> None:
    """Create a 2-page synthetic invoice PDF."""
    output_path = Path(output_path)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.darkblue,
    )
    header_style = ParagraphStyle(
        "Header",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=12,
    )
    normal_style = styles["Normal"]

    elements = []

    # ============ PAGE 1 ============
    # Header
    elements.append(Paragraph("INVOICE", title_style))
    elements.append(Spacer(1, 0.25 * inch))

    # Company Info
    company_info = """
    <b>TechCorp Solutions Inc.</b><br/>
    123 Innovation Drive, Suite 500<br/>
    San Francisco, CA 94105<br/>
    Phone: (415) 555-0199<br/>
    Email: billing@techcorp.com
    """
    elements.append(Paragraph(company_info, normal_style))
    elements.append(Spacer(1, 0.3 * inch))

    # Invoice Details
    invoice_details = [
        ["Invoice Number:", "INV-2024-0892"],
        ["Invoice Date:", "2024-03-15"],
        ["Due Date:", "2024-04-15"],
        ["Payment Terms:", "Net 30"],
    ]
    invoice_table = Table(invoice_details, colWidths=[2 * inch, 3 * inch])
    invoice_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(invoice_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Bill To
    elements.append(Paragraph("Bill To:", header_style))
    bill_to = """
    <b>Acme Corporation</b><br/>
    456 Business Park Way<br/>
    New York, NY 10001<br/>
    Attn: Accounts Payable
    """
    elements.append(Paragraph(bill_to, normal_style))
    elements.append(Spacer(1, 0.4 * inch))

    # Line Items - Page 1
    elements.append(Paragraph("Items (Page 1 of 2)", header_style))

    items_data = [
        ["Description", "Qty", "Unit Price", "Amount"],
        ["Cloud Infrastructure Setup", "1", "$5,000.00", "$5,000.00"],
        ["API Development Services", "40", "$150.00", "$6,000.00"],
        ["Database Migration", "1", "$3,500.00", "$3,500.00"],
        ["Security Audit", "1", "$2,500.00", "$2,500.00"],
        ["Load Balancer Configuration", "2", "$750.00", "$1,500.00"],
        ["SSL Certificate Setup", "3", "$200.00", "$600.00"],
        ["DNS Configuration", "1", "$350.00", "$350.00"],
        ["Monitoring Setup", "1", "$1,200.00", "$1,200.00"],
    ]

    items_table = Table(
        items_data, colWidths=[3.5 * inch, 0.75 * inch, 1.25 * inch, 1.25 * inch]
    )
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]
        )
    )
    elements.append(items_table)
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("<i>Continued on next page...</i>", normal_style))

    # Page break
    elements.append(PageBreak())

    # ============ PAGE 2 ============
    elements.append(Paragraph("INVOICE (Continued)", title_style))
    elements.append(Paragraph("Invoice #: INV-2024-0892", normal_style))
    elements.append(Spacer(1, 0.3 * inch))

    # More Line Items - Page 2
    elements.append(Paragraph("Items (Page 2 of 2)", header_style))

    items_data_p2 = [
        ["Description", "Qty", "Unit Price", "Amount"],
        ["Performance Optimization", "1", "$2,800.00", "$2,800.00"],
        ["Technical Documentation", "1", "$1,500.00", "$1,500.00"],
        ["Training Sessions (2hr)", "4", "$400.00", "$1,600.00"],
        ["24/7 Support (Monthly)", "3", "$800.00", "$2,400.00"],
        ["Backup System Setup", "1", "$1,850.00", "$1,850.00"],
    ]

    items_table_p2 = Table(
        items_data_p2, colWidths=[3.5 * inch, 0.75 * inch, 1.25 * inch, 1.25 * inch]
    )
    items_table_p2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]
        )
    )
    elements.append(items_table_p2)
    elements.append(Spacer(1, 0.5 * inch))

    # Summary
    elements.append(Paragraph("Invoice Summary", header_style))

    summary_data = [
        ["Subtotal:", "$30,800.00"],
        ["Tax (8.5%):", "$2,618.00"],
        ["Shipping:", "$0.00"],
        ["", ""],
        ["TOTAL DUE:", "$33,418.00"],
    ]

    summary_table = Table(summary_data, colWidths=[5 * inch, 1.75 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, -1), (-1, -1), 14),
                ("TEXTCOLOR", (0, -1), (-1, -1), colors.darkblue),
                ("LINEABOVE", (0, -1), (-1, -1), 2, colors.darkblue),
                ("TOPPADDING", (0, -1), (-1, -1), 12),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5 * inch))

    # Payment Info
    elements.append(Paragraph("Payment Information", header_style))
    payment_info = """
    <b>Bank Transfer:</b><br/>
    Bank: First National Bank<br/>
    Account Name: TechCorp Solutions Inc.<br/>
    Account Number: 1234567890<br/>
    Routing Number: 021000021<br/><br/>
    <b>Credit Card:</b> Visa, MasterCard, American Express accepted<br/>
    <b>Online Payment:</b> https://pay.techcorp.com/INV-2024-0892
    """
    elements.append(Paragraph(payment_info, normal_style))
    elements.append(Spacer(1, 0.4 * inch))

    # Footer
    footer = """
    <i>Thank you for your business!</i><br/>
    Questions? Contact billing@techcorp.com or call (415) 555-0199
    """
    elements.append(Paragraph(footer, normal_style))

    # Build PDF
    doc.build(elements)
    print(f"Created: {output_path}")


def create_simple_invoice(output_path: str | Path) -> None:
    """Create a simple 1-page invoice PDF."""
    output_path = Path(output_path)
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("INVOICE", styles["Title"]))
    elements.append(Spacer(1, 0.5 * inch))

    info = """
    <b>From:</b> Quick Services LLC<br/>
    <b>Invoice #:</b> QS-2024-001<br/>
    <b>Date:</b> 2024-02-20<br/>
    <b>Due Date:</b> 2024-03-20<br/><br/>
    <b>Bill To:</b> Sample Customer Inc.<br/>
    """
    elements.append(Paragraph(info, styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))

    data = [
        ["Item", "Quantity", "Price", "Total"],
        ["Consulting Services", "10 hrs", "$100.00", "$1,000.00"],
        ["Software License", "1", "$500.00", "$500.00"],
        ["Support Package", "1", "$250.00", "$250.00"],
        ["", "", "Subtotal:", "$1,750.00"],
        ["", "", "Tax (7%):", "$122.50"],
        ["", "", "TOTAL:", "$1,872.50"],
    ]

    table = Table(data, colWidths=[3 * inch, 1 * inch, 1.25 * inch, 1.25 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, 3), 0.5, colors.black),
                ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(
        Paragraph("Payment due within 30 days. Thank you!", styles["Normal"])
    )

    doc.build(elements)
    print(f"Created: {output_path}")


if __name__ == "__main__":
    samples_dir = Path(__file__).parent.parent.parent / "samples"
    samples_dir.mkdir(exist_ok=True)

    # Create multi-page invoice
    create_multipage_invoice(samples_dir / "sample_multipage_invoice.pdf")

    # Create simple invoice
    create_simple_invoice(samples_dir / "sample_simple_invoice.pdf")

    print("\nSynthetic test PDFs created successfully!")
