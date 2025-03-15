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
import geocoder  # Untuk mendapatkan lokasi terkini

# -------------------------------
# Fungsi untuk mendapatkan lokasi terkini
# -------------------------------
def get_current_location():
    try:
        g = geocoder.ip('me')
        if g.ok and g.latlng:
            return g.latlng[0], g.latlng[1]
    except Exception as e:
        print("Gagal mendapatkan lokasi:", e)
    return None, None

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
    
    # Buat grid untuk permukaan bola
    u = np.linspace(0, np.pi, 50)
    v = np.linspace(0, 2*np.pi, 50)
    x = np.outer(np.sin(u), np.cos(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.cos(u), np.ones_like(v))
    
    # Warna: bagian atas (z>=0) = langit (biru), bagian bawah (z<0) = bumi (coklat)
    colors = np.empty(x.shape, dtype=object)
    colors[z >= 0] = 'skyblue'
    colors[z < 0] = 'saddlebrown'
    
    ax.plot_surface(x, y, z, facecolors=colors, rstride=1, cstride=1, alpha=0.5, linewidth=0)
    
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_zlim([-1, 1])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.set_box_aspect([1,1,1])
    
    # Tambahkan label arah: Utara, Selatan, Barat, Timur
    ax.text(0, 1.05, 0, "T", color="k", fontsize=10, ha="center", fontname="Lucida Console")
    ax.text(0, -1.05, 0, "B", color="k", fontsize=10, ha="center", fontname="Lucida Console")
    ax.text(1.05, 0, 0, "S", color="k", fontsize=10, va="center", fontname="Lucida Console")
    ax.text(-1.05, 0, 0, "U", color="k", fontsize=10, va="center", fontname="Lucida Console")
    
    # Dapatkan posisi Matahari dan Bulan (sistem lokal: alt-azimuth)
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
    
    # Koordinat Matahari
    sun_az, sun_alt = float(sun.az), float(sun.alt)
    x_sun = math.cos(sun_alt) * math.cos(sun_az)
    y_sun = math.cos(sun_alt) * math.sin(sun_az)
    z_sun = math.sin(sun_alt)
    
    # Koordinat Bulan
    moon_az, moon_alt = float(moon.az), float(moon.alt)
    x_moon = math.cos(moon_alt) * math.cos(moon_az)
    y_moon = math.cos(moon_alt) * math.sin(moon_az)
    z_moon = math.sin(moon_alt)
    
    ax.scatter([x_sun], [y_sun], [z_sun], color='red', s=100, label='Matahari')
    ax.scatter([x_moon], [y_moon], [z_moon], color='blue', s=100, label='Bulan')
    
    # Tambahkan rasi bintang dengan marker segitiga
    constellations = {
        "Orion": {"coords": (83.8, -5.9), "color": "darkorange"},
        "Ursa Major": {"coords": (165.0, 56.0), "color": "indigo"},
        "Ursa Minor": {"coords": (150.0, 75.0), "color": "green"},
        "Crux": {"coords": (186.0, -63.0), "color": "magenta"},
        "Canis Major": {"coords": (101.0, -17.0), "color": "cyan"},
        "Taurus": {"coords": (65.0, 16.0), "color": "sienna"},
        "Scorpius": {"coords": (247.0, -26.0), "color": "firebrick"},
        "Sagittarius": {"coords": (266.0, -29.0), "color": "gold"},
        "Capricornus": {"coords": (340.0, -20.0), "color": "teal"},
        "Leo": {"coords": (170.0, 12.0), "color": "navy"}
    }
    
    for name, data in constellations.items():
        ra_deg, dec_deg = data["coords"]
        color = data["color"]
        # Buat FixedBody agar posisinya di-update oleh observer
        body = ephem.FixedBody()
        body._ra = math.radians(ra_deg)
        body._dec = math.radians(dec_deg)
        body.compute(observer)
        # Dapatkan alt dan az dari body (sistem lokal)
        alt_local = float(body.alt)
        az_local = float(body.az)
        # Konversi ke koordinat kartesian (unit sphere)
        x_star = math.cos(alt_local) * math.cos(az_local)
        y_star = math.cos(alt_local) * math.sin(az_local)
        z_star = math.sin(alt_local)
        ax.scatter([x_star], [y_star], [z_star], color=color, s=50, marker='^')
        ax.text(x_star, y_star, z_star, f" {name}", color=color, fontsize=8, fontname="Lucida Console")
    
    ax.legend(loc='upper right', prop={"family": "Lucida Console", "size": 10})
    star_canvas.draw()

# -------------------------------
# Fungsi Update GUI Utama
# -------------------------------
def update_gui():
    try:
        lat = float(entry_lat.get())
        lon = float(entry_lon.get())
    except ValueError:
        status_label.config(text="Masukkan latitude dan longitude yang valid!", font=("Lucida Console", 10))
        window.after(1000, update_gui)
        return

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
    status_label.config(text=status_text, font=("Lucida Console", 10))

    # Update label waktu dan info terbit/tenggelam di pojok kiri bawah
    label_time.config(text=f"Waktu Lokal: {now}", font=("Lucida Console", 10))
    label_sun.config(
        text=(
            f"Matahari Terbit: {terbit if isinstance(terbit, str) else terbit.strftime('%H:%M:%S')} | "
            f"Matahari Tenggelam: {terbenam if isinstance(terbenam, str) else terbenam.strftime('%H:%M:%S')}"
        ),
        font=("Lucida Console", 10)
    )
    
    # Update dial astrolab 2D
    canvas.delete("all")
    cx, cy = 250, 250
    radius = 170
    canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline="black", width=2)
    for deg in range(0, 360, 30):
        rad = math.radians(deg)
        x_end, y_end = polar_to_cartesian(rad, radius, cx, cy)
        canvas.create_line(cx, cy, x_end, y_end, fill="gray", dash=(2,2))
        x_label, y_label = polar_to_cartesian(rad, radius + 15, cx, cy)
        canvas.create_text(x_label, y_label, text=f"{deg}°", font=("Lucida Console", 8))

    # Pointer Matahari
    pointer_length = radius * 0.9
    x_pointer, y_pointer = polar_to_cartesian(az, pointer_length, cx, cy)
    canvas.create_line(cx, cy, x_pointer, y_pointer, fill="red", width=3, arrow=tk.LAST)
    canvas.create_text(x_pointer, y_pointer, text="Matahari", fill="red", anchor=tk.SW, font=("Lucida Console", 8))

    # Pointer Bulan
    x_pointer_bulan, y_pointer_bulan = polar_to_cartesian(az_bulan, pointer_length * 0.8, cx, cy)
    canvas.create_line(cx, cy, x_pointer_bulan, y_pointer_bulan, fill="blue", width=3, arrow=tk.LAST)
    canvas.create_text(x_pointer_bulan, y_pointer_bulan, text="Bulan", fill="blue", anchor=tk.SE, font=("Lucida Console", 8))
    
    # Update peta langit 3D
    update_star_map()

    # Perbarui setiap 1 detik
    window.after(1000, update_gui)

