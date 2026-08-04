from django.contrib import admin
from .models import Conveyance

@admin.register(Conveyance)
class ConveyanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'client', 'amount', 'status')
    list_filter = ('status', 'date')
    search_fields = ('student__full_name', 'client__name')
