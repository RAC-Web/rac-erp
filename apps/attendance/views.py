from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponse
from .models import Attendance

@login_required
def mark_attendance(request):
    if request.method == 'POST':
        student_profile = getattr(request.user, 'student_profile', None)
        if not student_profile:
            return HttpResponse("<div class='alert alert-danger'>Only students can mark attendance.</div>")
        
        today = timezone.now().date()
        current_time = timezone.now().time()
        
        attendance, created = Attendance.objects.get_or_create(
            student=student_profile,
            date=today,
            defaults={'time_in': current_time, 'status': 'Present'}
        )
        
        if not created and attendance.time_in and not attendance.time_out:
            attendance.time_out = current_time
            in_datetime = timezone.datetime.combine(today, attendance.time_in)
            out_datetime = timezone.datetime.combine(today, attendance.time_out)
            duration = out_datetime - in_datetime
            attendance.working_hours = round(duration.total_seconds() / 3600, 2)
            attendance.save()
            return HttpResponse(f"<button class='btn btn-secondary btn-lg rounded-pill px-5 py-3 shadow mb-3 fw-bold' disabled>Marked OUT at {attendance.time_out.strftime('%I:%M %p')}</button>")
        elif created:
            return HttpResponse(f"<button class='btn btn-warning btn-lg rounded-pill px-5 py-3 shadow mb-3 fw-bold' hx-post='/attendance/mark/' hx-target='this' hx-swap='outerHTML'>Mark OUT Now</button>")
        else:
            return HttpResponse(f"<button class='btn btn-secondary btn-lg rounded-pill px-5 py-3 shadow mb-3 fw-bold' disabled>Already Marked OUT</button>")

    return HttpResponse("Invalid request.", status=400)
