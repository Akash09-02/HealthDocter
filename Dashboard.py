import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import mysql.connector
import io
import smtplib
from email.message import EmailMessage
from fpdf import FPDF
from datetime import datetime, timedelta
import threading
import matplotlib.pyplot as plt
import os
import time
import csv

# ✅ MySQL Connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="HealthDoctor"
)
cursor = conn.cursor()

# ✅ GUI Setup
root = tk.Tk()
root.title("Dashboard - पाणी प्या")
root.geometry("1000x800")

# ============================ PROFILE ============================
profile_frame = tk.LabelFrame(root, text="प्रोफाइल", font=("Arial", 12))
profile_frame.pack(pady=10, fill="x")

cursor.execute("SELECT name, mobile, photo FROM user_profile ORDER BY id DESC LIMIT 1")
row = cursor.fetchone()

if row:
    name, mobile, photo_blob = row
    profile_text = f"👤 नाव: {name}     📞 मोबाइल: {mobile}"
    profile_label = tk.Label(profile_frame, text=profile_text, font=("Arial", 12))
    profile_label.pack(side=tk.LEFT, padx=20)

    img = Image.open(io.BytesIO(photo_blob))
    img = img.resize((60, 60))
    photo = ImageTk.PhotoImage(img)
    img_label = tk.Label(profile_frame, image=photo)
    img_label.image = photo
    img_label.pack(side=tk.RIGHT, padx=20)

# ============================ TABLE ============================
columns = ("ID", "Time", "Status")
tree = ttk.Treeview(root, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
tree.pack(fill=tk.BOTH, expand=True, pady=10)

def load_table():
    for item in tree.get_children():
        tree.delete(item)
    cursor.execute("SELECT id, timestamp, status FROM water_reminders ORDER BY timestamp DESC")
    data = cursor.fetchall()
    for row in data:
        tree.insert("", tk.END, values=row)

load_table()

# ============================ IMAGE PREVIEW ============================
image_label = tk.Label(root)
image_label.pack(pady=10)
info_label = tk.Label(root, text="", font=("Arial", 12))
info_label.pack()

def on_select(event):
    selected = tree.selection()
    if selected:
        entry_id = tree.item(selected[0])['values'][0]
        cursor.execute("SELECT timestamp, status, image FROM water_reminders WHERE id=%s", (entry_id,))
        row = cursor.fetchone()
        if row:
            ts, status, blob = row
            info_label.config(text=f"🕒 वेळ: {ts}\n📌 Status: {status}")
            img = Image.open(io.BytesIO(blob))
            img = img.resize((300, 300))
            img = ImageTk.PhotoImage(img)
            image_label.config(image=img)
            image_label.image = img

tree.bind("<<TreeviewSelect>>", on_select)

# ============================ EMAIL ============================
email_frame = tk.Frame(root)
email_frame.pack(pady=10)

tk.Label(email_frame, text="Report Email: ", font=("Arial", 10)).pack(side=tk.LEFT)
email_entry = tk.Entry(email_frame, width=30, font=("Arial", 10))
email_entry.pack(side=tk.LEFT, padx=5)
saved_email = ""

def save_email():
    global saved_email
    saved_email = email_entry.get()
    if saved_email:
        messagebox.showinfo("Email", f"Email जतन झाला: {saved_email}")
    else:
        messagebox.showerror("Error", "कृपया Email टाका")

save_btn = tk.Button(email_frame, text="📂 Save", command=save_email, bg="orange", fg="white")
save_btn.pack(side=tk.LEFT, padx=5)

# ============================ CHART ============================
def generate_chart(data):
    dates = [row[0].strftime("%d-%m") for row in data]
    counts = list(range(1, len(dates) + 1))
    plt.figure(figsize=(6, 3))
    plt.plot(dates, counts, marker='o', color='blue')
    plt.title("पाण्याचंया सेवन विश्लेषण")
    plt.xlabel("Date")
    plt.ylabel("Reminder Count")
    plt.xticks(rotation=45)
    plt.tight_layout()
    path = "chart.png"
    plt.savefig(path)
    plt.close()
    return path

# ============================ PDF ============================
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Health Report - Last 10 Days", ln=1, align="C")
    pdf.ln(10)

    ten_days_ago = datetime.now() - timedelta(days=10)
    cursor.execute("SELECT timestamp, status, image FROM water_reminders WHERE timestamp >= %s ORDER BY timestamp DESC", (ten_days_ago,))
    report_data = cursor.fetchall()

    for i, (ts, status, blob) in enumerate(report_data):
        pdf.cell(200, 10, txt=f"{ts} - {status}", ln=1)
        img_path = f"img_temp_{i}.jpg"
        with open(img_path, 'wb') as f:
            f.write(blob)
        pdf.image(img_path, x=10, y=pdf.get_y(), w=60)
        pdf.ln(65)
        os.remove(img_path)

    chart = generate_chart(report_data)
    if os.path.exists(chart):
        pdf.image(chart, x=10, y=pdf.get_y(), w=180)

    filename = "health_report.pdf"
    pdf.output(filename)
    return filename

# ============================ EMAIL SEND ============================
EMAIL_ADDRESS = "akashjadhav9136@gmail.com"
EMAIL_PASSWORD = "xwjt mntz alrc gpvt"

def send_email_report():
    recipient = saved_email or email_entry.get()
    if not recipient:
        messagebox.showerror("Error", "कृपया Email टाका")
        return

    filename = generate_pdf()

    try:
        msg = EmailMessage()
        msg['Subject'] = 'Health Report - Last 10 Days'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient
        msg.set_content('Please find your health report with analysis attached.')

        with open(filename, 'rb') as f:
            msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=filename)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        messagebox.showinfo("Success", "Report पाठवला गेला!")
    except Exception as e:
        messagebox.showerror("Error", f"Report पाठवता आला नाही: {e}")

