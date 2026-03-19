# Google Meet Auto-Attender 🤖

Welcome to the **Google Meet Auto-Attender**! 🎉 

Have you ever felt tired of waking up super early for a mandatory online meeting where you just listen and never talk? Or maybe you have a packed schedule and keep forgetting to join calls on time? I built this Python application to solve exactly that problem for you.

This desktop application automatically logs you into your Google account, jumps into your scheduled Google Meet calls exactly on time, and keeps your microphone and camera turned off so you don't accidentally broadcast yourself. Once the meeting starts emptying out, the bot is smart enough to detect that and automatically leave the call.

Set your schedule, hit start, and let the bot do the heavy lifting while you catch up on sleep or focus on other work! 🛌✨

## 🌟 What This Bot Actually Does

- **⏰ Automated Scheduling:** You can set exactly when you want the bot to join a meeting (e.g., `09:00, https://meet.google.com/abc-defg-hij`). It will wait patiently and join precisely on time.
- **🙈 Stealth Mode (Camera & Mic Off):** The bot ensures your camera and microphone are muted before joining, so you have zero risk of an embarrassing hot-mic moment.
- **🚪 Smart Auto-Leave:** You can set a minimum number of participants. If the class or meeting ends and people start leaving, the bot will automatically dip out once the participant count drops below your threshold (default is 4).
- **🔒 Zero Login Friction:** Instead of logging in from scratch every time (which triggers Google's 2FA and bot protections), it uses your actual, regular Chrome profile. You are already logged in!
- **☕ Anti-Sleep/Anti-Idle:** The bot subtly jitters your mouse in the background so your computer won't suddenly lock or go to sleep in the middle of a 2-hour lecture.
- **👻 Background Mode:** Don't want a random Chrome tab popping up and ruining your flow? Check the "Run in Background" box, and the bot will do its job minimized while you continue working or gaming.
- **🔔 Discord Notifications:** (Optional) You can provide a Discord webhook URL, and the bot will message you when it joins a meeting, when the host ends it, or when it decides to leave.

## 🛠️ How to Get Started

### 1. Prerequisites
Make sure you have Python installed on your computer.

### 2. Setup
Open up your terminal or command prompt, navigate to this project folder, and install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run the App
Launch the graphical interface by running:
```bash
python meet_bot.py
```

### 4. Important Step Before Hitting "Start"
**Close all your regular Google Chrome windows** before starting the automation. 
Because the bot uses your actual logged-in Chrome profile to bypass login screens, it needs exclusive access to that profile. If you have Chrome open, it might fail to load properly.

### 5. Configure and Go!
1. **Schedule:** Paste your meeting times and URLs in the text box (example: `14:30, https://meet.google.com/xyz`).
2. **Profile:** Double-check that the "Chrome User Data Dir" path in the app points to your actual Chrome profile (the default usually works just fine).
3. **Threshold:** Set the minimum amount of people before it leaves (4 is a safe bet).
4. Hit **Start Automation**!

## 💡 Troubleshooting & FAQs

- **"It opens up and asks me to log in!"**
  Double-check that the "Chrome User Data Dir" path in the app matches your computer's actual setup. It should point to something like `C:\Users\YOURNAME\AppData\Local\Google\Chrome\User Data`.
- **"The bot crashes as soon as it opens Chrome!"**
  Seriously, **close your regular Chrome windows** before running it. Chrome doesn't like sharing the same user profile across two separate instances at the exact same time.
- **"Will the professor know I use a bot?"**
  The bot joins using your real account, your real name, and mutes everything. To the host, it looks exactly like you joined normally and are just listening quietly. 

---

*Disclaimer: Have fun, get some rest, and use this responsibly. I am not responsible if you miss something important because you were asleep!*
