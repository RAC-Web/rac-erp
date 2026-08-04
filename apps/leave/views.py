from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import LeaveRequest, LeaveType
from django.contrib import messages

@login_required
def apply_leave(request):
    if request.method == 'POST':
        leave_type_id = request.POST.get('leave_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason')
        
        student_profile = getattr(request.user, 'student_profile', None)
        if not student_profile:
            messages.error(request, "Only students can apply for leave.")
            return redirect('leave:apply_leave')
            
        leave_type = LeaveType.objects.get(id=leave_type_id)
        
        LeaveRequest.objects.create(
            student=student_profile,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason
        )
        messages.success(request, "Leave request submitted successfully.")
        return redirect('leave:leave_list')
        
    leave_types = LeaveType.objects.all()
    return render(request, 'leave/apply.html', {'leave_types': leave_types})

@login_required
def leave_list(request):
    student_profile = getattr(request.user, 'student_profile', None)
    if student_profile:
        requests = LeaveRequest.objects.filter(student=student_profile).order_by('-applied_on')
    else:
        requests = LeaveRequest.objects.all().order_by('-applied_on')
        
    return render(request, 'leave/list.html', {'requests': requests})
