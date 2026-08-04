from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponse
from .models import Attendance
from apps.practice.models import Client, Assignment, WorkType, ClientVisit
from django.contrib import messages

@login_required
def mark_attendance(request):
    if request.method == 'POST':
        student_profile = getattr(request.user, 'student_profile', None)
        if not student_profile:
            messages.error(request, "Only students can mark attendance.")
            return redirect('/')
        
        today = timezone.now().date()
        current_time = timezone.now().time()
        
        attendance = Attendance.objects.filter(student=student_profile, date=today).first()
        
        if not attendance:
            # Mark IN
            location = request.POST.get('location', 'Office')
            attendance = Attendance.objects.create(
                student=student_profile,
                date=today,
                time_in=current_time,
                status='Present',
                location=location
            )
            
            if location == 'Client Office':
                client_id = request.POST.get('client')
                assignment_id = request.POST.get('assignment')
                work_type_id = request.POST.get('work_type')
                remarks = request.POST.get('remarks')
                
                if client_id and assignment_id and work_type_id:
                    ClientVisit.objects.create(
                        attendance=attendance,
                        client_id=client_id,
                        assignment_id=assignment_id,
                        work_type_id=work_type_id,
                        remarks=remarks
                    )
            messages.success(request, f"Marked IN at {current_time.strftime('%I:%M %p')}")
        
        elif attendance and not attendance.time_out:
            # Mark OUT
            attendance.time_out = current_time
            in_datetime = timezone.datetime.combine(today, attendance.time_in)
            out_datetime = timezone.datetime.combine(today, attendance.time_out)
            duration = out_datetime - in_datetime
            attendance.working_hours = round(duration.total_seconds() / 3600, 2)
            attendance.save()
            messages.success(request, f"Marked OUT at {current_time.strftime('%I:%M %p')}. Total hours: {attendance.working_hours}")
        
        else:
            messages.warning(request, "You have already completed your attendance for today.")
            
        return redirect('/')

    return redirect('/')
