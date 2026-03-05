# Google Meet Auto-Attender 🤖

So I got tired of having to wake up early or sit through mandatory online meetings where nobody actually talks to me, so I built this little Python script to do it for me. 

Basically, it logs you into your normal Google account, hops into the meeting exactly when it starts, keeps your mic and camera off so you don't accidentally dox yourself, and then automatically leaves whenever the room empties out. Oh, and it keeps your PC awake so you don't mysteriously go offline.

Set it, forget it, and go back to sleep. 🛌

## What it actually does
- **Saves Your URLs:** Paste your links once, and it remembers them for next time.
- **Background Mode (Headless):** You can check the "Run in Background" box to hide Chrome completely, so you can still game or work on your PC without a random Meet tab getting in the way.
- **Anti-Sleep:** Your PC won't suddenly lock or go to sleep in the middle of a 2 hour lecture.
- **Smart Leave:** It checks how many people are in the call. If the professor and like 3 other people are left, it dips out automatically.
- **Zero Login Friction:** It uses your actual normal Chrome profile. None of that "please enter 2FA on a guest window" nonsense.

## How to use it

1. Make sure you have python installed.
2. Open up your terminal or whatever, go to this folder, and install the stuff:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the script:
   ```bash
   python meet_bot.py
   ```
4. **Important:** Close all your regular Google Chrome windows before you hit "Start" (otherwise it can't load your logged-in profile). 
5. Paste your links, set the minimum amount of people before it leaves (I usually keep it at 4), and start it.

## Troubleshooting
- If it opens up and says you need to log in, just double check that the "Chrome User Data Dir" path makes sense for your computer. It should point to `C:\Users\YOURNAME\AppData\Local\Google\Chrome\User Data`.
- Seriously, **close your regular Chrome windows** before running it.

Have fun and use it responsibly (or don't, I'm just a README).
