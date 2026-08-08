from django.utils import timezone
from apps.attendance.models import Attendance
from apps.practice.models import Client, Assignment, WorkType

def global_attendance_context(request):
    context = {}
    if request.user.is_authenticated and getattr(request.user, 'role', '') == 'Student':
        student_profile = getattr(request.user, 'student_profile', None)
        if student_profile:
            today = timezone.now().date()
            attendance = Attendance.objects.filter(student=student_profile, date=today).first()
            context['attendance_today_global'] = attendance
            if not attendance:
                context['clients_global'] = Client.objects.filter(status='Active')
                context['assignments_global'] = Assignment.objects.exclude(status='Completed')
                context['work_types_global'] = WorkType.objects.all()

    if request.user.is_authenticated:
        from apps.core.models import Notification
        unread = Notification.objects.filter(user=request.user, is_read=False)
        context['unread_notifications'] = unread[:5]
        context['unread_count'] = unread.count()
        
    return context
