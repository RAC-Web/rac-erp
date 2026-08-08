from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

def generate_leave_pdf(leave_request):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(200, height - 60, "Rahman Anis & Co.")
    c.setFont("Helvetica", 14)
    c.drawString(220, height - 85, "Leave Application Form")
    
    c.line(50, height - 100, width - 50, height - 100)

    # Details
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 130, "Student Details")
    
    c.setFont("Helvetica", 11)
    y = height - 150
    c.drawString(50, y, f"Name: {leave_request.student.full_name}")
    c.drawString(300, y, f"Student ID: {leave_request.student.student_id}")
    y -= 20
    c.drawString(50, y, f"Department: {leave_request.student.department}")
    c.drawString(300, y, f"Designation: {leave_request.student.designation}")
    
    y -= 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Leave Details")
    c.setFont("Helvetica", 11)
    y -= 20
    c.drawString(50, y, f"Leave Type: {leave_request.leave_type.name}")
    y -= 20
    c.drawString(50, y, f"Start Date: {leave_request.start_date.strftime('%d-%b-%Y')}")
    c.drawString(300, y, f"End Date: {leave_request.end_date.strftime('%d-%b-%Y')}")
    y -= 20
    c.drawString(50, y, f"Total Days: {leave_request.total_days}")
    y -= 20
    c.drawString(50, y, "Reason:")
    y -= 15
    c.setFont("Helvetica-Oblique", 11)
    
    # Handle long reason (simple split by length)
    reason_text = leave_request.reason
    chars_per_line = 80
    for i in range(0, len(reason_text), chars_per_line):
        c.drawString(70, y, reason_text[i:i+chars_per_line])
        y -= 15
    
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Approval Status")
    c.setFont("Helvetica", 11)
    y -= 20
    c.drawString(50, y, f"Current Status: {leave_request.status}")

    # Signatures
    y = 120
    c.line(50, y, 180, y)
    c.drawString(60, y - 15, "Student Signature")
    
    c.line(220, y, 360, y)
    c.drawString(240, y - 15, "Manager Signature")
    
    c.line(410, y, 560, y)
    c.drawString(420, y - 15, "Principal Signature")

    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer
