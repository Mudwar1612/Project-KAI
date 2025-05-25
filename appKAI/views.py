from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count, Sum
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from .models import Ticket, Pemesan, Penumpang, Order
from .utils import calculate_ticket_price
from django.core.files.uploadedfile import SimpleUploadedFile
import qrcode
import base64
from io import BytesIO
import json

# Create your views here.
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_superuser:
                # Login untuk admin (superuser)
                login(request, user)
                return redirect('admin')  # Ganti 'admin_dashboard' dengan URL dashboard admin Anda
            else:
                # Login untuk pengguna biasa
                login(request, user)
                return redirect('home')  # Ganti 'user_dashboard' dengan URL dashboard pengguna Anda
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'login.html')

@login_required
@user_passes_test(lambda user: user.is_superuser)
def admin_view(request):
    if not request.user.is_superuser:
        return redirect('login')
    # Mengambil semua pemesanan dengan status 'Sudah Dibayar'
    orders = Order.objects.filter(status='Sudah Dibayar')
    # Menghitung jumlah pemesanan yang sudah dibayar
    jumlah_pemesanan_sudah_dibayar = orders.count()
    # Menghitung total harga dari semua pemesanan yang sudah dibayar
    total_harga = orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    # Mengirim data ke template
    return render(request, 'admin/admin.html', {
        'orders': orders,
        'jumlah_pemesanan_sudah_dibayar': jumlah_pemesanan_sudah_dibayar,
        'total_harga': total_harga
    })

@login_required
def user_view(request):
    # Logika untuk pengguna biasa tidak dapat mengakses halaman superuser
    if request.user.is_superuser:
        return redirect('admin')
    return render(request, 'utama/home.html')

def signup_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        # Validasi password
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters!')
            return redirect('signup')
        # Validasi username
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken')
            return redirect('signup')
        # Buat pengguna
        user = User.objects.create_user(
            username=username, 
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password
        )
        user.save()
        messages.success(request, 'Account successfully created! You can now login.')
        return redirect('login')
    return render(request, 'signup.html')

def custom_logout_view(request):
    logout(request)
    return redirect('login')

# View untuk menampilkan tiket dan menangani pemesanan tiket
def order_view(request):
    tickets = Ticket.objects.all()
    if request.method == 'POST':
        # Handle pemesanan tiket
        ticket_id = request.POST.get('ticket_id')
        ticket = get_object_or_404(Ticket, id=ticket_id)
        if ticket.total_seats > 0:
            ticket.total_seats -= 1
            ticket.save()
            return JsonResponse({'success': True, 'message': 'Tiket berhasil dipesan!'})
        else:
            return JsonResponse({'success': False, 'message': 'Tiket tidak tersedia'})
    # Menghitung harga tiket untuk setiap tiket yang ada
    for ticket in tickets:
        ticket.price = calculate_ticket_price(ticket.coach_class)
    return render(request, 'utama/order.html', {'tickets': tickets})

