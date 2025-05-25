from django.core.management.base import BaseCommand
from appKAI.models import Ticket
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Generate tickets for the next month'

    def handle(self, *args, **kwargs):
        cities = ['BANDUNG', 'JAKARTA', 'MALANG']
        coach_classes = ['Ekonomi', 'Bisnis', 'Eksekutif']

        for day in range(1, 31):
            date = datetime.today() + timedelta(days=day)
            for departure in cities:
                for destination in cities:
                    if departure != destination:
                        for coach_class in coach_classes:
                            Ticket.objects.create(
                                departure_city=departure,
                                destination_city=destination,
                                departure_time=datetime.now().time(),
                                arrival_time=(datetime.now() + timedelta(hours=random.randint(4, 12))).time(),
                                departure_date=date.date(),
                                arrival_date=date.date(),
                                coach_class=coach_class,
                                total_seats=25,
                                price=random.randint(100000, 800000),
                            )
        self.stdout.write("Tickets for the next month have been generated.")
