from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import PayrollRecord
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

@login_required
def payroll_list(request):
    if getattr(request.user, 'role', '') == 'Student':
        payrolls = PayrollRecord.objects.filter(student=request.user.student_profile).order_by('-month')
    else:
        payrolls = PayrollRecord.objects.all().order_by('-month')
    return render(request, 'payroll/list.html', {'payrolls': payrolls})

@login_required
def generate_payslip_pdf(request, pk):
    payroll = get_object_or_404(PayrollRecord, pk=pk)
    
    if getattr(request.user, 'role', '') == 'Student' and payroll.student != request.user.student_profile:
        return HttpResponse("Unauthorized", status=403)
        
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Draw PDF
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "Rahman Anis & Co., Chartered Accountants")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, 720, f"Payslip for {payroll.month.strftime('%B %Y')}")
    
    p.drawString(100, 680, f"Name: {payroll.student.full_name}")
    p.drawString(100, 660, f"Status: {payroll.status}")
    
    p.drawString(100, 620, "Earnings:")
    p.drawString(120, 600, f"Base Stipend: BDT {payroll.base_stipend}")
    p.drawString(120, 580, f"Conveyance Allowance: BDT {payroll.conveyance_allowance}")
    p.drawString(120, 560, f"Bonus: BDT {payroll.bonus}")
    
    p.drawString(100, 520, "Deductions:")
    p.drawString(120, 500, f"Late Deductions: BDT {payroll.late_deduction}")
    p.drawString(120, 480, f"Leave Deductions: BDT {payroll.leave_deduction}")
    p.drawString(120, 460, f"Other Deductions: BDT {payroll.other_deduction}")
    
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, 420, f"Net Pay: BDT {payroll.net_pay}")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="payslip_{payroll.month.strftime("%Y_%m")}.pdf"'
    
    return response
