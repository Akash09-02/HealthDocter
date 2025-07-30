import tkinter as tk
from tkinter import messagebox, filedialog
from plyer import notification
import threading
import time
import cv2
import mysql.connector
from datetime import datetime
import subprocess
from PIL import Image, ImageTk
import io
import pygame
import math
import os
import sys

# ==== Resource Path for .exe compatibility ====
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # for PyInstaller
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ==== Global flags ====
running = True
sound_playing = False
profile_data = {'name': '', 'mobile': '', 'photo': None}

# ==== Initialize pygame ====
pygame.mixer.init()

# ==== MySQL Connection ====
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="HealthDoctor"
)
cursor = conn.cursor()

# ==== MP3 Play ====
def play_mp3_loop():
    try:
        path = resource_path("sound/Ak.mp3")
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(loops=-1)
    except Exception as e:
        print(f"MP3 Error: {e}")

def stop_mp3():
    pygame.mixer.music.stop()

# ==== Webcam ====
def capture_photo():
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    img_bytes = None
    if ret:
        retval, buffer = cv2.imencode('.jpg', frame)
        img_bytes = buffer.tobytes()
    cam.release()
    return img_bytes

# ==== MySQL Insert ====
def insert_into_mysql(image_data):
    now = datetime.now()
    query = "INSERT INTO water_reminders (user_id, timestamp, status, image, name, mobile) VALUES (%s, %s, %s, %s, %s, %s)"
    values = ("user_akash", now, "pani pilya", image_data, profile_data['name'], profile_data['mobile'])
    cursor.execute(query, values)
    conn.commit()

# ==== Reminder loop (repeats!) ====
def reminder_loop(interval):
    global sound_playing
    while running:
        time.sleep(interval)

        if not running:
            break

        notification.notify(
            title="💧 पाणी प्या!",
            message="उठा उट्टा, बेल आली — पाणी पिण्याची वेळ झाली!",
            timeout=5
        )

        sound_playing = True
        threading.Thread(target=play_mp3_loop, daemon=True).start()

        result = messagebox.askyesno("पाणी प्या!", "पाणी पिताना फोटो घेण्यात येइल. तयार आहात का?")
        stop_mp3()

        if result and running:
            image_bytes = capture_photo()
            insert_into_mysql(image_bytes)
            messagebox.showinfo("धन्यवाद!", "फोटो सेव्ह झाला.")
        elif running:
            messagebox.showinfo("सूचना", "तुम्ही पाणी पिलं नाही.")

        sound_playing = False

# ==== GUI ====
root = tk.Tk()
root.title("💧 पाणी प्या रिमाइंडर")
root.geometry("500x560")
root.configure(bg="#f0f0f0")

# Stylish Buttons
def styled_button(master, text, command, bg, fg, hover_bg, font=("Arial", 12), pady=5):
    btn = tk.Button(master, text=text, command=command, font=font, bg=bg, fg=fg,
                    activebackground=hover_bg, relief="flat", padx=10, pady=6)
    btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn

# Time Inputs
time_frame = tk.Frame(root, bg="#f0f0f0")
time_frame.pack(pady=10)
tk.Label(time_frame, text="Interval:", font=("Arial", 12), bg="#f0f0f0").grid(row=0, column=0)
hour_entry = tk.Entry(time_frame, width=3)
hour_entry.grid(row=0, column=1)
tk.Label(time_frame, text="h", bg="#f0f0f0").grid(row=0, column=2)
min_entry = tk.Entry(time_frame, width=3)
min_entry.grid(row=0, column=3)
tk.Label(time_frame, text="m", bg="#f0f0f0").grid(row=0, column=4)
sec_entry = tk.Entry(time_frame, width=3)
sec_entry.grid(row=0, column=5)
tk.Label(time_frame, text="s", bg="#f0f0f0").grid(row=0, column=6)

# Profile Frame
profile_frame = tk.LabelFrame(root, text="👤 प्रोफाइल", padx=10, pady=10, bg="#ffffff", font=("Arial", 10, "bold"), fg="#333")
profile_frame.pack(pady=10)

photo_label = tk.Label(profile_frame, width=80, height=80, bg="gray")
photo_label.grid(row=0, column=0, rowspan=3, padx=10)

tk.Button(profile_frame, text="📸 फोटो", command=lambda: upload_photo()).grid(row=0, column=1)
tk.Label(profile_frame, text="नाव:", bg="#ffffff").grid(row=1, column=1, sticky='w')
name_entry = tk.Entry(profile_frame, width=25)
name_entry.grid(row=2, column=1)
tk.Label(profile_frame, text="📱 मोबाइल:", bg="#ffffff").grid(row=3, column=0, columnspan=2, sticky='w')
mobile_entry = tk.Entry(profile_frame, width=25)
mobile_entry.grid(row=4, column=0, columnspan=2)
tk.Button(profile_frame, text="💾 Save", command=lambda: save_profile()).grid(row=5, column=0, columnspan=2, pady=5)

# Dashboard
def open_dashboard():
    try:
        exe_path = os.path.join(os.path.dirname(sys.executable), "Dashboard.exe")
        if os.path.exists(exe_path):
            subprocess.Popen([exe_path])
        else:
            messagebox.showerror("त्रुटी", "Dashboard.exe सापडत नाही! कृपया Dashboard.exe HealthCare.exe च्या फोल्डरमध्ये ठेवा.")
    except Exception as e:
        messagebox.showerror("त्रुटी", f"Dashboard.exe सुरू होत नाही: {e}")