def prosesorder_view(request):
    # Ambil parameter ticket_code dari URL
    ticket_code = request.POST.get('ticket_code') if request.method == 'POST' else request.GET.get('ticket_code')
    ticket = None
    # Jika ticket_code ditemukan, ambil data tiket dari database
    if ticket_code:
        try:
            ticket = Ticket.objects.get(ticket_code=ticket_code)
        except Ticket.DoesNotExist:
            ticket = None
    if request.method == 'POST':
        # Ambil jumlah tiket yang dipesan
        jumlah_tiket = int(request.POST.get('jumlah_tiket', 1))  # Default 1 jika tidak diisi
        print(f"DEBUG: jumlah_tiket: {jumlah_tiket}")
        # Ambil data pemesan
        title_pemesan = request.POST.get('title-pemesan')
        nama_pemesan = request.POST.get('nama-pemesan')
        identitas_pemesan = request.POST.get('identitas-pemesan')
        hp_pemesan = request.POST.get('hp-pemesan')
        email_pemesan = request.POST.get('email-pemesan')
        alamat_pemesan = request.POST.get('alamat-pemesan')
        # Ambil data penumpang
        title_penumpang = request.POST.get('title-penumpang')
        nama_penumpang = request.POST.get('nama-penumpang')
        identitas_penumpang = request.POST.get('identitas-penumpang')
        nomor_identitas_penumpang = request.POST.get('nomor-penumpang')
        # Validasi apakah semua data terisi
        missing_fields = []
        all_fields = {
            'title_pemesan': title_pemesan,
            'nama_pemesan': nama_pemesan,
            'identitas_pemesan': identitas_pemesan,
            'hp_pemesan': hp_pemesan,
            'email_pemesan': email_pemesan,
            'alamat_pemesan': alamat_pemesan,
            'title_penumpang': title_penumpang,
            'nama_penumpang': nama_penumpang,
            'identitas_penumpang': identitas_penumpang,
            'nomor_identitas_penumpang': nomor_identitas_penumpang,
            'ticket_code': ticket_code,
        }
        for field, value in all_fields.items():
            if not value:
                missing_fields.append(field)
                print(f"DEBUG: {field} tidak diisi.")
        if missing_fields:
            print(f"DEBUG: Validasi gagal. Kolom kosong: {', '.join(missing_fields)}")
            return render(request, 'sub/prosesorder.html', {
                'error': 'Semua kolom harus diisi!',
                'ticket': ticket,
            })
        # Ambil data tiket berdasarkan kode tiket yang dipilih
        try:
            ticket = Ticket.objects.get(ticket_code=ticket_code)
            print(f"DEBUG: Tiket berhasil ditemukan: {ticket}")
        except Ticket.DoesNotExist:
            print("DEBUG: Tiket tidak ditemukan.")
            return render(request, 'sub/prosesorder.html', {
                'error': 'Tiket tidak ditemukan!',
            })
        # Hitung total harga
        total_harga = ticket.price * jumlah_tiket
        print(f"DEBUG: Total harga: {total_harga}")
        try:
            # Simpan data pemesan
            pemesan = Pemesan.objects.create(
                title=title_pemesan,
                nama=nama_pemesan,
                tipe_identitas=identitas_pemesan,
                no_hp=hp_pemesan,
                email=email_pemesan,
                alamat=alamat_pemesan
            )
            print(f"DEBUG: Data Pemesan berhasil disimpan: {pemesan}")
            # Simpan data penumpang
            penumpang = Penumpang.objects.create(
                title=title_penumpang,
                nama=nama_penumpang,
                tipe_identitas=identitas_penumpang,
                nomor_identitas=nomor_identitas_penumpang,
                pemesan=pemesan
            )
            print(f"DEBUG: Data Penumpang berhasil disimpan: {penumpang}")
        except Exception as e:
            print(f"DEBUG: Terjadi kesalahan saat menyimpan data: {e}")
            return render(request, 'sub/prosesorder.html', {
                'error': 'Terjadi kesalahan saat menyimpan data. Silakan coba lagi.',
                'ticket': ticket,
            })
        # Buat entri di model Order
        order = Order.objects.create(
            pemesan=pemesan,
            penumpang=penumpang,
            ticket=ticket,
            status='Belum Bayar'
        )
        # Redirect ke halaman pembayaran setelah data disimpan
        print("DEBUG: Redirect ke halaman pembayaran.")
        return redirect('belumbayar')  # Pastikan 'belumbayar' sudah terdaftar di urls.py
    # Jika metode bukan POST, kirim data tiket ke template
    if ticket:
        total_harga = ticket.price * int(request.GET.get('jumlah_tiket', 1))
    else:
        total_harga = 0
    return render(request, 'sub/prosesorder.html', {
        'ticket': ticket,
        'total_harga': total_harga
    })

def belumbayar(request):
    orders = Order.objects.filter(status='Belum Bayar')  # Sesuaikan query-nya
    return render(request, 'sub/belumbayar.html', {'orders': orders})

