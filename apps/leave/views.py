from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import CreateView, UpdateView, DeleteView
from .models import LeaveRequest, LeaveType
from .forms import LeaveRequestForm
from django.contrib import messages

class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['Manager', 'Principal']
    def handle_no_permission(self):
        return redirect('/')

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

@login_required
def approve_leave(request, pk):
    if request.user.role not in ['Manager', 'Principal']:
        messages.error(request, "Unauthorized")
        return redirect('leave:leave_list')
        
    leave = get_object_or_404(LeaveRequest, pk=pk)
    
    if request.user.role == 'Manager' and leave.status == 'Pending':
        leave.status = 'Manager Approved'
        leave.save()
        messages.success(request, f"Leave {leave.id} approved by Manager.")
    elif request.user.role == 'Principal' and leave.status in ['Pending', 'Manager Approved']:
        leave.status = 'Principal Approved'
        leave.save()
        messages.success(request, f"Leave {leave.id} fully approved by Principal.")
        
    return redirect('leave:leave_list')

@login_required
def reject_leave(request, pk):
    if request.user.role not in ['Manager', 'Principal']:
        messages.error(request, "Unauthorized")
        return redirect('leave:leave_list')
        
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = 'Rejected'
    leave.save()
    messages.error(request, f"Leave {leave.id} has been rejected.")
    return redirect('leave:leave_list')

class LeaveCreateView(ManagerRequiredMixin, CreateView):
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'core/form.html'
    success_url = reverse_lazy('leave:leave_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Add Leave Request (Manager)'
        ctx['cancel_url'] = self.success_url
        return ctx
        
    def form_valid(self, form):
        messages.success(self.request, "Leave request created successfully.")
        return super().form_valid(form)

class LeaveUpdateView(ManagerRequiredMixin, UpdateView):
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'core/form.html'
    success_url = reverse_lazy('leave:leave_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Edit Leave: {self.object.student.full_name}'
        ctx['cancel_url'] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Leave request updated successfully.")
        return super().form_valid(form)

class LeaveDeleteView(ManagerRequiredMixin, DeleteView):
    model = LeaveRequest
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('leave:leave_list')
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cancel_url'] = self.success_url
        return ctx
        
    def form_valid(self, form):
        messages.success(self.request, "Leave request deleted successfully.")
        return super().form_valid(form)

from django.http import HttpResponse
from .utils import generate_leave_pdf

@login_required
def download_leave_pdf(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    
    # Only allow students to download their own, or managers/principals to download any
    if request.user.role == 'Student' and leave.student != getattr(request.user, 'student_profile', None):
        messages.error(request, "Unauthorized")
        return redirect('leave:leave_list')
        
    if leave.status not in ['Manager Approved', 'Principal Approved']:
        messages.error(request, "Leave request must be approved to download PDF.")
        return redirect('leave:leave_list')
        
    pdf_buffer = generate_leave_pdf(leave)
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Leave_Form_{leave.id}.pdf"'
    return response