# Upload Photo
def upload_photo():
    path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png")])
    if path:
        profile_data['photo'] = path
        img = Image.open(path).resize((80, 80))
        photo = ImageTk.PhotoImage(img)
        photo_label.config(image=photo)
        photo_label.image = photo

# Save Profile
def save_profile():
    profile_data['name'] = name_entry.get()
    profile_data['mobile'] = mobile_entry.get()
    if profile_data['photo']:
        with open(profile_data['photo'], 'rb') as f:
            photo_blob = f.read()
    else:
        photo_blob = None

    cursor.execute("SELECT id FROM user_profile LIMIT 1")
    existing = cursor.fetchone()
    if existing:
        cursor.execute("UPDATE user_profile SET name=%s, mobile=%s, photo=%s WHERE id=%s",
                       (profile_data['name'], profile_data['mobile'], photo_blob, existing[0]))
    else:
        cursor.execute("INSERT INTO user_profile (name, mobile, photo) VALUES (%s, %s, %s)",
                       (profile_data['name'], profile_data['mobile'], photo_blob))
    conn.commit()
    messagebox.showinfo("सेव्ह", "प्रोफाइल माहिती सेव्ह झाली!")

# Load Profile
def load_profile():
    cursor.execute("SELECT name, mobile, photo FROM user_profile LIMIT 1")
    row = cursor.fetchone()
    if row:
        profile_data['name'], profile_data['mobile'], photo_blob = row
        name_entry.insert(0, profile_data['name'])
        mobile_entry.insert(0, profile_data['mobile'])
        if photo_blob:
            img = Image.open(io.BytesIO(photo_blob)).resize((80, 80))
            photo = ImageTk.PhotoImage(img)
            photo_label.config(image=photo)
            photo_label.image = photo

# Reminder Control
def start_reminder():
    try:
        hrs = int(hour_entry.get() or 0)
        mins = int(min_entry.get() or 0)
        secs = int(sec_entry.get() or 0)
        interval = hrs * 3600 + mins * 60 + secs
        if interval <= 0:
            raise ValueError
        global running
        running = True
        threading.Thread(target=reminder_loop, args=(interval,), daemon=True).start()
        messagebox.showinfo("सुरू", f"प्रत्येक {hrs}h {mins}m {secs}s ने स्मरण येइल.")
    except ValueError:
        messagebox.showerror("चूक", "कृपया वैध वेळ द्या.")

def stop_reminder():
    global running, sound_playing
    running = False
    sound_playing = False
    stop_mp3()
    messagebox.showinfo("बंद", "स्मरण बंद करण्यात आले.")

def exit_app():
    global running, sound_playing
    running = False
    sound_playing = False
    stop_mp3()
    root.destroy()

    # ==== Analog Watch Setup ====
canvas = tk.Canvas(root, width=130, height=130, bg="white", highlightthickness=1)
canvas.place(x=355, y=5)
center_x, center_y = 65, 65
radius = 55
sec_hand = 50
min_hand = 40
hr_hand = 30

canvas.create_oval(center_x - radius, center_y - radius, center_x + radius, center_y + radius, outline="black", width=2)

def update_watch():
    canvas.delete("hands")
    now = datetime.now()
    sec = now.second
    min = now.minute
    hr = now.hour % 12 + min / 60.0

    sec_angle = math.radians(sec * 6 - 90)
    min_angle = math.radians(min * 6 - 90)
    hr_angle = math.radians(hr * 30 - 90)

    sec_x = center_x + sec_hand * math.cos(sec_angle)
    sec_y = center_y + sec_hand * math.sin(sec_angle)
    canvas.create_line(center_x, center_y, sec_x, sec_y, fill="red", width=1, tags="hands")

    min_x = center_x + min_hand * math.cos(min_angle)
    min_y = center_y + min_hand * math.sin(min_angle)
    canvas.create_line(center_x, center_y, min_x, min_y, fill="blue", width=2, tags="hands")

    hr_x = center_x + hr_hand * math.cos(hr_angle)
    hr_y = center_y + hr_hand * math.sin(hr_angle)
    canvas.create_line(center_x, center_y, hr_x, hr_y, fill="black", width=3, tags="hands")

    for i in range(1, 13):
        angle = math.radians(i * 30 - 90)
        x = center_x + (radius - 12) * math.cos(angle)
        y = center_y + (radius - 12) * math.sin(angle)
        canvas.create_text(x, y, text=str(i), font=("Arial", 8, "bold"), tags="hands")

    root.after(1000, update_watch)

# Start watch
update_watch()


# Buttons
btn_frame = tk.Frame(root, bg="#f0f0f0")
btn_frame.pack(pady=10)
styled_button(btn_frame, "▶️ सुरू करा", start_reminder, "green", "white", "#28a745").pack(pady=6)
styled_button(btn_frame, "⛔ OFF करा", stop_reminder, "red", "white", "#c82333").pack(pady=6)
styled_button(btn_frame, "📊 Dashboard", open_dashboard, "#007bff", "white", "#0056b3").pack(pady=6)
styled_button(btn_frame, "🚪 Exit", exit_app, "#6c757d", "white", "#5a6268").pack(pady=6)

load_profile()
root.mainloop()
