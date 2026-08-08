from django.contrib import admin
from .models import Conveyance, ConveyanceItem

class ConveyanceItemInline(admin.TabularInline):
    model = ConveyanceItem
    extra = 1

@admin.register(Conveyance)
class ConveyanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'total_amount', 'status')
    list_filter = ('status', 'date')
    search_fields = ('student__full_name',)
    inlines = [ConveyanceItemInline]
