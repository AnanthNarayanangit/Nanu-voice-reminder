# 🎙️ Smart Voice Reminder

A smart voice and text reminder web application built with Flask, SQLite, Web Speech API, and OpenAI. Record voice reminders, schedule one-time or recurring bill alerts, and receive email notifications when reminders trigger.

---

## ✨ Features

- **Voice & Text Input**: Record audio via your browser microphone with speech-to-text transcription or type reminders directly.
- **Multi-Language Speech Recognition**: Supports English (`en-IN`), Tamil (`ta-IN`), and Hindi (`hi-IN`).
- **AI-Powered Reminder Extraction**: Extracts reminder dates, times, and task messages from natural speech using OpenAI GPT models.
- **Audio Storage & Playback**: Audio recordings are saved in `.webm` format for playback in the web dashboard.
- **Bill Reminders**: Schedule recurring monthly bills (e.g., Electricity, Internet, House Rent, or custom bills) with calendar date clamping.
- **Automated Background Scheduler**: Built-in scheduler checks every minute and sends automated reminder emails via SMTP.
- **Reminder Management**: View, play audio, edit messages/schedules, or delete reminders.

---

## 📋 Prerequisites

- **Python**: Version 3.9 or higher
- **Web Browser**: Google Chrome or Microsoft Edge recommended for full Web Speech API (`webkitSpeechRecognition`) and microphone recording support.
- **(Optional) OpenAI API Key**: For natural language date/time extraction from spoken audio.
- **(Optional) Gmail App Password**: For sending email notifications via SMTP.

---

## 🚀 Quickstart Guide

### 1. Clone the Repository

```bash
git clone https://github.com/Antony-Ahelgen/Nanu-voice-reminder.git
cd Nanu-voice-reminder
```

### 2. Create and Activate a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ⚙️ Environment Variables Configuration

Create a `.env` file or set the following environment variables:

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | OpenAI API key for reminder parsing | *(Optional)* `sk-...` |
| `SMTP_EMAIL` | Sender & receiver Gmail address for alerts | *(Optional)* `your-email@gmail.com` |
| `SMTP_APP_PASSWORD` | Google App Password (16-character) | *(Optional)* `abcd efgh ijkl mnop` |

> [!NOTE]
> If `OPENAI_API_KEY` is not provided, manual date-time picking will be used. If SMTP credentials are not configured, reminders will be stored and tracked locally without crashing the background scheduler.

---

## 🏃 Running the Application

Start the Flask development server:

```bash
python app.py
```

Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🎤 Granting Browser Microphone Permissions

When using voice reminders for the first time:

1. Click the **Microphone** button on the home page.
2. When prompted by your browser:
   - Click **Allow** on the permission dialog: *"Allow http://127.0.0.1:5000 to use your microphone"*.
3. Speak your reminder clearly. Recording will capture audio and transcribe it into the text box automatically.
4. If microphone access was previously blocked:
   - Click the **Tune / Padlock** icon in your browser address bar.
   - Toggle **Microphone** to **Allow**, then refresh the page.

---

## 📁 Project Structure

```text
Nanu-voice-reminder/
├── app.py                   # Main Flask application and scheduler
├── requirements.txt         # Project dependencies
├── reminders.db             # SQLite database (created on startup)
├── static/
│   ├── audio/               # Saved audio recordings (.webm)
│   ├── script.js            # Voice recording and frontend logic
│   └── style.css            # Application styles
└── templates/
    ├── home.html            # Reminder creation dashboard
    ├── recordings.html      # Reminders list and bill management
    ├── set_bill.html        # Schedule recurring bill reminder
    ├── add_bill.html        # Create custom bill category
    └── edit_reminder.html   # Edit existing reminder
```
