import random
import string
from django.db import models
from .utils import calculate_ticket_price

class TicketData(models.Model):
    departure_station = models.CharField(max_length=100)
    destination_station = models.CharField(max_length=100)
    departure_date = models.DateField()
    adult_count = models.PositiveIntegerField(default=1)
    baby_count = models.PositiveIntegerField(default=0)


class Ticket(models.Model):
    departure_city = models.CharField(max_length=100)
    destination_city = models.CharField(max_length=100)
    departure_date = models.DateField()
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    coach_class = models.CharField(max_length=100)  # Ekonomi, Bisnis, Eksekutif
    total_seats = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Harga tiket
    ticket_code = models.CharField(max_length=10, unique=True, editable=False)

    def generate_ticket_code(self):
        """Generate a unique random ticket code."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    def save(self, *args, **kwargs):
        if not self.ticket_code:
            self.ticket_code = self.generate_ticket_code()

        # Harga tetap per tiket sesuai dengan kelas tiket
        base_price = calculate_ticket_price(self.coach_class)  # Dapatkan harga dasar per tiket
        self.price = base_price

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.departure_city} ➞ {self.destination_city} ({self.ticket_code})"

    def formatted_departure_time(self):
        return self.departure_time.strftime('%H:%M')

    def formatted_arrival_time(self):
        return self.arrival_time.strftime('%H:%M')

class Pemesan(models.Model):
    title = models.CharField(max_length=10)
    nama = models.CharField(max_length=255)
    tipe_identitas = models.CharField(max_length=10)
    no_hp = models.CharField(max_length=15)
    email = models.EmailField()
    alamat = models.TextField()

    def __str__(self):
        return self.nama

class Penumpang(models.Model):
    title = models.CharField(max_length=10)
    nama = models.CharField(max_length=255)
    tipe_identitas = models.CharField(max_length=10)
    nomor_identitas = models.CharField(max_length=50)
    pemesan = models.ForeignKey(Pemesan, on_delete=models.CASCADE, related_name='penumpang')

    def __str__(self):
        return self.nama

class Order(models.Model):
    STATUS_CHOICES = [
        ('Belum Bayar', 'Belum Bayar'),
        ('Sudah Dibayar', 'Sudah Dibayar'),
    ]

    pemesan = models.ForeignKey(Pemesan, on_delete=models.CASCADE, related_name='orders')
    penumpang = models.ForeignKey(Penumpang, on_delete=models.CASCADE, related_name='orders')
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='orders')
    payment_date = models.DateTimeField(null=True, blank=True)  # Field tanggal pembayaran
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Field total harga
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True)  # Menyimpan QR Code
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Belum Bayar')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.status}"