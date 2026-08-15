from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Client, Assignment

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

@login_required
def client_list(request):
    clients = Client.objects.all().order_by('name')
    return render(request, 'practice/client_list.html', {'clients': clients})

@login_required
def assignment_list(request):
    assignments = Assignment.objects.all().order_by('-deadline')
    return render(request, 'practice/assignment_list.html', {'assignments': assignments})
