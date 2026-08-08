from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import CreateView, UpdateView, DeleteView
from django.utils import timezone
from django.http import HttpResponse
from .models import Attendance
from .forms import AttendanceForm
from apps.practice.models import Client, Assignment, WorkType, ClientVisit
from apps.students.models import StudentProfile
from django.contrib import messages

class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['Manager', 'Principal']
    def handle_no_permission(self):
        return redirect('/')

@login_required
def mark_attendance(request):
    if request.method == 'POST':
        student_profile = getattr(request.user, 'student_profile', None)
        if not student_profile:
            messages.error(request, "Only students can mark attendance.")
            return redirect('/')
        
        now_local = timezone.localtime(timezone.now())
        today = now_local.date()
        current_time = now_local.time()
        
        attendance = Attendance.objects.filter(student=student_profile, date=today).first()
        
        if not attendance:
            location = request.POST.get('location', 'Office')
            in_lat = request.POST.get('in_latitude')
            in_lng = request.POST.get('in_longitude')
            
            attendance = Attendance.objects.create(
                student=student_profile,
                date=today,
                time_in=current_time,
                status='Present',
                location=location,
                in_latitude=in_lat if in_lat else None,
                in_longitude=in_lng if in_lng else None
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
            now_local = timezone.localtime(timezone.now())
            current_time = now_local.time()
            out_lat = request.POST.get('out_latitude')
            out_lng = request.POST.get('out_longitude')
            
            attendance.time_out = current_time
            if out_lat and out_lng:
                attendance.out_latitude = out_lat
                attendance.out_longitude = out_lng
                
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

@login_required
def attendance_list(request):
    role = getattr(request.user, 'role', '')
    
    if role == 'Student':
        student_profile = getattr(request.user, 'student_profile', None)
        if student_profile:
            records = Attendance.objects.filter(student=student_profile).order_by('-date')
        else:
            records = Attendance.objects.none()
    else:
        records = Attendance.objects.all().select_related('student').order_by('-date')
    
    # Filter by month/year if provided
    month = request.GET.get('month')
    year = request.GET.get('year')
    if month and year:
        records = records.filter(date__month=int(month), date__year=int(year))
    
    return render(request, 'attendance/list.html', {
        'records': records,
        'month': month,
        'year': year,
    })

class AttendanceCreateView(ManagerRequiredMixin, CreateView):
    model = Attendance
    form_class = AttendanceForm
    template_name = 'core/form.html'
    success_url = reverse_lazy('attendance:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Add Attendance Record'
        ctx['cancel_url'] = self.success_url
        return ctx
        
    def form_valid(self, form):
        messages.success(self.request, "Attendance record created successfully.")
        return super().form_valid(form)

class AttendanceUpdateView(ManagerRequiredMixin, UpdateView):
    model = Attendance
    form_class = AttendanceForm
    template_name = 'core/form.html'
    success_url = reverse_lazy('attendance:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Edit Attendance: {self.object.student.full_name} ({self.object.date})'
        ctx['cancel_url'] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Attendance record updated successfully.")
        return super().form_valid(form)

class AttendanceDeleteView(ManagerRequiredMixin, DeleteView):
    model = Attendance
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('attendance:list')
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cancel_url'] = self.success_url
        return ctx
        
    def form_valid(self, form):
        messages.success(self.request, "Attendance record deleted successfully.")
        return super().form_valid(form)
