from flask import Flask, render_template, request, jsonify, redirect
import sqlite3
import os
import time
import json
import threading
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from urllib.parse import unquote

import schedule
import smtplib
from email.message import EmailMessage
from openai import OpenAI

# ================= APP CONFIG =================
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = "reminders.db"
AUDIO_FOLDER = "static/audio"

if not os.path.isdir(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

# ================= CREDENTIALS & CLIENTS =================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD")

client = None
if OPENAI_API_KEY and OPENAI_API_KEY != "YOUR_OPENAI_API_KEY":
    client = OpenAI(api_key=OPENAI_API_KEY)

# ================= DATABASE =================
def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            time TEXT,
            audio TEXT,
            bill_name TEXT,
            recurring INTEGER DEFAULT 0,
            sent INTEGER DEFAULT 0
        )
    """)

    for bill in ["Electricity", "Internet", "House Rent"]:
        cur.execute(
            "INSERT OR IGNORE INTO bills (name) VALUES (?)",
            (bill,)
        )

    conn.commit()
    conn.close()

# ================= AI HELPER =================
def ai_extract_reminder(text):
    if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_OPENAI_API_KEY" or not client:
        logger.info("OpenAI API key not configured or default; skipping AI extraction.")
        return {}

    prompt = f"""
Extract reminder information from the text.

Return ONLY valid JSON:
- message
- date (YYYY-MM-DD)
- time (HH:MM)

Text: "{text}"
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"AI reminder extraction failed: {e}")
        return {}

# ================= EMAIL =================
def send_email(text):
    if not SMTP_EMAIL or not SMTP_APP_PASSWORD or SMTP_EMAIL == "YOUR_EMAIL@gmail.com":
        logger.warning("SMTP credentials not configured; skipping email dispatch.")
        return

    msg = EmailMessage()
    msg.set_content(text)
    msg["Subject"] = "🔔 Reminder"
    msg["From"] = SMTP_EMAIL
    msg["To"] = SMTP_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
        server.send_message(msg)

# ================= SCHEDULER =================
def check_reminders():
    conn = get_db()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        cur.execute("""
            SELECT id, text, time, recurring
            FROM reminders
            WHERE sent = 0 OR recurring = 1
        """)

        reminders = cur.fetchall()

        for rid, text, reminder_time, recurring in reminders:
            if reminder_time and reminder_time[:16] == now:
                try:
                    send_email(text)
                except Exception as e:
                    logger.error(f"Failed to send email for reminder {rid}: {e}")

                if recurring:
                    dt = datetime.strptime(reminder_time, "%Y-%m-%d %H:%M")
                    month = dt.month + 1
                    year = dt.year
                    if month > 12:
                        month = 1
                        year += 1
                    try:
                        next_dt = dt.replace(year=year, month=month)
                    except ValueError:
                        next_dt = dt.replace(year=year, month=month, day=28)

                    cur.execute(
                        "UPDATE reminders SET time = ? WHERE id = ?",
                        (next_dt.strftime("%Y-%m-%d %H:%M"), rid)
                    )
                else:
                    cur.execute(
                        "UPDATE reminders SET sent = 1 WHERE id = ?",
                        (rid,)
                    )

                conn.commit()
    except Exception as e:
        logger.error(f"Error checking reminders: {e}")
    finally:
        conn.close()

def run_scheduler():
    schedule.every(1).minute.do(check_reminders)
    while True:
        schedule.run_pending()
        time.sleep(1)

# ================= ROUTES =================

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/recordings")
def recordings():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id, text, time, audio FROM reminders ORDER BY id DESC")
    reminders = cur.fetchall()

    cur.execute("SELECT name FROM bills")
    bills = [row[0] for row in cur.fetchall()]

    conn.close()

    return render_template(
        "recordings.html",
        reminders=reminders,
        bills=bills
    )

# ---------- SET BILL ----------
@app.route("/set-bill/<path:bill>")
def set_bill(bill):
    return render_template("set_bill.html", bill_name=unquote(bill))

@app.route("/save-bill", methods=["POST"])
def save_bill():
    bill_name = request.form.get("bill_name")
    day = int(request.form.get("day"))
    time_value = request.form.get("time")

    now = datetime.now()
    month = now.month
    year = now.year

    if day < now.day:
        month += 1
        if month > 12:
            month = 1
            year += 1

    reminder_time = f"{year}-{month:02d}-{day:02d} {time_value}"

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO reminders (text, time, bill_name, recurring)
        VALUES (?, ?, ?, 1)
        """,
        (f"{bill_name} Bill Reminder", reminder_time, bill_name)
    )
    conn.commit()
    conn.close()

    return redirect("/recordings")

# ---------- ADD BILL ----------
@app.route("/add-bill")
def add_bill():
    return render_template("add_bill.html")

@app.route("/add-bill", methods=["POST"])
def add_bill_post():
    bill_name = request.form.get("bill_name")
    day = int(request.form.get("day"))
    time_value = request.form.get("time")

    now = datetime.now()
    month = now.month
    year = now.year

    if day < now.day:
        month += 1
        if month > 12:
            month = 1
            year += 1

    reminder_time = f"{year}-{month:02d}-{day:02d} {time_value}"

    conn = get_db()
    cur = conn.cursor()

    cur.execute("INSERT OR IGNORE INTO bills (name) VALUES (?)", (bill_name,))
    cur.execute(
        """
        INSERT INTO reminders (text, time, bill_name, recurring)
        VALUES (?, ?, ?, 1)
        """,
        (f"{bill_name} Bill Reminder", reminder_time, bill_name)
    )

    conn.commit()
    conn.close()

    return redirect("/recordings")

# ---------- SAVE NORMAL REMINDER ----------
@app.route("/save", methods=["POST"])
def save():
    text = request.form.get("text")
    datetime_value = request.form.get("datetime")
    audio_file = request.files.get("audio")

    if not datetime_value:
        try:
            ai = ai_extract_reminder(text)
            text = ai.get("message", text)
            if ai.get("date") and ai.get("time"):
                datetime_value = f"{ai['date']} {ai['time']}"
        except:
            pass

    if datetime_value:
        datetime_value = datetime_value.replace("T", " ")

    audio_filename = None
    if audio_file:
        audio_filename = secure_filename(f"{int(time.time())}.webm")
        audio_file.save(os.path.join(AUDIO_FOLDER, audio_filename))

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reminders (text, time, audio) VALUES (?, ?, ?)",
        (text, datetime_value, audio_filename)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Reminder saved successfully"})

# ---------- DELETE REMINDER ----------
@app.route("/delete-reminder/<int:rid>")
def delete_reminder(rid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM reminders WHERE id = ?", (rid,))
    conn.commit()
    conn.close()
    return redirect("/recordings")

# ---------- EDIT REMINDER ----------
@app.route("/edit-reminder/<int:rid>")
def edit_reminder(rid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, text, time FROM reminders WHERE id = ?", (rid,))
    reminder = cur.fetchone()
    conn.close()
    return render_template("edit_reminder.html", reminder=reminder)

@app.route("/update-reminder", methods=["POST"])
def update_reminder():
    rid = request.form.get("id")
    text = request.form.get("text")
    time_val = request.form.get("time")

    if time_val:
        time_val = time_val.replace("T", " ")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE reminders SET text = ?, time = ? WHERE id = ?",
        (text, time_val, rid)
    )
    conn.commit()
    conn.close()

    return redirect("/recordings")

# ================= MAIN =================
if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_scheduler, daemon=True).start()
    app.run(debug=True)