def bayar_view(request, order_id):
    order = Order.objects.get(id=order_id) 
    if request.method == "POST":
        # Update order status to 'Sudah Dibayar'
        order.status = 'Sudah Dibayar'
        order.payment_date = timezone.now()  # Menyimpan tanggal pembayaran
        order.total_price = order.ticket.price  # Misalnya harga tiket
        order.save()
        # Membuat QR Code yang berisi URL ke halaman selesai.html
        qr_url = f"http://127.0.0.1:8000/#/{order.id}/"  # URL yang akan di-encode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)  # Menambahkan URL ke QR Code
        qr.make(fit=True)
        # Menghasilkan gambar QR Code
        img = qr.make_image(fill='black', back_color='white') 
        # Mengonversi gambar ke BytesIO untuk disimpan ke dalam database
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        buffered.seek(0)
        # Simpan QR Code ke dalam field 'qr_code' di database
        order.qr_code.save(f"qr_{order.id}.png", SimpleUploadedFile(f"qr_{order.id}.png", buffered.getvalue()), save=True)
        # Simpan perubahan pada model
        order.save()
        # Menyediakan data QR Code dalam bentuk base64 untuk ditampilkan di template
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8") 
        context = {
            'order': order,
            'qr_code': qr_code_base64,  # Mengirim QR Code dalam format base64
        }
        return render(request, 'sub/sudahdibayar.html', context) 
    return render(request, 'sub/belumbayar.html', {'order': order})

def sudahdibayar(request):
    # Ambil data tiket dengan status "Sudah Dibayar"
    order = Order.objects.filter(status='Sudah Dibayar').order_by('-created_at').first()
    if not order:
        # Jika tidak ada tiket dengan status "Sudah Dibayar"
        return render(request, 'sub/sudahdibayar.html', {'order': None, 'qr_code': None})
    # Generate QR Code untuk order jika ada
    qr_url = f"http://127.0.0.1:8000/selesai/{order.id}/"  # URL untuk ditampilkan di QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)  # Tambahkan URL ke QR Code
    qr.make(fit=True)
    # Konversi QR Code ke base64
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    # Render template dengan data tiket dan QR Code
    context = {
        'order': order,
        'qr_code': qr_code_base64,  # QR Code dalam format base64
    }
    return render(request, 'sub/sudahdibayar.html', context)

@csrf_exempt
def update_card_header(request):
    if request.method == 'POST':
        data = json.loads(request.body)  # Parse JSON data from AJAX request
        # Extract form data
        departure = data.get('departure')
        destination = data.get('destination')
        date = data.get('date')
        adults = data.get('adults', 1)
        babies = data.get('babies', 0)
        # Format the updated header string
        header = f"{departure.upper()} ➞ {destination.upper()}<br>{date} - {adults} Dewasa"
        if int(babies) > 0:
            header += f", {babies} Bayi"
        return JsonResponse({'header': header}, status=200)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_dates(request):
    if request.method == "GET":
        # Dapatkan tanggal hari ini
        today = datetime.today() 
        # Buat daftar 30 hari ke depan
        dates = [
            {
                "day": (today + timedelta(days=i)).strftime("%A").upper(),  # Hari (uppercase)
                "date": (today + timedelta(days=i)).strftime("%d %B %Y"),  # Format: DD Bulan YYYY
                "iso_date": (today + timedelta(days=i)).strftime("%Y-%m-%d"),  # Format ISO
            }
            for i in range(30)
        ]
        return JsonResponse({"dates": dates})
    return JsonResponse({"error": "Invalid request method"}, status=400)

def dibatalkan(request):
    return render(request, 'sub/dibatalkan.html')

def refund(request):
    return render(request, 'sub/refund.html')
    
def home_view(request):
    return render(request, 'utama/home.html')
    
def booking_view(request):
    return render(request, 'utama/booking.html')