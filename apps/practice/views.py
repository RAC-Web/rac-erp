from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Client, Assignment

@login_required
def client_list(request):
    clients = Client.objects.all().order_by('name')
    return render(request, 'practice/client_list.html', {'clients': clients})

@login_required
def assignment_list(request):
    assignments = Assignment.objects.all().order_by('-deadline')
    return render(request, 'practice/assignment_list.html', {'assignments': assignments})