# ============================ SAVE PDF ============================
def save_pdf_local():
    filename = generate_pdf()
    messagebox.showinfo("Saved", f"PDF Saved as {filename}")

# ============================ EXPORT CSV ============================
def export_csv():
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if path:
        cursor.execute("SELECT id, timestamp, status FROM water_reminders ORDER BY timestamp DESC")
        data = cursor.fetchall()
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Timestamp', 'Status'])
            writer.writerows(data)
        messagebox.showinfo("Export", f"CSV फाइल सेव्ह झाली: {path}")

# ============================ FILTER BY DATE ============================
def filter_by_date():
    date_str = date_entry.get()
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        cursor.execute("SELECT id, timestamp, status FROM water_reminders WHERE DATE(timestamp) = %s ORDER BY timestamp DESC", (selected_date,))
        data = cursor.fetchall()
        for item in tree.get_children():
            tree.delete(item)
        for row in data:
            tree.insert("", tk.END, values=row)
    except ValueError:
        messagebox.showerror("Error", "कृपया दिनांक योग्य फॉरमॅटमध्ये द्या (YYYY-MM-DD)")

# ============================ BUTTONS ============================
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

send_btn = tk.Button(btn_frame, text="📧 Send Email", command=send_email_report, bg="green", fg="white")
send_btn.pack(side=tk.LEFT, padx=10)

save_btn = tk.Button(btn_frame, text="📄 Save PDF Locally", command=save_pdf_local, bg="blue", fg="white")
save_btn.pack(side=tk.LEFT, padx=10)

csv_btn = tk.Button(btn_frame, text="📤 Export CSV", command=export_csv, bg="purple", fg="white")
csv_btn.pack(side=tk.LEFT, padx=10)

# ============================ DATE FILTER ============================
date_frame = tk.Frame(root)
date_frame.pack(pady=5)

tk.Label(date_frame, text="🔍 Filter Date (YYYY-MM-DD):", font=("Arial", 10)).pack(side=tk.LEFT)
date_entry = tk.Entry(date_frame, width=15, font=("Arial", 10))
date_entry.pack(side=tk.LEFT, padx=5)
filter_btn = tk.Button(date_frame, text="🔍 Filter", command=filter_by_date, bg="gray", fg="white")
filter_btn.pack(side=tk.LEFT)

# ============================ AUTO EMAIL ============================
def schedule_email():
    while True:
        time.sleep(10 * 24 * 60 * 60)
        send_email_report()

th = threading.Thread(target=schedule_email, daemon=True)
th.start()

root.mainloop()