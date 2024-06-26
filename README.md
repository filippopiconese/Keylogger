# Program objectives
This is a keylogger, use it for testing purposes only.
You will gather keyboard strokes, mouse movements, screenshots and microphone input.
All the collected info will be sent via email every defined time interval.

## Program phases

### Imports

from dotenv import load_dotenv
from utils import (
    send_mail_with_attachment,
    get_wav_and_png_files,
    delete_wav_and_png_files,
)
- **smtplib**: Provides an SMTP client session to send emails.
- **os**: Provides a way of using operating system-dependent functionality.
- **platform**: Provides an interface to various services that interact with the operating system.
- **socket**: Provides access to the underlying operating system's socket services.
- **time**: Used for both sleeping the program and get timestamp.
- **wave**: Used for reading and writing WAV files.
- **pyscreenshot**: Captures screenshots.
- **sounddevice**: Provides an interface to play and record audio.
- **pynput**: Library for monitoring input devices.
- **load_dotenv**: Get environment variables.
- **utils**: Some custom functions.

Note: to install everything you need you should run
```python
pip install -r requirements.txt
```

### Configuration

Defines email details for sending logs.
For this project, I created an email account using [mailtrap](https://mailtrap.io).
Specifies the interval for sending reports (SEND_REPORT_EVERY) and some other variables.

### KeyLogger Class

- Collects system information (hostname, IP address, processor, system, machine).
- Collects system geo-location
- Monitors keyboard strokes.
- Records mouse movements, clicks, and scrolls - but only log clicks to reduce the quantity of logs.
- Take screenshots.
- Capture microphone input.
- Saves the logged data to a string (self.log).
- Sends email reports with logged data and attachments.
- Clean the data.
- The run method starts the keylogger by setting up keyboard, mouse, screenshot and microphone listeners.

### Execution

Creates an instance of the KeyLogger class with the needed variables.
Calls the run method to start the keylogger.
The first action, based on the operating system, deletes the .env file. In this way, the target cannot see your sensitive data.
Write the magic word (if set) to break the loop.

### TODO
- Add an optional parameter to copy the Python script somewhere and creates a scheduled task to execute it
- Create a USB key that runs upon it's plugged in a PC
- Improve the remove_env_file function to remove the .env file only when somebody tries to check the file content
