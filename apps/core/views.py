from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.attendance.models import Attendance
from apps.practice.models import Client, Assignment, WorkType
from django.utils import timezone

@login_required
def dashboard(request):
    context = {}
    if getattr(request.user, 'role', '') == 'Student':
        student_profile = getattr(request.user, 'student_profile', None)
        if student_profile:
            today = timezone.now().date()
            attendance = Attendance.objects.filter(student=student_profile, date=today).first()
            context['attendance_today'] = attendance
            
            context['clients'] = Client.objects.filter(status='Active')
            context['assignments'] = Assignment.objects.exclude(status='Completed')
            context['work_types'] = WorkType.objects.all()

    return render(request, 'core/dashboard.html', context)
