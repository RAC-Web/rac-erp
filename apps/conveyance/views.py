from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import CreateView, UpdateView, DeleteView
from .models import Conveyance
from .forms import ConveyanceForm
from apps.practice.models import Client, Assignment
from django.contrib import messages

class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['Manager', 'Principal']
    def handle_no_permission(self):
        return redirect('/')

@login_required
def submit_conveyance(request):
    if getattr(request.user, 'role', '') != 'Student':
        messages.error(request, "Only students can submit conveyance.")
        return redirect('/')
        
    if request.method == 'POST':
        date = request.POST.get('date')
        
        client_ids = request.POST.getlist('client[]')
        assignment_ids = request.POST.getlist('assignment[]')
        from_locs = request.POST.getlist('from_location[]')
        to_locs = request.POST.getlist('to_location[]')
        transports = request.POST.getlist('transport[]')
        amounts = request.POST.getlist('amount[]')
        descriptions = request.POST.getlist('description[]')
        
        # Calculate total amount
        total = sum([float(a) for a in amounts if a.strip()])
        
        conveyance = Conveyance.objects.create(
            student=request.user.student_profile,
            date=date,
            total_amount=total,
            status='Pending'
        )
        
        from .models import ConveyanceItem
        
        for i in range(len(from_locs)):
            amount_val = float(amounts[i]) if amounts[i].strip() else 0.0
            client_id = client_ids[i] if i < len(client_ids) and client_ids[i] else None
            assignment_id = assignment_ids[i] if i < len(assignment_ids) and assignment_ids[i] else None
            
            ConveyanceItem.objects.create(
                conveyance=conveyance,
                client_id=client_id,
                assignment_id=assignment_id,
                from_location=from_locs[i],
                to_location=to_locs[i],
                transport=transports[i],
                amount=amount_val,
                description=descriptions[i] if i < len(descriptions) else ''
            )
            
        messages.success(request, f"Conveyance claim for {total} BDT submitted successfully.")
        return redirect('conveyance:list')
        
    clients = Client.objects.filter(status='Active')
    assignments = Assignment.objects.exclude(status='Completed')
    return render(request, 'conveyance/submit.html', {
        'clients': clients,
        'assignments': assignments
    })

@login_required
def conveyance_list(request):
    if getattr(request.user, 'role', '') == 'Student':
        conveyances = Conveyance.objects.filter(student=request.user.student_profile).prefetch_related('items__client').order_by('-date')
    else:
        conveyances = Conveyance.objects.all().prefetch_related('items__client').select_related('student').order_by('-date')
        
    return render(request, 'conveyance/list.html', {'conveyances': conveyances})

@login_required
def approve_conveyance(request, pk):
    if request.user.role not in ['Manager', 'Principal']:
        messages.error(request, "Unauthorized")
        return redirect('conveyance:list')
        
    conveyance = get_object_or_404(Conveyance, pk=pk)
    
    if conveyance.status == 'Pending':
        conveyance.status = 'Approved'
        conveyance.approved_by = request.user
        conveyance.save()
        messages.success(request, f"Conveyance bill {conveyance.id} approved.")
        
    return redirect('conveyance:list')

@login_required
def reject_conveyance(request, pk):
    if request.user.role not in ['Manager', 'Principal']:
        messages.error(request, "Unauthorized")
        return redirect('conveyance:list')
        
    conveyance = get_object_or_404(Conveyance, pk=pk)
    conveyance.status = 'Rejected'
    conveyance.save()
    messages.error(request, f"Conveyance bill {conveyance.id} has been rejected.")
    return redirect('conveyance:list')

class ConveyanceCreateView(ManagerRequiredMixin, CreateView):
    model = Conveyance
    form_class = ConveyanceForm
    template_name = 'core/form.html'
    success_url = reverse_lazy('conveyance:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Add Conveyance (Manager)'
        ctx['cancel_url'] = self.success_url
        return ctx
        
    def form_valid(self, form):
        messages.success(self.request, "Conveyance record created successfully.")
        return super().form_valid(form)

class ConveyanceUpdateView(ManagerRequiredMixin, UpdateView):
    model = Conveyance
    form_class = ConveyanceForm
    template_name = 'core/form.html'
    success_url = reverse_lazy('conveyance:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Edit Conveyance: {self.object.student.full_name}'
        ctx['cancel_url'] = self.success_url
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Conveyance record updated successfully.")
        return super().form_valid(form)

class ConveyanceDeleteView(ManagerRequiredMixin, DeleteView):
    model = Conveyance
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('conveyance:list')
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cancel_url'] = self.success_url
        return ctx
        
    def form_valid(self, form):
        messages.success(self.request, "Conveyance record deleted successfully.")
        return super().form_valid(form)
