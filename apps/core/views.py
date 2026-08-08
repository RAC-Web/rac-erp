import json
from datetime import timedelta
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
from apps.attendance.utils import get_working_days, is_working_day
from apps.core.models import Notification
from django.shortcuts import redirect
import datetime

@login_required
def dashboard(request):
    context = {}
    today = timezone.now().date()
    current_month = today.replace(day=1)
    role = getattr(request.user, 'role', '')

    popup = Notification.objects.filter(user=request.user, is_popup=True, popup_seen=False).first()
    context['popup_notification'] = popup

    if role == 'Student':
        student_profile = getattr(request.user, 'student_profile', None)
        if student_profile:
            # AUTO-CHECKOUT LOGIC: Close any previous unclosed attendances
            unclosed = Attendance.objects.filter(
                student=student_profile,
                date__lt=today,
                time_out__isnull=True
            )
            for att in unclosed:
                att.time_out = datetime.time(23, 59)
                att.save()
                Notification.objects.create(
                    user=request.user,
                    message=f"Warning: You forgot to Mark OUT on {att.date}. You were automatically checked out at 11:59 PM."
                )

            attendance = Attendance.objects.filter(student=student_profile, date=today).first()
            context['attendance_today'] = attendance

            # Student KPIs
            month_attendance = Attendance.objects.filter(student=student_profile, date__gte=current_month)
            days_present_late = month_attendance.filter(status__in=['Present', 'Late']).count()
            
            working_days = get_working_days(current_month, today)
            
            # Calculate leave days taken within the working days range
            leaves = LeaveRequest.objects.filter(
                student=student_profile,
                status__in=['Manager Approved', 'Principal Approved'],
                start_date__lte=today,
                end_date__gte=current_month
            )
            leave_days = 0
            for l in leaves:
                d = max(l.start_date, current_month)
                end_d = min(l.end_date, today)
                while d <= end_d:
                    if d in working_days:
                        leave_days += 1
                    d += timedelta(days=1)
                    
            days_absent = len(working_days) - days_present_late - leave_days
            if days_absent < 0:
                days_absent = 0
                
            context['days_present'] = days_present_late
            context['days_late'] = month_attendance.filter(status='Late').count()
            context['days_absent'] = days_absent
            
            context['pending_leaves'] = LeaveRequest.objects.filter(student=student_profile, status='Pending').count()

            context['clients'] = Client.objects.filter(status='Active')
            context['assignments'] = Assignment.objects.exclude(status='Completed')
            context['work_types'] = WorkType.objects.all()

    elif role in ('Principal', 'Manager'):
        # Manager/Principal KPIs
        context['total_students'] = StudentProfile.objects.count()
        context['present_today'] = Attendance.objects.filter(date=today, status__in=['Present', 'Late']).count()
        
        if is_working_day(today):
            leaves_today = LeaveRequest.objects.filter(
                status__in=['Manager Approved', 'Principal Approved'],
                start_date__lte=today,
                end_date__gte=today
            ).count()
            absent = context['total_students'] - context['present_today'] - leaves_today
            context['absent_today'] = max(absent, 0)
        else:
            context['absent_today'] = 0
            
        context['pending_leaves'] = LeaveRequest.objects.filter(status='Pending').count()
        context['pending_conveyances'] = Conveyance.objects.filter(status='Pending').count()
        context['active_assignments'] = Assignment.objects.filter(status='In Progress').count()
        context['active_clients'] = Client.objects.filter(status='Active').count()

        # Recent activity
        context['recent_attendance'] = Attendance.objects.filter(date=today).select_related('student').order_by('-time_in')[:10]
        context['recent_leaves'] = LeaveRequest.objects.order_by('-applied_on')[:5]

        # Chart Data: Leave Status Distribution
        leave_counts = list(LeaveRequest.objects.values('status').annotate(count=Count('id')))
        leave_labels = [item['status'] for item in leave_counts]
        leave_data = [item['count'] for item in leave_counts]
        context['leave_chart_labels'] = json.dumps(leave_labels)
        context['leave_chart_data'] = json.dumps(leave_data)

        # Chart Data: Last 7 Days Attendance Trend
        last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        attendance_trend = []
        for d in last_7_days:
            count = Attendance.objects.filter(date=d, status='Present').count()
            attendance_trend.append(count)
            
        context['attendance_trend_labels'] = json.dumps([d.strftime('%b %d') for d in last_7_days])
        context['attendance_trend_data'] = json.dumps(attendance_trend)

    return render(request, 'core/dashboard.html', context)

@login_required
def mark_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', '/'))

from django.http import JsonResponse
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib import messages

@login_required
def send_announcement(request):
    if request.user.role not in ['Manager', 'Principal']:
        return redirect('/')
        
    if request.method == 'POST':
        target = request.POST.get('target')
        message = request.POST.get('message')
        is_popup = request.POST.get('is_popup') == 'on'
        
        users_to_notify = []
        if target == 'all':
            users_to_notify = User.objects.all()
        elif target == 'students':
            users_to_notify = User.objects.filter(role='Student')
        elif target == 'managers':
            users_to_notify = User.objects.filter(role__in=['Manager', 'Principal'])
        elif target == 'specific':
            user_id = request.POST.get('specific_user')
            if user_id:
                users_to_notify = User.objects.filter(id=user_id)
                
        for u in users_to_notify:
            Notification.objects.create(
                user=u,
                message=message,
                is_popup=is_popup
            )
            
        messages.success(request, f"Announcement sent to {len(users_to_notify)} user(s).")
        return redirect('core:dashboard')
        
    # Get lists for the form
    students = User.objects.filter(role='Student')
    managers = User.objects.filter(role__in=['Manager', 'Principal'])
    return render(request, 'core/send_announcement.html', {
        'students': students,
        'managers': managers
    })

@login_required
def dismiss_popup(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_popup=True, popup_seen=False).update(popup_seen=True)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Invalid request'}, status=400)
