# KeyLogger - Monitoring and Reporting Program

## Description
Collects keyboard/mouse input, screenshots, and microphone audio at regular intervals. Sends logs via email and uploads files to Dropbox.

> **Use exclusively for testing in authorized environments.**

---

## Requirements
Python 3 + packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

---

## Configuration

### 1. Create `.env`
```plaintext
SMTP_SERVER=<your_smtp_server>
SMTP_PORT=<your_smtp_port>
EMAIL_ADDRESS=<your_email_address>
EMAIL_PASSWORD=<your_email_password>
EMAIL_SENDER=<sender_email>
EMAIL_RECEIVER=<receiver_email>
EMAIL_CC=<cc_email_or_empty>

DROPBOX_APP_KEY=<your_app_key>
DROPBOX_APP_SECRET=<your_app_secret>
DROPBOX_REFRESH_TOKEN=<your_refresh_token>
```

### 2. Obtain a permanent Dropbox refresh token
Run once (requires App Key and App Secret from https://www.dropbox.com/developers/apps):
```bash
python dropbox_auth.py
```
Follow the instructions printed in the terminal. Copy the three values into `.env`.

### 3. Adjust settings in `main.py`
| Variable | Default | Description |
|---|---|---|
| `SEND_REPORT_EVERY` | `30` | Report interval in seconds |
| `MAGIC_WORD` | `"stop"` | Type this word to stop the keylogger |
| `SCHEDULED_TASK_NAME` | `"TASK_NAME"` | Name of the Windows scheduled task |

---

## Run as Python script
```bash
python main.py
```

---

## Build a standalone `.exe`

Use the interactive build script — it bundles the `.env` inside the executable so the final `dist\main.exe` is fully self-contained.

```bash
python build_exe.py
```

The script will ask:
```
[1] Simple build (no obfuscation)
[2] Obfuscated build (pyarmor + pyinstaller)
```

Output: `dist\main.exe` — no `.env` or any other file needed alongside it.

---

## How it works
- On startup: collects system info and geolocation, copies itself to `%APPDATA%\KEYLOGGER\`, creates a Windows scheduled task for persistence.
- Every interval: records keyboard/mouse, takes a screenshot on-click, records microphone audio (if available), then sends an email report and uploads files to Dropbox.
- Typing the `MAGIC_WORD` stops the process.
- All actions (including errors) are logged and included in the email report.

---

## TODO
- [ ] Save logs to local file when email sending fails (data loss prevention)
- [ ] Move `SEND_REPORT_EVERY`, `MAGIC_WORD`, `SCHEDULED_TASK_NAME` from `main.py` to `.env` (avoid recompiling for config changes)
- [ ] Replace `print()` + `appendlog()` with Python `logging` module (unified structured logging)
- [ ] Refactor `KeyLogger` class into separate components: `SystemInfoCollector`, `AudioRecorder`, `Reporter` (maintainability)
