import sys
print("Interpreter:", sys.executable)
print("Sys.path:", sys.path)

import tkinter as tk
import datetime
import math
import ephem


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

# Fungsi untuk mengubah koordinat polar (angle, radius) ke koordinat Cartesian pada canvas
def polar_to_cartesian(angle, radius, cx, cy):
    # Sudut dalam radian; canvas: 0 radian menunjuk ke kanan
    x = cx + radius * math.cos(angle)
    y = cy - radius * math.sin(angle)
    return x, y

# Fungsi update GUI secara real-time
def update_gui():
    try:
        lat = float(entry_lat.get())
        lon = float(entry_lon.get())
    except ValueError:
        status_label.config(text="Masukkan latitude dan longitude yang valid!")
        window.after(1000, update_gui)
        return

    az, alt = hitung_posisi_matahari(lat, lon)
    
    # Update status
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_label.config(text=f"Waktu lokal: {now} | Azimuth: {math.degrees(az):.1f}° | Ketinggian: {math.degrees(alt):.1f}°")

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
    
    # Tentukan panjang pointer sesuai ketinggian Matahari (misalnya skala sederhana)
    # Disini pointer akan mengarah ke azimuth (perhitungan sederhana)
    pointer_length = radius * 0.9
    x_pointer, y_pointer = polar_to_cartesian(az, pointer_length, cx, cy)
    canvas.create_line(cx, cy, x_pointer, y_pointer, fill="red", width=3, arrow=tk.LAST)
    
    # Perbarui setiap 1 detik
    window.after(1000, update_gui)

# Membuat jendela utama
window = tk.Tk()
window.title("GUI Astrolab Real-Time")

# Frame untuk input lokasi
frame_input = tk.Frame(window)
frame_input.pack(pady=10)

tk.Label(frame_input, text="Latitude:").grid(row=0, column=0, padx=5)
entry_lat = tk.Entry(frame_input, width=10)
entry_lat.grid(row=0, column=1, padx=5)
entry_lat.insert(0, " -6.2000")  # contoh: Jakarta

tk.Label(frame_input, text="Longitude:").grid(row=0, column=2, padx=5)
entry_lon = tk.Entry(frame_input, width=10)
entry_lon.grid(row=0, column=3, padx=5)
entry_lon.insert(0, "106.8166")  # contoh: Jakarta

# Canvas untuk menggambar dial astrolab
canvas = tk.Canvas(window, width=400, height=400, bg="white")
canvas.pack()

# Label status untuk menampilkan waktu dan posisi benda langit
status_label = tk.Label(window, text="Memperbarui...", font=("Arial", 10))
status_label.pack(pady=5)

# Mulai update GUI
update_gui()

# Menjalankan aplikasi
window.mainloop()
