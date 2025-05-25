# appKAI/admin.py
from django.contrib import admin
from .models import Ticket

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'departure_city', 'destination_city', 'departure_date', 'total_seats')
