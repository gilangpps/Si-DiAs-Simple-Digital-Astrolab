import sys
print("Interpreter:", sys.executable)
print("Sys.path:", sys.path)

import tkinter as tk
import datetime
import math
import ephem
import matplotlib.pyplot as plt

# Fungsi untuk menghitung posisi Matahari berdasarkan lokasi dan waktu saat ini
def hitung_posisi_matahari(lat, lon):
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = datetime.datetime.utcnow()  # waktu UTC
    matahari = ephem.Sun(observer)
    # Mengambil azimuth dan ketinggian (dalam radian)
    az = float(matahari.az)
    alt = float(matahari.alt)
    return az, alt

# Fungsi untuk menghitung posisi Bulan dan fase Bulan
def hitung_posisi_bulan(lat, lon):
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = datetime.datetime.utcnow()
    bulan = ephem.Moon(observer)
    az = float(bulan.az)
    alt = float(bulan.alt)
    fase = bulan.moon_phase  # nilai antara 0 (bulan baru) dan 1 (bulan purnama)
    return az, alt, fase

# Fungsi untuk menghitung waktu terbit dan terbenam Matahari
def hitung_terbit_terbenam(lat, lon):
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = datetime.datetime.utcnow()
    matahari = ephem.Sun(observer)
    try:
        terbit = observer.next_rising(matahari)
        terbenam = observer.next_setting(matahari)
        terbit_local = ephem.localtime(terbit)
        terbenam_local = ephem.localtime(terbenam)
    except Exception as e:
        terbit_local = terbenam_local = "N/A"
    return terbit_local, terbenam_local

# Fungsi untuk mengubah koordinat polar (angle, radius) ke koordinat Cartesian pada canvas
def polar_to_cartesian(angle, radius, cx, cy):
    # Sudut dalam radian; canvas: 0 radian menunjuk ke kanan
    x = cx + radius * math.cos(angle)
    y = cy - radius * math.sin(angle)
    return x, y

# Fungsi untuk menampilkan peta langit sederhana dengan matplotlib
def plot_peta_langit(lat, lon):
    # Contoh sederhana: menampilkan beberapa bintang terkenal
    bintang = {
        'Sirius': (101.2875, -16.7161),
        'Betelgeuse': (88.7929, 7.4071),
        'Rigel': (78.6345, -8.2016),
        'Aldebaran': (68.9800, 16.5093)
    }
    
    plt.figure(figsize=(6,6))
    for nama, (ra, dec) in bintang.items():
        plt.plot(ra, dec, 'o', label=nama)
        plt.text(ra, dec, f' {nama}', fontsize=9)
    plt.xlabel('Right Ascension (°)')
    plt.ylabel('Declination (°)')
    plt.title('Peta Langit Sederhana')
    plt.legend()
    plt.grid(True)
    plt.show()

# Fungsi update GUI secara real-time
def update_gui():
    try:
        lat = float(entry_lat.get())
        lon = float(entry_lon.get())
    except ValueError:
        status_label.config(text="Masukkan latitude dan longitude yang valid!")
        window.after(1000, update_gui)
        return

    # Hitung posisi Matahari
    az, alt = hitung_posisi_matahari(lat, lon)
    # Hitung posisi Bulan dan fase
    az_bulan, alt_bulan, fase_bulan = hitung_posisi_bulan(lat, lon)
    # Hitung waktu terbit dan terbenam Matahari
    terbit, terbenam = hitung_terbit_terbenam(lat, lon)
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_text = (
        f"Waktu lokal: {now}\n"
        f"Matahari -> Azimuth: {math.degrees(az):.1f}°, Ketinggian: {math.degrees(alt):.1f}°\n"
        f"Bulan    -> Azimuth: {math.degrees(az_bulan):.1f}°, Ketinggian: {math.degrees(alt_bulan):.1f}°, Fase: {fase_bulan:.2f}\n"
        f"Matahari Terbit: {terbit if isinstance(terbit, str) else terbit.strftime('%H:%M:%S')} | "
        f"Terbenam: {terbenam if isinstance(terbenam, str) else terbenam.strftime('%H:%M:%S')}"
    )
    status_label.config(text=status_text)

    # Bersihkan canvas dan gambar dial astrolab
    canvas.delete("all")
    
    # Gambar lingkaran dial
    cx, cy = 200, 200  # pusat canvas
    radius = 150
    canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, outline="black", width=2)

    # Gambar garis arah (misalnya tiap 30 derajat)
    for deg in range(0, 360, 30):
        rad = math.radians(deg)
        x_end, y_end = polar_to_cartesian(rad, radius, cx, cy)
        canvas.create_line(cx, cy, x_end, y_end, fill="gray", dash=(2,2))
        # Label arah
        x_label, y_label = polar_to_cartesian(rad, radius+15, cx, cy)
        canvas.create_text(x_label, y_label, text=f"{deg}°", font=("Arial", 8))
    
    # Gambar pointer Matahari (merah)
    pointer_length = radius * 0.9
    x_pointer, y_pointer = polar_to_cartesian(az, pointer_length, cx, cy)
    canvas.create_line(cx, cy, x_pointer, y_pointer, fill="red", width=3, arrow=tk.LAST)
    
    # Gambar pointer Bulan (biru)
    x_pointer_bulan, y_pointer_bulan = polar_to_cartesian(az_bulan, pointer_length * 0.8, cx, cy)
    canvas.create_line(cx, cy, x_pointer_bulan, y_pointer_bulan, fill="blue", width=3, arrow=tk.LAST)
    
    # Perbarui setiap 1 detik
    window.after(1000, update_gui)

# Fungsi untuk membuka peta langit
def buka_peta_langit():
    try:
        lat = float(entry_lat.get())
        lon = float(entry_lon.get())
    except ValueError:
        status_label.config(text="Masukkan latitude dan longitude yang valid!")
        return
    plot_peta_langit(lat, lon)

# Membuat jendela utama
window = tk.Tk()
window.title("GUI Astrolab Real-Time")

# Frame untuk input lokasi dan tombol peta langit
frame_input = tk.Frame(window)
frame_input.pack(pady=10)

tk.Label(frame_input, text="Latitude:").grid(row=0, column=0, padx=5)
entry_lat = tk.Entry(frame_input, width=10)
entry_lat.grid(row=0, column=1, padx=5)
entry_lat.insert(0, "-6.2000")  # contoh: Jakarta

tk.Label(frame_input, text="Longitude:").grid(row=0, column=2, padx=5)
entry_lon = tk.Entry(frame_input, width=10)
entry_lon.grid(row=0, column=3, padx=5)
entry_lon.insert(0, "106.8166")  # contoh: Jakarta

btn_peta = tk.Button(frame_input, text="Lihat Peta Langit", command=buka_peta_langit)
btn_peta.grid(row=0, column=4, padx=5)

# Canvas untuk menggambar dial astrolab
canvas = tk.Canvas(window, width=400, height=400, bg="white")
canvas.pack()

# Label status untuk menampilkan informasi posisi dan waktu
status_label = tk.Label(window, text="Memperbarui...", font=("Arial", 10))
status_label.pack(pady=5)

# Mulai update GUI
update_gui()

# Menjalankan aplikasi
window.mainloop()
