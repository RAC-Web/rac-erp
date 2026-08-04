from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Conveyance
from apps.practice.models import Client, Assignment
from django.contrib import messages

@login_required
def submit_conveyance(request):
    if getattr(request.user, 'role', '') != 'Student':
        messages.error(request, "Only students can submit conveyance.")
        return redirect('/')
        
    if request.method == 'POST':
        date = request.POST.get('date')
        client_id = request.POST.get('client')
        assignment_id = request.POST.get('assignment')
        from_loc = request.POST.get('from_location')
        to_loc = request.POST.get('to_location')
        transport = request.POST.get('transport')
        amount = request.POST.get('amount')
        desc = request.POST.get('description')
        attachment = request.FILES.get('attachment')
        
        Conveyance.objects.create(
            student=request.user.student_profile,
            date=date,
            client_id=client_id,
            assignment_id=assignment_id,
            from_location=from_loc,
            to_location=to_loc,
            transport=transport,
            amount=amount,
            description=desc,
            attachment=attachment
        )
        messages.success(request, "Conveyance bill submitted successfully.")
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
        conveyances = Conveyance.objects.filter(student=request.user.student_profile).order_by('-date')
    else:
        conveyances = Conveyance.objects.all().order_by('-date')
        
    return render(request, 'conveyance/list.html', {'conveyances': conveyances})