# -------------------------------
# Pembuatan GUI dengan Tkinter (Layout Responsif)
# -------------------------------
window = tk.Tk()
window.title("Si-DiAs: Simple Digital Astrolab")

# Atur ukuran jendela berdasarkan layar pengguna
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
window.geometry(f"{screen_width}x{screen_height}")

# Opsional: Aktifkan mode fullscreen
#window.attributes('-fullscreen', True)

# Konfigurasi grid pada jendela utama agar responsif
window.rowconfigure(0, weight=0)  # frame input
window.rowconfigure(1, weight=0)  # frame info
window.rowconfigure(2, weight=1)  # frame utama (isi)
window.rowconfigure(3, weight=0)  # label status
window.rowconfigure(4, weight=0)  # frame koordinat bintang

window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=1)

# Frame untuk input lokasi
frame_input = tk.Frame(window)
frame_input.grid(row=0, column=0, columnspan=2, sticky="ew", pady=10)
for i in range(4):
    frame_input.columnconfigure(i, weight=1)

tk.Label(frame_input, text="Latitude:", font=("Lucida Console", 10)).grid(row=0, column=0, padx=5, sticky="e")
entry_lat = tk.Entry(frame_input, width=10, font=("Lucida Console", 10))
entry_lat.grid(row=0, column=1, padx=5, sticky="w")

