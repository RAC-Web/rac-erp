from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Sum, Q
from apps.attendance.models import Attendance
from apps.leave.models import LeaveRequest
from apps.practice.models import Client, Assignment, WorkType
from apps.students.models import StudentProfile
from apps.payroll.models import PayrollRecord
from apps.conveyance.models import Conveyance

@login_required
def dashboard(request):
    context = {}
    today = timezone.now().date()
    current_month = today.replace(day=1)
    role = getattr(request.user, 'role', '')

    if role == 'Student':
        student_profile = getattr(request.user, 'student_profile', None)
        if student_profile:
            attendance = Attendance.objects.filter(student=student_profile, date=today).first()
            context['attendance_today'] = attendance

            # Student KPIs
            month_attendance = Attendance.objects.filter(student=student_profile, date__gte=current_month)
            context['days_present'] = month_attendance.filter(status='Present').count()
            context['days_late'] = month_attendance.filter(status='Late').count()
            context['days_absent'] = month_attendance.filter(status='Absent').count()
            context['pending_leaves'] = LeaveRequest.objects.filter(student=student_profile, status='Pending').count()

            context['clients'] = Client.objects.filter(status='Active')
            context['assignments'] = Assignment.objects.exclude(status='Completed')
            context['work_types'] = WorkType.objects.all()

    elif role in ('Principal', 'Manager'):
        # Manager/Principal KPIs
        context['total_students'] = StudentProfile.objects.count()
        context['present_today'] = Attendance.objects.filter(date=today, status='Present').count()
        context['absent_today'] = context['total_students'] - context['present_today']
        context['pending_leaves'] = LeaveRequest.objects.filter(status='Pending').count()
        context['pending_conveyances'] = Conveyance.objects.filter(status='Pending').count()
        context['active_assignments'] = Assignment.objects.filter(status='In Progress').count()
        context['active_clients'] = Client.objects.filter(status='Active').count()

        # Recent activity
        context['recent_attendance'] = Attendance.objects.filter(date=today).select_related('student').order_by('-time_in')[:10]
        context['recent_leaves'] = LeaveRequest.objects.order_by('-applied_on')[:5]

    return render(request, 'core/dashboard.html', context)
