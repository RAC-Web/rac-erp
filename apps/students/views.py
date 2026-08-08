from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib import messages
from .models import StudentProfile
from .forms import StudentForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import StudentProfile
from django.http import HttpResponse

@login_required
def student_list(request):
    if getattr(request.user, 'role', '') not in ('Principal', 'Manager'):
        return HttpResponse("Unauthorized", status=403)
    
    students = StudentProfile.objects.all().order_by('full_name')
    return render(request, 'students/list.html', {'students': students})

class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['Manager', 'Principal']
    
    def handle_no_permission(self):
        return redirect('/')

class StudentCreateView(ManagerRequiredMixin, CreateView):
    model = StudentProfile
    form_class = StudentForm
    template_name = 'core/form.html'
    success_url = reverse_lazy('students:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Add New Student'
        ctx['cancel_url'] = self.success_url
        return ctx
        
    def form_valid(self, form):
        messages.success(self.request, "Student profile created successfully.")
        return super().form_valid(form)

class StudentUpdateView(ManagerRequiredMixin, UpdateView):
    model = StudentProfile
    form_class = StudentForm
    template_name = 'core/form.html'
    success_url = reverse_lazy('students:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Edit Student: {self.object.full_name}'
        ctx['cancel_url'] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Student profile updated successfully.")
        return super().form_valid(form)

class StudentDeleteView(ManagerRequiredMixin, DeleteView):
    model = StudentProfile
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('students:list')
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cancel_url'] = self.success_url
        return ctx
        
    def form_valid(self, form):
        messages.success(self.request, "Student profile deleted successfully.")
        return super().form_valid(form)