tk.Label(frame_input, text="Longitude:", font=("Lucida Console", 10)).grid(row=0, column=2, padx=5, sticky="e")
entry_lon = tk.Entry(frame_input, width=10, font=("Lucida Console", 10))
entry_lon.grid(row=0, column=3, padx=5, sticky="w")

# Auto-populasi lokasi jika memungkinkan
lat_curr, lon_curr = get_current_location()
if lat_curr is not None and lon_curr is not None:
    entry_lat.insert(0, f"{lat_curr:.4f}")
    entry_lon.insert(0, f"{lon_curr:.4f}")
else:
    entry_lat.insert(0, "-6.2000")
    entry_lon.insert(0, "106.8166")

# Frame untuk informasi waktu dan Matahari terbit/tenggelam (pojok kiri bawah)
frame_info = tk.Frame(window)
frame_info.grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
frame_info.columnconfigure(0, weight=1)

label_time = tk.Label(frame_info, text="Waktu Lokal: ", font=("Lucida Console", 10))
label_time.grid(row=0, column=0, padx=5, sticky="w")
label_sun = tk.Label(frame_info, text="Matahari Terbit: ... | Matahari Tenggelam: ...", font=("Lucida Console", 10))
label_sun.grid(row=1, column=0, padx=5, sticky="w")

# Frame utama untuk dial 2D dan peta langit 3D secara horizontal
frame_main = tk.Frame(window)
frame_main.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
frame_main.rowconfigure(0, weight=1)
frame_main.columnconfigure(0, weight=1)
frame_main.columnconfigure(1, weight=1)

# Frame dial astrolab 2D
frame_dial = tk.Frame(frame_main)
frame_dial.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
frame_dial.rowconfigure(0, weight=1)
frame_dial.columnconfigure(0, weight=1)
canvas = tk.Canvas(frame_dial, bg="white")
canvas.grid(row=0, column=0, sticky="nsew")

# Frame peta langit 3D
frame_star_map = tk.Frame(frame_main)
frame_star_map.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
frame_star_map.rowconfigure(0, weight=1)
frame_star_map.columnconfigure(0, weight=1)
fig = Figure(figsize=(6, 6))
ax = fig.add_subplot(111, projection='3d')
star_canvas = FigureCanvasTkAgg(fig, master=frame_star_map)
star_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

# Frame untuk judul & copyright (pojok kanan bawah)
frame_footer = tk.Frame(window)
frame_footer.grid(row=5, column=0, columnspan=2, sticky="e", padx=10, pady=5)
label_title = tk.Label(frame_footer, text="Si-DiAs: Simple Digital Astrolab", font=("Lucida Console", 12, "bold"))
label_title.pack(side="top")
label_copy = tk.Label(frame_footer, text="© 2025 Gilang Pratama PS & Najlah Rupaidah", font=("Lucida Console", 10))
label_copy.pack(side="bottom", padx=(10,10))

# Label status untuk informasi tambahan (jika diperlukan)
status_label = tk.Label(window, text="Memperbarui...", font=("Lucida Console", 10))
status_label.grid(row=3, column=0, columnspan=2, pady=5)

update_gui()
window.mainloop()
