# Python Auto-Attender

Automates joining Google Meet sessions using Selenium and CustomTkinter.

## Features
- **CustomTkinter GUI**: Modern dark-mode interface.
- **Persistent Login**: Uses your local Chrome `User Data` profile to bypass 2FA and stay logged in.
- **Auto Join & Leave**: Automatically mutes the mic/camera, joins the requested URLs, and monitors participant count. If the count drops below a threshold, it leaves and moves to the next link.
- **Anti-Idle**: Prevents your computer from sleeping while attending the meeting by slightly moving the mouse every minute.

## Setup
1. Clone the repository.
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the bot:
   ```bash
   python meet_bot.py
   ```

## Usage
- Paste one or more Google Meet links in the text box.
- Make sure ALL your existing Chrome windows are closed so the bot can use your profile.
- Click "Start Automation".
