"""Generate sample PDF files for testing."""

import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def create_invoice_1():
    """Create a simple invoice PDF."""
    filename = os.path.join(OUTPUT_DIR, "invoice_techcorp.pdf")
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        "Title", parent=styles["Heading1"], alignment=TA_CENTER, fontSize=24
    )
    story.append(Paragraph("INVOICE", title_style))
    story.append(Spacer(1, 0.3 * inch))

    # Company Info
    story.append(Paragraph("<b>TechCorp Solutions Inc.</b>", styles["Normal"]))
    story.append(Paragraph("123 Innovation Drive", styles["Normal"]))
    story.append(Paragraph("San Francisco, CA 94102", styles["Normal"]))
    story.append(Paragraph("Phone: (415) 555-0123", styles["Normal"]))
    story.append(Paragraph("Email: billing@techcorp.com", styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    # Invoice Details
    story.append(Paragraph("<b>Invoice Number:</b> INV-2024-0042", styles["Normal"]))
    story.append(Paragraph("<b>Invoice Date:</b> January 10, 2024", styles["Normal"]))
    story.append(Paragraph("<b>Due Date:</b> February 10, 2024", styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    # Bill To
    story.append(Paragraph("<b>Bill To:</b>", styles["Heading3"]))
    story.append(Paragraph("Acme Corporation", styles["Normal"]))
    story.append(Paragraph("456 Business Blvd", styles["Normal"]))
    story.append(Paragraph("New York, NY 10001", styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    # Items Table
    data = [
        ["Description", "Quantity", "Unit Price", "Total"],
        ["Cloud Hosting - Monthly", "1", "$299.00", "$299.00"],
        ["API Access - Premium Tier", "1", "$149.00", "$149.00"],
        ["Technical Support - 10 hours", "10", "$75.00", "$750.00"],
        ["Data Storage - 500GB", "1", "$50.00", "$50.00"],
    ]

    table = Table(data, colWidths=[3 * inch, 1 * inch, 1.2 * inch, 1.2 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.3 * inch))

    # Totals
    right_style = ParagraphStyle("Right", parent=styles["Normal"], alignment=TA_RIGHT)
    story.append(Paragraph("<b>Subtotal:</b> $1,248.00", right_style))
    story.append(Paragraph("<b>Tax (8.5%):</b> $106.08", right_style))
    story.append(Paragraph("<b>Total Due:</b> $1,354.08", right_style))

    doc.build(story)
    print(f"Created: {filename}")


def create_invoice_2():
    """Create another invoice PDF."""
    filename = os.path.join(OUTPUT_DIR, "invoice_designstudio.pdf")
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        "Title", parent=styles["Heading1"], alignment=TA_CENTER, fontSize=24
    )
    story.append(Paragraph("INVOICE", title_style))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("<b>Creative Design Studio LLC</b>", styles["Normal"]))
    story.append(Paragraph("789 Artisan Way, Suite 200", styles["Normal"]))
    story.append(Paragraph("Los Angeles, CA 90012", styles["Normal"]))
    story.append(Paragraph("Phone: (323) 555-7890", styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("<b>Invoice #:</b> DS-2024-115", styles["Normal"]))
    story.append(Paragraph("<b>Date:</b> January 5, 2024", styles["Normal"]))
    story.append(Paragraph("<b>Payment Terms:</b> Net 30", styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("<b>Client:</b>", styles["Heading3"]))
    story.append(Paragraph("StartupXYZ Inc.", styles["Normal"]))
    story.append(Paragraph("Contact: Sarah Johnson", styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    data = [
        ["Service", "Hours", "Rate", "Amount"],
        ["Logo Design & Branding", "20", "$150/hr", "$3,000.00"],
        ["Website UI/UX Design", "35", "$125/hr", "$4,375.00"],
        ["Marketing Collateral", "15", "$100/hr", "$1,500.00"],
    ]

    table = Table(data, colWidths=[3 * inch, 1 * inch, 1.2 * inch, 1.2 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.3 * inch))

    right_style = ParagraphStyle("Right", parent=styles["Normal"], alignment=TA_RIGHT)
    story.append(Paragraph("<b>Subtotal:</b> $8,875.00", right_style))
    story.append(Paragraph("<b>Tax (9.5%):</b> $843.13", right_style))
    story.append(Paragraph("<b>Total:</b> $9,718.13 USD", right_style))

    doc.build(story)
    print(f"Created: {filename}")


def create_resume_1():
    """Create a senior developer resume."""
    filename = os.path.join(OUTPUT_DIR, "resume_john_developer.pdf")
    doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    story = []

    # Name
    name_style = ParagraphStyle(
        "Name", parent=styles["Heading1"], alignment=TA_CENTER, fontSize=22
    )
    story.append(Paragraph("JOHN ANDERSON", name_style))

    contact_style = ParagraphStyle(
        "Contact", parent=styles["Normal"], alignment=TA_CENTER
    )
    story.append(Paragraph("Senior Software Engineer", contact_style))
    story.append(
        Paragraph(
            "john.anderson@email.com | (555) 123-4567 | San Francisco, CA",
            contact_style,
        )
    )
    story.append(
        Paragraph(
            "LinkedIn: linkedin.com/in/johnanderson | GitHub: github.com/janderson",
            contact_style,
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    # Summary
    story.append(Paragraph("<b>PROFESSIONAL SUMMARY</b>", styles["Heading2"]))
    story.append(
        Paragraph(
            "Results-driven Senior Software Engineer with 8+ years of experience designing and implementing "
            "scalable applications. Expert in Python, JavaScript, and cloud technologies (AWS, GCP). "
            "Proven track record of leading teams, improving system performance by 40%, and delivering "
            "high-impact projects on time.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    # Skills
    story.append(Paragraph("<b>TECHNICAL SKILLS</b>", styles["Heading2"]))
    story.append(
        Paragraph(
            "<b>Languages:</b> Python, JavaScript/TypeScript, Go, SQL, Java",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "<b>Frameworks:</b> React, Node.js, FastAPI, Django, Flask",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "<b>Cloud & DevOps:</b> AWS (EC2, Lambda, S3, RDS), Docker, Kubernetes, Terraform, CI/CD",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "<b>Databases:</b> PostgreSQL, MongoDB, Redis, Elasticsearch",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    # Experience
    story.append(Paragraph("<b>WORK EXPERIENCE</b>", styles["Heading2"]))

    story.append(
        Paragraph(
            "<b>Senior Software Engineer</b> | TechGiant Inc. | Jan 2021 - Present",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Led a team of 5 engineers to build a real-time analytics platform serving 10M+ users",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Architected microservices migration reducing infrastructure costs by 35%",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Implemented CI/CD pipelines cutting deployment time from 2 hours to 15 minutes",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "<b>Software Engineer</b> | DataFlow Systems | Mar 2018 - Dec 2020",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Developed RESTful APIs handling 1M+ daily requests with 99.9% uptime",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Built machine learning pipeline for fraud detection (95% accuracy)",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Mentored 3 junior developers, conducted code reviews", styles["Normal"]
        )
    )
    story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "<b>Junior Developer</b> | StartupHub | Jun 2016 - Feb 2018",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Built customer-facing web applications using React and Node.js",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Optimized database queries improving response time by 60%",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    # Education
    story.append(Paragraph("<b>EDUCATION</b>", styles["Heading2"]))
    story.append(
        Paragraph(
            "<b>B.S. Computer Science</b> | Stanford University | 2016",
            styles["Normal"],
        )
    )
    story.append(Paragraph("GPA: 3.8/4.0 | Dean's List", styles["Normal"]))
    story.append(Spacer(1, 0.15 * inch))

    # Certifications
    story.append(Paragraph("<b>CERTIFICATIONS</b>", styles["Heading2"]))
    story.append(
        Paragraph("• AWS Solutions Architect Professional (2023)", styles["Normal"])
    )
    story.append(Paragraph("• Kubernetes Administrator (CKA) (2022)", styles["Normal"]))

    doc.build(story)
    print(f"Created: {filename}")


def create_resume_2():
    """Create a data scientist resume."""
    filename = os.path.join(OUTPUT_DIR, "resume_sarah_datascientist.pdf")
    doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    story = []

    name_style = ParagraphStyle(
        "Name", parent=styles["Heading1"], alignment=TA_CENTER, fontSize=22
    )
    story.append(Paragraph("SARAH CHEN", name_style))

    contact_style = ParagraphStyle(
        "Contact", parent=styles["Normal"], alignment=TA_CENTER
    )
    story.append(Paragraph("Data Scientist", contact_style))
    story.append(
        Paragraph("sarah.chen@email.com | (555) 987-6543 | Seattle, WA", contact_style)
    )
    story.append(Paragraph("LinkedIn: linkedin.com/in/sarahchen", contact_style))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>SUMMARY</b>", styles["Heading2"]))
    story.append(
        Paragraph(
            "Data Scientist with 5 years of experience in machine learning, statistical analysis, and "
            "data engineering. Skilled in building predictive models that drive business decisions. "
            "Published researcher with expertise in NLP and computer vision.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>SKILLS</b>", styles["Heading2"]))
    story.append(
        Paragraph(
            "<b>ML/AI:</b> TensorFlow, PyTorch, Scikit-learn, XGBoost, NLP, Computer Vision",
            styles["Normal"],
        )
    )
    story.append(Paragraph("<b>Languages:</b> Python, R, SQL, Scala", styles["Normal"]))
    story.append(
        Paragraph(
            "<b>Tools:</b> Pandas, NumPy, Spark, Airflow, MLflow, Jupyter",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "<b>Cloud:</b> AWS SageMaker, GCP Vertex AI, Azure ML", styles["Normal"]
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>EXPERIENCE</b>", styles["Heading2"]))

    story.append(
        Paragraph(
            "<b>Senior Data Scientist</b> | AI Innovations Corp | Apr 2022 - Present",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Built recommendation engine increasing user engagement by 25%",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Developed NLP models for sentiment analysis processing 5M+ reviews/day",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Led A/B testing framework used across 15 product teams", styles["Normal"]
        )
    )
    story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(
            "<b>Data Scientist</b> | RetailTech Solutions | Jul 2019 - Mar 2022",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Created demand forecasting models saving $2M annually in inventory costs",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Built customer churn prediction model with 92% accuracy",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Designed ETL pipelines processing 10TB of daily data", styles["Normal"]
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>EDUCATION</b>", styles["Heading2"]))
    story.append(
        Paragraph(
            "<b>M.S. Data Science</b> | University of Washington | 2019",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph("<b>B.S. Statistics</b> | UC Berkeley | 2017", styles["Normal"])
    )
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("<b>PUBLICATIONS</b>", styles["Heading2"]))
    story.append(
        Paragraph(
            "• 'Efficient Transformer Architectures for NLP' - EMNLP 2023",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• 'Time-Series Forecasting with Deep Learning' - KDD 2022",
            styles["Normal"],
        )
    )

    doc.build(story)
    print(f"Created: {filename}")


def create_resume_3():
    """Create a fresh graduate resume."""
    filename = os.path.join(OUTPUT_DIR, "resume_mike_graduate.pdf")
    doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    story = []

    name_style = ParagraphStyle(
        "Name", parent=styles["Heading1"], alignment=TA_CENTER, fontSize=22
    )
    story.append(Paragraph("MICHAEL TORRES", name_style))

    contact_style = ParagraphStyle(
        "Contact", parent=styles["Normal"], alignment=TA_CENTER
    )
    story.append(Paragraph("Junior Software Developer", contact_style))
    story.append(
        Paragraph("mike.torres@email.com | (555) 456-7890 | Austin, TX", contact_style)
    )
    story.append(Paragraph("GitHub: github.com/miketorres", contact_style))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>OBJECTIVE</b>", styles["Heading2"]))
    story.append(
        Paragraph(
            "Recent Computer Science graduate seeking an entry-level software development position. "
            "Passionate about web development and eager to contribute to innovative projects while "
            "learning from experienced team members.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>EDUCATION</b>", styles["Heading2"]))
    story.append(
        Paragraph(
            "<b>B.S. Computer Science</b> | University of Texas at Austin | May 2024",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "GPA: 3.5/4.0 | Relevant Coursework: Data Structures, Algorithms, Web Development, Databases",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>SKILLS</b>", styles["Heading2"]))
    story.append(
        Paragraph(
            "<b>Languages:</b> Python, JavaScript, Java, HTML/CSS", styles["Normal"]
        )
    )
    story.append(
        Paragraph("<b>Frameworks:</b> React, Node.js, Express", styles["Normal"])
    )
    story.append(
        Paragraph("<b>Tools:</b> Git, VS Code, MySQL, MongoDB", styles["Normal"])
    )
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>PROJECTS</b>", styles["Heading2"]))
    story.append(
        Paragraph("<b>E-Commerce Platform</b> (Capstone Project)", styles["Normal"])
    )
    story.append(
        Paragraph(
            "• Built full-stack shopping app with React frontend and Node.js backend",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Implemented user authentication, shopping cart, and payment integration",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    story.append(
        Paragraph("<b>Task Management App</b> (Personal Project)", styles["Normal"])
    )
    story.append(
        Paragraph(
            "• Created responsive web app using React and Firebase", styles["Normal"]
        )
    )
    story.append(
        Paragraph(
            "• Features include drag-and-drop, real-time sync, user collaboration",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>INTERNSHIP</b>", styles["Heading2"]))
    story.append(
        Paragraph(
            "<b>Software Development Intern</b> | LocalTech Startup | Summer 2023",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Developed features for customer dashboard using React", styles["Normal"]
        )
    )
    story.append(
        Paragraph(
            "• Wrote unit tests improving code coverage from 60% to 85%",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "• Participated in daily standups and sprint planning", styles["Normal"]
        )
    )

    doc.build(story)
    print(f"Created: {filename}")


def create_job_description():
    """Create a sample job description text file."""
    filename = os.path.join(OUTPUT_DIR, "job_description_senior_developer.txt")
    content = """SENIOR SOFTWARE ENGINEER

Company: TechVentures Inc.
Location: San Francisco, CA (Hybrid)
Salary: $150,000 - $200,000

About Us:
TechVentures is a fast-growing startup building next-generation cloud infrastructure. We're looking for a Senior Software Engineer to join our Platform team.

Requirements:
- 5+ years of software development experience
- Strong proficiency in Python and/or Go
- Experience with cloud platforms (AWS, GCP, or Azure)
- Hands-on experience with Kubernetes and Docker
- Familiarity with microservices architecture
- Experience with CI/CD pipelines
- Strong understanding of databases (PostgreSQL, Redis)
- Excellent communication and teamwork skills

Nice to Have:
- Experience with Terraform or similar IaC tools
- Knowledge of machine learning/AI systems
- Open source contributions
- Experience leading or mentoring developers

Responsibilities:
- Design and implement scalable backend services
- Lead technical initiatives and architectural decisions
- Mentor junior engineers and conduct code reviews
- Collaborate with product and design teams
- Participate in on-call rotation
- Contribute to engineering best practices

Benefits:
- Competitive equity package
- Health, dental, vision insurance
- 401(k) matching
- Unlimited PTO
- Remote-friendly culture
"""
    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename}")


if __name__ == "__main__":
    print("Generating sample PDFs...")
    create_invoice_1()
    create_invoice_2()
    create_resume_1()
    create_resume_2()
    create_resume_3()
    create_job_description()
    print("\nDone! All sample files created in:", OUTPUT_DIR)
