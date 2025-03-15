import sys
print("Interpreter:", sys.executable)
print("Sys.path:", sys.path)

import tkinter as tk
import datetime
import math
import ephem
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# -------------------------------
# Fungsi Perhitungan Objek Langit
# -------------------------------

def hitung_posisi_matahari(lat, lon):
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = datetime.datetime.utcnow()
    matahari = ephem.Sun(observer)
    az = float(matahari.az)  # dalam radian
    alt = float(matahari.alt)  # dalam radian
    return az, alt

def hitung_posisi_bulan(lat, lon):
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = datetime.datetime.utcnow()
    bulan = ephem.Moon(observer)
    az = float(bulan.az)
    alt = float(bulan.alt)
    fase = bulan.moon_phase  # antara 0 (bulan baru) hingga 1 (purnama)
    return az, alt, fase

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
    except Exception:
        terbit_local = terbenam_local = "N/A"
    return terbit_local, terbenam_local

def polar_to_cartesian(angle, radius, cx, cy):
    # Konversi koordinat polar ke kartesian untuk dial 2D
    x = cx + radius * math.cos(angle)
    y = cy - radius * math.sin(angle)
    return x, y

# -------------------------------
# Fungsi Peta Langit 3D dengan Matplotlib
# -------------------------------

def update_star_map():
    ax.clear()
    
    # Buat grid untuk permukaan bola dengan parameter u dan v
    u = np.linspace(0, np.pi, 50)
    v = np.linspace(0, 2*np.pi, 50)
    # Koordinat bola (dengan z sebagai vertikal)
    x = np.outer(np.sin(u), np.cos(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.cos(u), np.ones_like(v))
    
    # Tentukan warna: jika z >= 0, dianggap bagian langit (biru); jika z < 0, bagian bumi (coklat)
    colors = np.empty(x.shape, dtype=object)
    colors[z >= 0] = 'skyblue'
    colors[z < 0] = 'saddlebrown'
    
    # Plot permukaan bola dengan warna sesuai dan transparansi agar marker terlihat
    ax.plot_surface(x, y, z, facecolors=colors, rstride=1, cstride=1, alpha=0.5, linewidth=0)
    
    # Hilangkan label sumbu untuk tampilan yang bersih
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_zlim([-1, 1])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.set_box_aspect([1,1,1])
    
    # Dapatkan posisi Matahari dan Bulan dalam koordinat alt-az (sistem lokal)
    try:
        lat = float(entry_lat.get())
        lon = float(entry_lon.get())
    except ValueError:
        return

    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = datetime.datetime.utcnow()
    
    sun = ephem.Sun(observer)
    moon = ephem.Moon(observer)
    
    # Gunakan nilai altitude (alt) dan azimuth (az) untuk mengonversi ke koordinat kartesian
    sun_az, sun_alt = float(sun.az), float(sun.alt)
    x_sun = math.cos(sun_alt) * math.cos(sun_az)
    y_sun = math.cos(sun_alt) * math.sin(sun_az)
    z_sun = math.sin(sun_alt)
    
    moon_az, moon_alt = float(moon.az), float(moon.alt)
    x_moon = math.cos(moon_alt) * math.cos(moon_az)
    y_moon = math.cos(moon_alt) * math.sin(moon_az)
    z_moon = math.sin(moon_alt)
    
    # Plot Matahari dan Bulan pada peta 3D
    ax.scatter([x_sun], [y_sun], [z_sun], color='red', s=100, label='Matahari')
    ax.scatter([x_moon], [y_moon], [z_moon], color='blue', s=100, label='Bulan')
    
    ax.legend(loc='upper right')
    star_canvas.draw()

# -------------------------------
# Fungsi Update GUI Utama
# -------------------------------

def update_gui():
    try:
        lat = float(entry_lat.get())
        lon = float(entry_lon.get())
    except ValueError:
        status_label.config(text="Masukkan latitude dan longitude yang valid!")
        window.after(1000, update_gui)
        return

    # Hitung posisi Matahari dan Bulan dalam sistem 2D (dial astrolab)
    az, alt = hitung_posisi_matahari(lat, lon)
    az_bulan, alt_bulan, fase_bulan = hitung_posisi_bulan(lat, lon)
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

    # Update dial astrolab 2D pada canvas
    canvas.delete("all")
    cx, cy = 200, 200  # pusat dial
    radius = 150
    canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, outline="black", width=2)

    # Gambar garis arah tiap 30 derajat
    for deg in range(0, 360, 30):
        rad = math.radians(deg)
        x_end, y_end = polar_to_cartesian(rad, radius, cx, cy)
        canvas.create_line(cx, cy, x_end, y_end, fill="gray", dash=(2,2))
        x_label, y_label = polar_to_cartesian(rad, radius+15, cx, cy)
        canvas.create_text(x_label, y_label, text=f"{deg}°", font=("Arial", 8))
    
    # Gambar pointer Matahari (merah) dengan keterangan
    pointer_length = radius * 0.9
    x_pointer, y_pointer = polar_to_cartesian(az, pointer_length, cx, cy)
    canvas.create_line(cx, cy, x_pointer, y_pointer, fill="red", width=3, arrow=tk.LAST)
    canvas.create_text(x_pointer, y_pointer, text="Matahari", fill="red", anchor=tk.SW, font=("Arial", 8))
    
    # Gambar pointer Bulan (biru) dengan keterangan
    x_pointer_bulan, y_pointer_bulan = polar_to_cartesian(az_bulan, pointer_length * 0.8, cx, cy)
    canvas.create_line(cx, cy, x_pointer_bulan, y_pointer_bulan, fill="blue", width=3, arrow=tk.LAST)
    canvas.create_text(x_pointer_bulan, y_pointer_bulan, text="Bulan", fill="blue", anchor=tk.SE, font=("Arial", 8))
    
    # Update peta langit 3D
    update_star_map()
    
    window.after(1000, update_gui)

