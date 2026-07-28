import subprocess
import sys

def install_and_generate():
    # Install reportlab
    print("Installing reportlab for PDF generation...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    
    pdf_path = "Complaint.pdf"
    print(f"Generating {pdf_path}...")
    
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    # Write Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 80, "PHARMACEUTICAL PRODUCT COMPLAINT REPORT")
    
    # Draw line
    c.setLineWidth(1)
    c.line(50, height - 90, width - 50, height - 90)
    
    # Write Letter Content
    c.setFont("Helvetica", 11)
    
    content = [
        "Date: July 28, 2026",
        "To: Quality Assurance Team / QMS Department",
        "From: XYZ Pharmacy, Retail Operations Manager",
        "Subject: Urgent Product Quality Issue Notification",
        "",
        "Dear QA Team,",
        "",
        "Our pharmacy has received a shipment of Amoxicillin Capsules 250 mg.",
        "",
        "Product Details:",
        "----------------",
        "Product Name: Amoxicillin Capsules",
        "Strength: 250 mg",
        "Batch Number: AMX1032",
        "Manufactured: Feb 2026",
        "Expiry Date: Jan 2028",
        "Quantity Affected: 150 boxes",
        "",
        "Problem Description:",
        "--------------------",
        "Approximately 150 boxes of the delivered batch have broken capsules.",
        "A large portion of the capsules are split open, and loose powder is scattered",
        "inside the primary blister packages. This represents a significant product defect,",
        "and we cannot dispense these items to our patients.",
        "",
        "Please register this complaint inside your QMS system, trigger a QA investigation,",
        "and process a replacement shipment for our inventory as soon as possible.",
        "",
        "Regards,",
        "XYZ Pharmacy",
        "Quality Operations Division"
    ]
    
    y = height - 120
    for line in content:
        c.drawString(50, y, line)
        y -= 18
        
    c.save()
    print(f"Successfully generated {pdf_path}!")

if __name__ == "__main__":
    install_and_generate()
