from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse
from .models import PayrollRecord
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['Manager', 'Principal']
    def handle_no_permission(self):
        return redirect('/')

class PayrollCreateView(ManagerRequiredMixin, CreateView):
    model = PayrollRecord
    fields = ['student', 'month', 'base_stipend', 'conveyance_allowance', 'bonus', 'late_deduction', 'leave_deduction', 'other_deduction', 'status']
    template_name = 'payroll/generate.html'
    success_url = reverse_lazy('payroll:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Generate Payroll'
        ctx['cancel_url'] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Payroll generated successfully.")
        return super().form_valid(form)

from django.views.generic import UpdateView

class PayrollUpdateView(ManagerRequiredMixin, UpdateView):
    model = PayrollRecord
    fields = ['base_stipend', 'conveyance_allowance', 'bonus', 'late_deduction', 'leave_deduction', 'other_deduction', 'status']
    template_name = 'payroll/edit.html'
    success_url = reverse_lazy('payroll:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Edit Payroll (Manual Override)'
        ctx['cancel_url'] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Payroll updated successfully.")
        return super().form_valid(form)

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

from django.http import JsonResponse
from apps.students.models import StudentProfile
import datetime
from .utils import calculate_payroll_deductions

@login_required
def calculate_deductions_api(request):
    if request.user.role not in ['Manager', 'Principal']:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    student_id = request.GET.get('student_id')
    month_str = request.GET.get('month') # expected format YYYY-MM-01
    
    if not student_id or not month_str:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
        
    try:
        student = StudentProfile.objects.get(id=student_id)
        month_date = datetime.datetime.strptime(month_str, '%Y-%m-%d').date()
    except (StudentProfile.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
        
    data = calculate_payroll_deductions(student, month_date)
    return JsonResponse(data)
