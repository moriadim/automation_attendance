import customtkinter as ctk
import tkinter as tk
import threading
import queue
import time
import os
import sys
import datetime
import requests
import pyautogui
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re

# GUI Settings
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AntiIdleThread(threading.Thread):
    def __init__(self, stop_event, log_queue):
        super().__init__()
        self.stop_event = stop_event
        self.log_queue = log_queue
        self.daemon = True

    def run(self):
        self.log_queue.put("Anti-idle thread started.")
        while not self.stop_event.is_set():
            # Jitter mouse slightly to prevent sleep every 60 seconds
            for _ in range(60):
                if self.stop_event.is_set():
                    break
                time.sleep(1)
            if not self.stop_event.is_set():
                try:
                    # Move mouse slightly by 1 pixel and back to avoid noticeable interference
                    pyautogui.moveRel(1, 1, duration=0.1)
                    pyautogui.moveRel(-1, -1, duration=0.1)
                    # Cannot log too frequently or UI clogs, so optionally log here or remain silent
                except Exception as e:
                    self.log_queue.put(f"Anti-idle error: {e}")
        self.log_queue.put("Anti-idle thread stopped.")


class BotThread(threading.Thread):
    def __init__(self, schedule_items, profile_path, min_participants, headless, webhook_url, stop_event, log_queue):
        super().__init__()
        # schedule_items is a list of dicts: [{'time': '09:00', 'url': '...', 'done': False}]
        self.schedule_items = schedule_items
        self.profile_path = profile_path
        self.min_participants = min_participants
        self.headless = headless
        self.webhook_url = webhook_url
        self.stop_event = stop_event
        self.log_queue = log_queue
        self.daemon = True
        self.driver = None

    def log(self, message):
        self.log_queue.put(message)

    def send_webhook(self, message):
        if not self.webhook_url or not self.webhook_url.strip():
            return
        
        try:
            payload = {"content": f"🤖 **Meet Bot Update**: {message}"}
            requests.post(self.webhook_url.strip(), json=payload, timeout=5)
        except Exception as e:
            self.log(f"Failed to send Discord webhook: {e}")

    def init_driver(self):
        self.log("Initializing Chrome Driver...")
        options = Options()
        
        # Security/Automated warnings bypass for Meet
        options.add_argument("--disable-infobars")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Mute camera and mic seamlessly
        options.add_argument("--use-fake-ui-for-media-stream")
        
        # Headless mode if selected
        if self.headless:
            options.add_argument("--headless=new")
            self.log("Running Chrome in Headless mode (hidden).")
        
        # Set profile path if provided
        if self.profile_path and self.profile_path.strip():
            # Usually profile path ends with "User Data" -> Need to handle appropriately
            # If path ends with '\Default' or Profile, strip it. We pass User Data dir.
            user_data_dir = self.profile_path.strip()
            options.add_argument(f"user-data-dir={user_data_dir}")
            self.log(f"Using Chrome profile at: {user_data_dir}")
        else:
            self.log("WARNING: No Chrome Profile provided. You will likely not be logged in and might be prompted for 2FA or fail to join.")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.maximize_window()
            return True
        except Exception as e:
            self.log(f"Error initializing Chrome: {str(e)}")
            self.log("Make sure all Chrome instances are closed before using a custom profile!")
            return False

    def join_meeting(self, url):
        self.log(f"Navigating to {url}...")
        self.driver.get(url)
        time.sleep(5)  # Let initial page load

        if self.stop_event.is_set():
            return False

        # Try to find and click "Join now" or "Ask to join"
        try:
            # Wait up to 30 seconds for the button to appear
            wait = WebDriverWait(self.driver, 30)
            
            # Using XPath to match common Join buttons
            # Language independent approach or generic buttons usually use specific jsnames or classes
            # Mute mic and camera again just in case the fake-ui didn't block an internal meet prompt
            try:
                # Ctrl+D (Mute Mic), Ctrl+E (Mute Cam) - sending keys to body
                body = self.driver.find_element(By.TAG_NAME, 'body')
                body.send_keys(u'\ue009' + 'd') # Keys.CONTROL + d
                body.send_keys(u'\ue009' + 'e') # Keys.CONTROL + e
                time.sleep(1)
            except:
                pass

            # Find join button
            self.log("Looking for Join button...")
            
            # Common XPath for "Join now" or "Ask to join" spans text
            join_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Join now') or contains(text(), 'Ask to join')]")))
            button_text = join_button.text
            self.log(f"Clicking '{button_text}'...")
            join_button.click()
            
            self.log("Successfully clicked Join button. Waiting 10s for meeting to start...")
            self.send_webhook(f"Just joined meeting at `{url}`!")
            
            # Important: Delay 10 seconds before monitoring participants to avoid premature leaving
            for _ in range(10):
                if self.stop_event.is_set():
                    return False
                time.sleep(1)
            
            return True
            
        except Exception as e:
            self.log(f"Could not join the meeting. Error: {str(e)}")
            return False

    def monitor_meeting(self):
        self.log("Starting participant monitoring...")
        while not self.stop_event.is_set():
            try:
                # Find participant count element.
                try:
                    # Look for the people icon button, which contains the participant count as text
                    people_btn = self.driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Show everyone') or contains(@aria-label, 'everyone')]")
                    count_text = people_btn.text
                    # Extract numbers from text
                    nums = re.findall(r'\d+', count_text)
                    if nums:
                        count = int(nums[0])
                        self.log(f"Current participants: {count}")
                        
                        if count < self.min_participants:
                            self.log(f"Participant count ({count}) dropped below minimum ({self.min_participants}). Leaving call...")
                            self.send_webhook(f"Leaving call. Participants dropped to {count} (minimum was {self.min_participants}).")
                            self.leave_meeting()
                            return True # Signal to move to next meeting
                    else:
                        self.log("Could not parse participant count from the UI.")
                except Exception as eval_e:
                    # Alternative approach: Find the div with class 'uGOf1d' which often holds the count
                    try:
                        divs = self.driver.find_elements(By.CLASS_NAME, "uGOf1d")
                        found = False
                        for div in divs:
                            if div.text.isdigit():
                                count = int(div.text)
                                self.log(f"Current participants: {count}")
                                found = True
                                if count < self.min_participants:
                                    self.log(f"Participant count ({count}) dropped below minimum ({self.min_participants}). Leaving call...")
                                    self.send_webhook(f"Leaving call. Participants dropped to {count} (minimum was {self.min_participants}).")
                                    self.leave_meeting()
                                    return True
                        if not found:
                            self.log("Could not find participant count element.")
                    except:
                        self.log("Error analyzing participants.")
            except Exception as e:
                self.log(f"Monitoring error: {str(e)}")
            
            # Wait 60 seconds before next check
            for _ in range(60):
                if self.stop_event.is_set():
                    return False
                time.sleep(1)
                
        return False

    def leave_meeting(self):
        self.log("Leaving meeting...")
        try:
            # Look for the leave call button (red phone icon)
            leave_button = self.driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Leave call')]")
            leave_button.click()
            self.log("Left the meeting successfully.")
            time.sleep(3)
        except Exception as e:
            self.log(f"Could not click leave button: {str(e)}")

    def run(self):
        self.log("Bot thread started. Monitoring schedule...")
        self.send_webhook("System Armed and Monitoring Schedule.")
        
        while not self.stop_event.is_set():
            now = datetime.datetime.now()
            current_time_str = now.strftime("%H:%M")
            
            for item in self.schedule_items:
                if item['done']:
                    continue
                
                # Check if it's time to join (we give a 1 minute window just in case)
                if current_time_str == item['time']:
                    self.log(f"--- Time reached for scheduled entry: {item['url']} ---")
                    
                    if not self.driver:
                        # Initialize driver if it's not open yet
                        if not self.init_driver():
                            self.log("Bot stopped due to driver initialization failure.")
                            self.send_webhook("🚨 Failed to initialize Chrome Driver.")
                            self.stop_event.set()
                            return
                            
                    joined = self.join_meeting(item['url'])
                    item['done'] = True
                    
                    if joined:
                        self.monitor_meeting()
                        # After leaving, clean up the browser to save RAM if waiting for next
                        if self.driver:
                            self.log("Closing browser until next meeting...")
                            try:
                                self.driver.quit()
                            except:
                                pass
                            self.driver = None
                    else:
                        self.log(f"Skipping {item['url']} due to join failure.")
                        self.send_webhook(f"🚨 Failed to join meeting at `{item['url']}`.")
                        
            # Check if all tasks are done
            if all(item['done'] for item in self.schedule_items):
                self.log("All scheduled meetings have been processed.")
                break
                
            # Sleep briefly before next time check
            for _ in range(10):
                if self.stop_event.is_set():
                    break
                time.sleep(1)
                
        self.log("Finished processing all scheduled URLs.")
        if self.driver:
            self.log("Closing browser...")
            try:
                self.driver.quit()
            except:
                pass
        self.send_webhook("System Finished gracefully.")
        self.log("Bot thread finished.")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Google Meet Auto-Attender")
        self.geometry("800x600")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(5, weight=1)

        # Title
        self.title_label = ctk.CTkLabel(self.main_frame, text="Google Meet Auto-Attender", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10))

        # URL Input
        self.url_label = ctk.CTkLabel(self.main_frame, text="Schedule (Format: HH:MM, URL):", font=ctk.CTkFont(weight="bold"))
        self.url_label.grid(row=1, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="w")
        
        self.url_hint = ctk.CTkLabel(self.main_frame, text="Example: 09:00, https://meet.google.com/abc-defg-hij", font=ctk.CTkFont(size=11, slant="italic"))
        self.url_hint.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 2), sticky="w")
        
        self.url_textbox = ctk.CTkTextbox(self.main_frame, height=100)
        self.url_textbox.grid(row=3, column=0, columnspan=2, padx=20, pady=(5, 10), sticky="ew")

        # Configuration options
        # Profile Path
        self.profile_label = ctk.CTkLabel(self.main_frame, text="Chrome User Data Dir:")
        self.profile_label.grid(row=4, column=0, padx=20, pady=(10, 0), sticky="w")
        
        default_profile_path = os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Local', 'Google', 'Chrome', 'User Data')
        self.profile_entry = ctk.CTkEntry(self.main_frame, placeholder_text="e.g. C:\\...\\User Data")
        self.profile_entry.insert(0, default_profile_path)
        self.profile_entry.grid(row=5, column=0, padx=20, pady=(5, 10), sticky="ew")

        # Participant Count
        self.min_parts_label = ctk.CTkLabel(self.main_frame, text="Minimum Participants to Leave:")
        self.min_parts_label.grid(row=4, column=1, padx=20, pady=(10, 0), sticky="w")
        
        self.min_parts_entry = ctk.CTkEntry(self.main_frame, placeholder_text="e.g. 4")
        self.min_parts_entry.insert(0, "4")
        self.min_parts_entry.grid(row=5, column=1, padx=20, pady=(5, 10), sticky="ew")

        # Webhook URL
        self.webhook_label = ctk.CTkLabel(self.main_frame, text="Discord Webhook URL (Optional):")
        self.webhook_label.grid(row=6, column=0, columnspan=2, padx=20, pady=(5, 0), sticky="w")
        
        self.webhook_entry = ctk.CTkEntry(self.main_frame, placeholder_text="https://discord.com/api/webhooks/...")
        self.webhook_entry.grid(row=7, column=0, columnspan=2, padx=20, pady=(5, 10), sticky="ew")

        # Headless Checkbox
        self.headless_var = ctk.BooleanVar(value=False)
        self.headless_checkbox = ctk.CTkCheckBox(self.main_frame, text="Run in Background (Headless)", variable=self.headless_var)
        self.headless_checkbox.grid(row=8, column=0, columnspan=2, padx=20, pady=(5, 10), sticky="w")

        # Status Log
        self.log_label = ctk.CTkLabel(self.main_frame, text="Status Log:")
        self.log_label.grid(row=9, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="w")
        
        self.log_textbox = ctk.CTkTextbox(self.main_frame, state="disabled")
        self.log_textbox.grid(row=10, column=0, columnspan=2, padx=20, pady=(5, 10), sticky="nsew")

        # Buttons
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.grid(row=11, column=0, columnspan=2, padx=20, pady=20)
        
        self.start_btn = ctk.CTkButton(self.button_frame, text="Start Automation", command=self.start_automation, fg_color="green", hover_color="darkgreen")
        self.start_btn.pack(side="left", padx=10)
        
        self.stop_btn = ctk.CTkButton(self.button_frame, text="Emergency Stop", command=self.stop_automation, fg_color="red", hover_color="darkred", state="disabled")
        self.stop_btn.pack(side="left", padx=10)

        # Threading and Queues
        self.log_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.bot_thread = None
        self.idle_thread = None
        
        # Load previous URLs if they exist
        self.load_urls()

        # Start queue checker
        self.check_queue()
        
    def load_urls(self):
        try:
            if os.path.exists("saved_data.txt"):
                with open("saved_data.txt", "r") as f:
                    lines = f.readlines()
                    if len(lines) >= 1:
                        self.url_textbox.insert("1.0", lines[0].strip().replace("||", "\n"))
                    if len(lines) >= 2:
                        self.webhook_entry.insert(0, lines[1].strip())
        except Exception:
            pass
            
    def save_urls(self, urls_text, webhook_url):
        try:
            with open("saved_data.txt", "w") as f:
                encoded_urls = urls_text.replace("\n", "||")
                f.write(encoded_urls + "\n")
                f.write(webhook_url + "\n")
        except Exception:
            pass

    def log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def check_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get(False)
            self.log(msg)
            
        # Also check if threads have finished to reset UI
        if self.bot_thread and not self.bot_thread.is_alive():
            if self.stop_btn._state != "disabled":
                self.stop_btn.configure(state="disabled")
                self.start_btn.configure(state="normal")
                self.log("Automation finished.")
                self.bot_thread = None
                
        self.after(100, self.check_queue)

    def start_automation(self):
        urls_text = self.url_textbox.get("1.0", "end-1c")
        lines = [u for u in urls_text.split('\n') if u.strip()]
        
        if not lines:
            self.log("Error: Please enter at least one schedule item.")
            return
            
        webhook_url = self.webhook_entry.get()
        
        # Save config for next time
        self.save_urls(urls_text, webhook_url)

        # Parse schedule
        schedule_items = []
        for line in lines:
            if ',' not in line:
                self.log(f"Error parsing line: '{line}'. Missing comma separation.")
                return
                
            parts = line.split(',', 1)
            time_str = parts[0].strip()
            url_str = parts[1].strip()
            
            # Basic validation of HH:MM
            if not re.match(r'^\d{2}:\d{2}$', time_str):
                self.log(f"Invalid time format: '{time_str}'. Please use HH:MM (e.g. 09:30)")
                return
                
            schedule_items.append({
                'time': time_str,
                'url': url_str,
                'done': False
            })

        profile_path = self.profile_entry.get()
        headless_mode = self.headless_var.get()
        try:
            min_parts = int(self.min_parts_entry.get())
        except ValueError:
            self.log("Error: Minimum participants must be an integer.")
            return

        self.log(f"Starting automation. Armed for {len(schedule_items)} meetings...")
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        self.stop_event.clear()
        
        # Start Anti-Idle Thread
        self.idle_thread = AntiIdleThread(self.stop_event, self.log_queue)
        self.idle_thread.start()
        
        # Start Bot Thread
        self.bot_thread = BotThread(schedule_items, profile_path, min_parts, headless_mode, webhook_url, self.stop_event, self.log_queue)
        self.bot_thread.start()

    def stop_automation(self):
        self.log("Emergency Stop initiated. Sending stop signals to threads...")
        self.stop_event.set()
        self.stop_btn.configure(state="disabled")

    def on_closing(self):
        self.stop_automation()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