# -------------------------------
# Pembuatan GUI dengan Tkinter (Layout Horizontal)
# -------------------------------

window = tk.Tk()
window.title("GUI Astrolab Real-Time")

# Frame untuk input lokasi
frame_input = tk.Frame(window)
frame_input.grid(row=0, column=0, columnspan=2, pady=10)

tk.Label(frame_input, text="Latitude:").grid(row=0, column=0, padx=5)
entry_lat = tk.Entry(frame_input, width=10)
entry_lat.grid(row=0, column=1, padx=5)
entry_lat.insert(0, "-6.2000")  # contoh: Jakarta

tk.Label(frame_input, text="Longitude:").grid(row=0, column=2, padx=5)
entry_lon = tk.Entry(frame_input, width=10)
entry_lon.grid(row=0, column=3, padx=5)
entry_lon.insert(0, "106.8166")  # contoh: Jakarta

# Frame utama yang menampung dial 2D dan peta 3D secara horizontal
frame_main = tk.Frame(window)
frame_main.grid(row=1, column=0, columnspan=2)

# Frame untuk dial astrolab 2D
frame_dial = tk.Frame(frame_main)
frame_dial.grid(row=0, column=0, padx=10, pady=10)
canvas = tk.Canvas(frame_dial, width=400, height=400, bg="white")
canvas.pack()

# Frame untuk peta langit 3D
frame_star_map = tk.Frame(frame_main)
frame_star_map.grid(row=0, column=1, padx=10, pady=10)
fig = Figure(figsize=(5, 5))
ax = fig.add_subplot(111, projection='3d')
star_canvas = FigureCanvasTkAgg(fig, master=frame_star_map)
star_canvas.get_tk_widget().pack()

# Label status untuk informasi posisi dan waktu
status_label = tk.Label(window, text="Memperbarui...", font=("Arial", 10))
status_label.grid(row=2, column=0, columnspan=2, pady=5)

update_gui()
window.mainloop()
