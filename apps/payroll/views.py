from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse
from .models import PayrollRecord, DailyPayrollLog
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import calendar
import datetime

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


@login_required
def daily_detail(request, pk):
    """Shows day-by-day payroll breakdown for a specific PayrollRecord."""
    payroll = get_object_or_404(PayrollRecord, pk=pk)
    
    # Access control
    if getattr(request.user, 'role', '') == 'Student' and payroll.student != request.user.student_profile:
        return HttpResponse("Unauthorized", status=403)
    
    # Get month date range
    year = payroll.month.year
    month = payroll.month.month
    _, num_days = calendar.monthrange(year, month)
    start_date = datetime.date(year, month, 1)
    end_date = datetime.date(year, month, num_days)
    
    # Get daily logs
    daily_logs = DailyPayrollLog.objects.filter(
        student=payroll.student,
        date__range=[start_date, end_date]
    ).order_by('date')
    
    # Summary stats
    total_present = daily_logs.filter(attendance_status='Present').count()
    total_late = daily_logs.filter(attendance_status='Late').count()
    total_absent = daily_logs.filter(attendance_status='Absent').count()
    total_leave = daily_logs.filter(attendance_status='Leave').count()
    total_holiday = daily_logs.filter(attendance_status__in=['Holiday', 'Weekend']).count()
    total_sandwich = daily_logs.filter(attendance_status='Sandwich').count()
    
    context = {
        'payroll': payroll,
        'daily_logs': daily_logs,
        'total_present': total_present,
        'total_late': total_late,
        'total_absent': total_absent,
        'total_leave': total_leave,
        'total_holiday': total_holiday,
        'total_sandwich': total_sandwich,
        'total_days_processed': daily_logs.count(),
        'total_days_in_month': num_days,
    }
    
    return render(request, 'payroll/daily_detail.html', context)


@login_required
def auto_generate_payroll_view(request):
    """Allows managers to trigger daily payroll generation from UI."""
    if request.user.role not in ['Manager', 'Principal']:
        return redirect('payroll:list')
    
    if request.method == 'POST':
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        backfill = request.POST.get('backfill', '') == 'on'
        target_date = request.POST.get('target_date', '')
        
        cmd_kwargs = {}
        if target_date:
            cmd_kwargs['date'] = target_date
        if backfill:
            cmd_kwargs['backfill'] = True
        
        call_command('auto_generate_payroll', stdout=out, **cmd_kwargs)
        
        output = out.getvalue()
        messages.success(request, f'Daily payroll generation completed! {output}')
        return redirect('payroll:list')
    
    return render(request, 'payroll/auto_generate.html')
