# appKAI/utils.py
def calculate_ticket_price(coach_class):
    """
    Fungsi ini menghitung harga dasar tiket berdasarkan kelas.
    """
    base_price = {
        'Ekonomi': 100000,  # Harga dasar untuk kelas Ekonomi
        'Bisnis': 300000,   # Harga dasar untuk kelas Bisnis
        'Eksekutif': 500000 # Harga dasar untuk kelas Eksekutif
    }

    # Mengambil harga tiket berdasarkan kelas yang dipilih
    price = base_price.get(coach_class, 100000)  # Default ke Ekonomi jika kelas tidak ditemukan
    return price
