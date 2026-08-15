from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Client, Assignment, WorkType

class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['Manager', 'Principal']
    def handle_no_permission(self):
        return redirect('/')

class ClientCreateView(ManagerRequiredMixin, CreateView):
    model = Client
    fields = ['name', 'contact_person', 'email', 'phone', 'address', 'status']
    template_name = 'core/form.html'
    success_url = reverse_lazy('practice:client_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Add New Client'
        ctx['cancel_url'] = self.success_url
        return ctx
        
    def form_valid(self, form):
        messages.success(self.request, "Client added successfully.")
        return super().form_valid(form)

class ClientUpdateView(ManagerRequiredMixin, UpdateView):
    model = Client
    fields = ['name', 'contact_person', 'email', 'phone', 'address', 'status']
    template_name = 'core/form.html'
    success_url = reverse_lazy('practice:client_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Edit Client'
        ctx['cancel_url'] = self.success_url
        return ctx
        
    def form_valid(self, form):
        messages.success(self.request, "Client updated successfully.")
        return super().form_valid(form)


class AssignmentCreateView(ManagerRequiredMixin, CreateView):
    model = Assignment
    fields = ['client', 'title', 'work_type', 'start_date', 'deadline', 'status', 'assigned_students']
    template_name = 'practice/assignment_form.html'
    success_url = reverse_lazy('practice:assignment_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'New Assignment'
        ctx['cancel_url'] = self.success_url
        ctx['is_edit'] = False
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "✅ Assignment created successfully.")
        return super().form_valid(form)


class AssignmentUpdateView(ManagerRequiredMixin, UpdateView):
    model = Assignment
    fields = ['client', 'title', 'work_type', 'start_date', 'deadline', 'status', 'assigned_students']
    template_name = 'practice/assignment_form.html'
    success_url = reverse_lazy('practice:assignment_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Edit — {self.object.title}'
        ctx['cancel_url'] = self.success_url
        ctx['is_edit'] = True
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f"✅ <strong>{self.object.title}</strong> updated successfully.")
        return super().form_valid(form)

@login_required
def client_list(request):
    clients = Client.objects.all().order_by('name')
    return render(request, 'practice/client_list.html', {'clients': clients})

@login_required
def assignment_list(request):
    from datetime import date
    status_filter = request.GET.get('status', '')
    all_assignments = Assignment.objects.select_related('client', 'work_type').prefetch_related('assigned_students')

    total_count        = all_assignments.count()
    in_progress_count  = all_assignments.filter(status='In Progress').count()
    not_started_count  = all_assignments.filter(status='Not Started').count()
    on_hold_count      = all_assignments.filter(status='On Hold').count()
    completed_count    = all_assignments.filter(status='Completed').count()

    assignments = all_assignments.order_by('-deadline')
    if status_filter:
        assignments = assignments.filter(status=status_filter)

    return render(request, 'practice/assignment_list.html', {
        'assignments':       assignments,
        'status_filter':     status_filter,
        'total_count':       total_count,
        'in_progress_count': in_progress_count,
        'not_started_count': not_started_count,
        'on_hold_count':     on_hold_count,
        'completed_count':   completed_count,
        'today':             date.today(),
    })

@login_required
def mark_assignment_status(request, pk):
    """Quick status update for Assignments — Manager/Principal only."""
    if request.user.role not in ['Manager', 'Principal']:
        messages.error(request, "Permission denied.")
        return redirect('practice:assignment_list')

    assignment = get_object_or_404(Assignment, pk=pk)
    new_status = request.POST.get('status')

    valid_statuses = ['Not Started', 'In Progress', 'On Hold', 'Completed']
    if new_status not in valid_statuses:
        messages.error(request, "Invalid status.")
        return redirect('practice:assignment_list')

    old_status = assignment.status
    assignment.status = new_status
    assignment.save()

    status_labels = {
        'Completed':   ('✅', 'success'),
        'In Progress': ('🔄', 'info'),
        'On Hold':     ('⏸️', 'warning'),
        'Not Started': ('📋', 'secondary'),
    }
    icon, _ = status_labels.get(new_status, ('✓', 'success'))
    messages.success(
        request,
        f"{icon} <strong>{assignment.title}</strong> marked as <strong>{new_status}</strong>."
    )
    return redirect('practice:assignment_list')
