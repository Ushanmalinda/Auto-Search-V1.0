import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import webbrowser
import time
import urllib.parse
import urllib.request
import json
import os
import random
import uuid
import winsound
import glob
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

CURRENT_VERSION = "1.0.0"
VERSION_CHECK_URL = "https://raw.githubusercontent.com/Ushanmalinda/Auto-Search-V1.0/main/version.json"

class EdgeSearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Edge Auto-Search Tool")
        self.root.geometry("850x800")
        self.root.configure(bg='#2b2b2b')
        
        # Variables
        self.file_path = tk.StringVar()
        self.delay_var = tk.IntVar(value=10)  # Default time set to 10 seconds
        self.profile_var = tk.StringVar()
        self.sentences_per_account = tk.IntVar(value=30)
        self.single_account_sentences = tk.IntVar(value=30)
        self.is_running = False
        self.search_thread = None
        self.available_profiles = []
        self.total_sentences = 0
        self.typing_delay_var = tk.DoubleVar(value=0.1)  # Delay between keystrokes (human-like typing)
        self.profile_checkboxes = {}  # Store profile checkboxes for multi-select
        self.profile_vars = {}  # Store checkbox variables
        self.headless_var = tk.BooleanVar(value=False)  # Headless mode for background stealth run
        self.driver = None  # Reference to the active Selenium driver
        self.update_info = None  # Store update information if version check finds new release
        
        # Style configuration
        self.setup_styles()
        self.create_widgets()
        self.load_profiles()
        
        # Check for updates in the background
        threading.Thread(target=self.run_update_check, daemon=True).start()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', background='#2b2b2b', foreground='#ffffff', font=('Segoe UI', 16, 'bold'))
        style.configure('Heading.TLabel', background='#2b2b2b', foreground='#4a9eff', font=('Segoe UI', 11, 'bold'))
        style.configure('Normal.TLabel', background='#2b2b2b', foreground='#ffffff', font=('Segoe UI', 10))
        style.configure('Success.TLabel', background='#2b2b2b', foreground='#4caf50', font=('Segoe UI', 10))
        style.configure('Info.TLabel', background='#2b2b2b', foreground='#ffa726', font=('Segoe UI', 10, 'bold'))
        style.configure('Custom.TFrame', background='#2b2b2b')
        style.configure('Action.TButton', font=('Segoe UI', 11, 'bold'), padding=(20, 10))
        style.configure('Start.TButton', font=('Segoe UI', 12, 'bold'), padding=(30, 15))
        
    def create_widgets(self):
        main_container = ttk.Frame(self.root, style='Custom.TFrame')
        main_container.pack(fill='both', expand=True, padx=5, pady=5)
        self.canvas = tk.Canvas(main_container, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient='vertical', command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, style='Custom.TFrame')
        self.scrollable_frame.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)
        self.root.bind('<MouseWheel>', self._on_mousewheel)
        main_frame = ttk.Frame(self.scrollable_frame, style='Custom.TFrame', padding="20")
        main_frame.pack(fill='both', expand=True)
        title_label = ttk.Label(main_frame, text="🔍 Enhanced Edge Auto-Search Tool", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Update Banner Frame (initially empty/hidden)
        self.update_banner_frame = ttk.Frame(main_frame, style='Custom.TFrame')
        self.update_banner_frame.pack(fill='x', pady=(0, 10))
        file_frame = ttk.LabelFrame(main_frame, text="📁 Text File Selection", padding="15")
        file_frame.pack(fill='x', pady=(0, 15))
        ttk.Label(file_frame, text="Select your text file:", style='Normal.TLabel').pack(anchor='w')
        file_select_frame = ttk.Frame(file_frame)
        file_select_frame.pack(fill='x', pady=(5, 0))
        self.file_entry = ttk.Entry(file_select_frame, textvariable=self.file_path, font=('Segoe UI', 10))
        self.file_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        ttk.Button(file_select_frame, text="Browse", command=self.browse_file, style='Action.TButton').pack(side='right')
        self.file_info_frame = ttk.Frame(file_frame)
        self.file_info_frame.pack(fill='x', pady=(10, 0))
        self.file_info_label = ttk.Label(self.file_info_frame, text="", style='Info.TLabel')
        self.file_info_label.pack(anchor='w')
        profile_frame = ttk.LabelFrame(main_frame, text="👤 Edge Profile Selection", padding="15")
        profile_frame.pack(fill='x', pady=(0, 15))
        ttk.Label(profile_frame, text="Choose Edge profile(s):", style='Normal.TLabel').pack(anchor='w')
        
        # Profile mode selection
        self.profile_mode_frame = ttk.Frame(profile_frame)
        self.profile_mode_frame.pack(fill='x', pady=(5, 10))
        
        self.profile_combo = ttk.Combobox(self.profile_mode_frame, textvariable=self.profile_var, font=('Segoe UI', 10), state='readonly')
        self.profile_combo.pack(fill='x')
        self.profile_combo.bind('<<ComboboxSelected>>', self.on_profile_change)
        
        # Multi-select checkboxes frame (hidden by default)
        self.multi_select_frame = ttk.LabelFrame(profile_frame, text="✓ Select Profiles to Run", padding="10")
        self.multi_select_scrollframe = ttk.Frame(self.multi_select_frame)
        self.multi_select_scrollframe.pack(fill='both', expand=True)
        distribution_frame = ttk.LabelFrame(main_frame, text="📊 Search Distribution Settings - Adjust the numbers below!", padding="15")
        distribution_frame.pack(fill='x', pady=(0, 15))
        self.all_profiles_frame = ttk.Frame(distribution_frame)
        self.all_profiles_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(self.all_profiles_frame, text="Sentences per account (All Profiles mode) - DEFAULT: 30 (You can change this!):", style='Normal.TLabel').pack(anchor='w')
        all_profiles_control = ttk.Frame(self.all_profiles_frame)
        all_profiles_control.pack(fill='x', pady=(5, 0))
        self.sentences_spin = ttk.Spinbox(all_profiles_control, from_=1, to=200, width=10, textvariable=self.sentences_per_account, font=('Segoe UI', 10))
        self.sentences_spin.pack(side='left')
        ttk.Label(all_profiles_control, text="sentences per profile (1-200 allowed)", style='Normal.TLabel').pack(side='left', padx=(10, 0))
        self.single_profile_frame = ttk.Frame(distribution_frame)
        self.single_profile_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(self.single_profile_frame, text="Number of sentences (Single Profile mode) - DEFAULT: 30 (You can change this!):", style='Normal.TLabel').pack(anchor='w')
        single_profile_control = ttk.Frame(self.single_profile_frame)
        single_profile_control.pack(fill='x', pady=(5, 0))
        self.single_sentences_spin = ttk.Spinbox(single_profile_control, from_=1, to=200, width=10, textvariable=self.single_account_sentences, font=('Segoe UI', 10))
        self.single_sentences_spin.pack(side='left')
        ttk.Label(single_profile_control, text="sentences to search (1-200 allowed)", style='Normal.TLabel').pack(side='left', padx=(10, 0))
        self.distribution_preview = ttk.Label(distribution_frame, text="", style='Info.TLabel')
        self.distribution_preview.pack(anchor='w', pady=(10, 0))
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ Search Settings", padding="15")
        settings_frame.pack(fill='x', pady=(0, 15))
        
        delay_frame = ttk.Frame(settings_frame)
        delay_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(delay_frame, text="Delay between searches (seconds):", style='Normal.TLabel').pack(side='left')
        delay_spin = ttk.Spinbox(delay_frame, from_=1, to=60, width=10, textvariable=self.delay_var, font=('Segoe UI', 10))
        delay_spin.pack(side='left', padx=(10,0))
        
        # Add typing speed option
        typing_frame = ttk.Frame(settings_frame)
        typing_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(typing_frame, text="Typing speed (seconds per character):", style='Normal.TLabel').pack(side='left')
        typing_spin = ttk.Spinbox(typing_frame, from_=0.05, to=0.5, increment=0.05, width=10, textvariable=self.typing_delay_var, font=('Segoe UI', 10))
        typing_spin.pack(side='left', padx=(10,0))
        ttk.Label(typing_frame, text="(0.05=fast, 0.2=human-like)", style='Normal.TLabel').pack(side='left', padx=(10,0))
        
        # Add Headless Mode checkbox
        headless_frame = ttk.Frame(settings_frame)
        headless_frame.pack(fill='x')
        self.headless_cb = ttk.Checkbutton(
            headless_frame, 
            text="Headless Mode (Completely Invisible Search in Background)", 
            variable=self.headless_var
        )
        self.headless_cb.pack(side='left')
        control_frame = ttk.Frame(main_frame, style='Custom.TFrame')
        control_frame.pack(fill='x', pady=(0, 15))
        self.start_button = ttk.Button(control_frame, text="🚀 Start Search", command=self.start_search, style='Start.TButton')
        self.start_button.pack(side='left', padx=(0, 10))
        self.stop_button = ttk.Button(control_frame, text="⏹️ Stop Search", command=self.stop_search, style='Action.TButton', state='disabled')
        self.stop_button.pack(side='left')
        progress_frame = ttk.LabelFrame(main_frame, text="📊 Progress", padding="15")
        progress_frame.pack(fill='x', pady=(0, 15))
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.pack(fill='x', pady=(0, 10))
        self.status_label = ttk.Label(progress_frame, text="Ready to start...", style='Normal.TLabel')
        self.status_label.pack(anchor='w')
        log_frame = ttk.LabelFrame(main_frame, text="📋 Activity Log", padding="15")
        log_frame.pack(fill='x', pady=(0, 15))
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=70, font=('Consolas', 9), bg='#1e1e1e', fg='#ffffff', insertbackground='#ffffff')
        self.log_text.pack(fill='x', pady=(5, 0))
        self.on_profile_change()
        self.root.after(100, self._update_scroll_region)
        
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
    def _update_scroll_region(self):
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        
    def browse_file(self):
        filename = filedialog.askopenfilename(title="Select Text File", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            self.file_path.set(filename)
            self.analyze_file()
            self.log_message(f"📁 Selected file: {Path(filename).name}")
            
    def analyze_file(self):
        if not self.file_path.get() or not os.path.exists(self.file_path.get()):
            self.file_info_label.config(text="")
            self.total_sentences = 0
            self.update_distribution_preview()
            return
        try:
            with open(self.file_path.get(), 'r', encoding='utf-8') as file:
                content = file.read()
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            self.total_sentences = len(lines)
            self.file_info_label.config(text=f"📄 File contains {self.total_sentences} sentences")
            self.update_distribution_preview()
        except Exception as e:
            self.file_info_label.config(text=f"❌ Error reading file: {str(e)}")
            self.total_sentences = 0
    
    def on_profile_change(self, event=None):
        profile_selection = self.profile_var.get()
        
        # Check if "Custom Selection" mode
        if profile_selection and "CUSTOM" in profile_selection.upper():
            # Show multi-select checkboxes
            self.multi_select_frame.pack(fill='x', pady=(10, 0))
            self.all_profiles_frame.pack(fill='x', pady=(0, 10))
            self.single_profile_frame.pack_forget()
        elif profile_selection and profile_selection.startswith("0"):
            # All profiles mode
            self.multi_select_frame.pack_forget()
            self.all_profiles_frame.pack(fill='x', pady=(0, 10))
            self.single_profile_frame.pack_forget()
        else:
            # Single profile mode
            self.multi_select_frame.pack_forget()
            self.single_profile_frame.pack(fill='x', pady=(0, 10))
            self.all_profiles_frame.pack_forget()
        
        self.update_distribution_preview()
        self._update_scroll_region()
    
    def update_distribution_preview(self):
        if self.total_sentences == 0:
            self.distribution_preview.config(text="")
            return
        profile_selection = self.profile_var.get()
        try:
            # Custom selection mode
            if profile_selection and "CUSTOM" in profile_selection.upper():
                selected_profiles = self.get_selected_profiles()
                if not selected_profiles:
                    self.distribution_preview.config(text="⚠️ Please select at least one profile")
                    return
                    
                try:
                    sentences_per_profile = self.sentences_per_account.get()
                except:
                    sentences_per_profile = 30
                    
                num_profiles = len(selected_profiles)
                total_searches = sentences_per_profile * num_profiles
                remaining = max(0, self.total_sentences - total_searches)
                
                profile_names = ", ".join([p.split(" - ")[0] for p in selected_profiles])
                preview_text = f"📊 Will search {sentences_per_profile} sentences in profiles: {profile_names}"
                if remaining > 0:
                    preview_text += f" ({remaining} sentences will be skipped)"
                elif total_searches > self.total_sentences:
                    actual_per_profile = self.total_sentences // num_profiles
                    preview_text = f"📊 Will search {actual_per_profile} sentences in selected profiles (adjusted to fit file)"
                self.distribution_preview.config(text=preview_text)
            # All profiles mode    
            elif profile_selection and profile_selection.startswith("0"):
                try:
                    sentences_per_profile = self.sentences_per_account.get()
                except:
                    sentences_per_profile = 30
                num_profiles = len(self.available_profiles)
                if num_profiles > 0:
                    total_searches = sentences_per_profile * num_profiles
                    remaining = max(0, self.total_sentences - total_searches)
                    preview_text = f"📊 Will search {sentences_per_profile} sentences in each of {num_profiles} profiles"
                    if remaining > 0:
                        preview_text += f" ({remaining} sentences will be skipped)"
                    elif total_searches > self.total_sentences:
                        actual_per_profile = self.total_sentences // num_profiles
                        preview_text = f"📊 Will search {actual_per_profile} sentences in each profile (adjusted to fit file)"
                    self.distribution_preview.config(text=preview_text)
                else:
                    self.distribution_preview.config(text="")
            # Single profile mode
            else:
                try:
                    sentences_to_search = self.single_account_sentences.get()
                except:
                    sentences_to_search = 30
                sentences_to_search = min(sentences_to_search, self.total_sentences)
                remaining = max(0, self.total_sentences - sentences_to_search)
                preview_text = f"📊 Will search {sentences_to_search} sentences in selected profile"
                if remaining > 0:
                    preview_text += f" ({remaining} sentences will be skipped)"
                self.distribution_preview.config(text=preview_text)
        except Exception as e:
            self.distribution_preview.config(text="")
    
    def load_profiles(self):
        """Load and display available Edge profiles."""
        self.log_message("🔍 Checking for Edge browser profiles...")
        self.available_profiles = self.get_edge_profiles()
        
        # Create profile options list
        if len(self.available_profiles) > 1:
            # Multiple profiles available - show "ALL PROFILES" and "CUSTOM SELECTION" options
            profile_options = [
                "0 - ALL PROFILES (Run through each profile)",
                "00 - CUSTOM SELECTION (Choose specific profiles)"
            ] + self.available_profiles
            self.log_message(f"✅ Found {len(self.available_profiles)} Edge profiles")
        else:
            # Only one profile - don't show "ALL PROFILES" or "CUSTOM" options
            profile_options = self.available_profiles
            self.log_message(f"✅ Found {len(self.available_profiles)} Edge profile")
        
        self.profile_combo['values'] = profile_options
        self.profile_combo.current(0)
        
        # Create checkboxes for custom selection
        self.create_profile_checkboxes()
        
        # Display summary
        self.log_message(f"📊 Available profiles:")
        for profile in self.available_profiles:
            self.log_message(f"   • {profile}")
        
        def safe_update_preview(event=None):
            try:
                self.update_distribution_preview()
            except:
                pass
        self.sentences_spin.bind('<KeyRelease>', safe_update_preview)
        self.sentences_spin.bind('<<Increment>>', safe_update_preview)
        self.sentences_spin.bind('<<Decrement>>', safe_update_preview)
        self.single_sentences_spin.bind('<KeyRelease>', safe_update_preview)
        self.single_sentences_spin.bind('<<Increment>>', safe_update_preview)
        self.single_sentences_spin.bind('<<Decrement>>', safe_update_preview)
        
        self.update_distribution_preview()
        
    def run_update_check(self):
        """Query the remote VERSION_CHECK_URL and notify if a new update is found."""
        try:
            # Add a cache-buster query parameter to force GitHub to bypass its 5-minute raw cache
            nocache_url = f"{VERSION_CHECK_URL}?nocache={uuid.uuid4()}"
            req = urllib.request.Request(
                nocache_url, 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get("latest_version")
                download_url = data.get("download_url")
                mandatory = data.get("mandatory_update", False)
                changelog = data.get("changelog", "")
                
                if not latest_version:
                    return

                # Compare version numbers (e.g. "1.0.0" -> [1, 0, 0])
                current_parts = [int(x) for x in CURRENT_VERSION.split('.')]
                latest_parts = [int(x) for x in latest_version.split('.')]
                
                if latest_parts > current_parts:
                    self.update_info = {
                        "version": latest_version,
                        "url": download_url,
                        "mandatory": mandatory,
                        "changelog": changelog
                    }
                    # Trigger GUI updates safely from background thread to main thread
                    self.root.after(10, self.show_update_notification)
        except Exception as e:
            # Silent background log so it doesn't break startup if user is offline
            print(f"Update check failed: {e}")

    def show_update_notification(self):
        """Display dialog/warning based on update priority."""
        if not self.update_info:
            return
            
        version = self.update_info["version"]
        url = self.update_info["url"]
        mandatory = self.update_info["mandatory"]
        changelog = self.update_info["changelog"]
        
        msg = f"A new version of this tool is available: v{version}\n"
        if changelog:
            msg += f"\nWhat's New:\n- {changelog}\n"
            
        if mandatory:
            msg += "\nThis is a mandatory update. You must update to continue using the application."
            messagebox.showwarning("Mandatory Update Required", msg)
            
            # Disable GUI execution
            self.start_button.config(state='disabled')
            self.status_label.config(text=f"🛑 UPDATE REQUIRED: Please download v{version}")
            self.log_message(f"🛑 Outdated version (v{CURRENT_VERSION}). v{version} is required!")
            
            # Show banner and auto-open download URL
            self.show_update_banner_in_gui(version, url)
            if url:
                webbrowser.open(url)
        else:
            # Standard friendly update banner inside the application
            self.show_update_banner_in_gui(version, url)
            self.log_message(f"🎁 A new update is available: v{version}!")
            
            # Ask user politely
            response = messagebox.askyesno(
                "Update Available",
                f"A new version (v{version}) is available!\n\n"
                f"Changelog:\n- {changelog}\n\n"
                "Would you like to open the download page now?"
            )
            if response and url:
                webbrowser.open(url)

    def show_update_banner_in_gui(self, version, url):
        """Draw a beautiful green alert banner at the top of the interface."""
        for widget in self.update_banner_frame.winfo_children():
            widget.destroy()
            
        style = ttk.Style()
        style.configure('UpdateBanner.TLabel', background='#1b4332', foreground='#2ec4b6', font=('Segoe UI', 10, 'bold'))
        
        banner_label = ttk.Label(
            self.update_banner_frame, 
            text=f"🎁 Update Available: v{version} (Your version: v{CURRENT_VERSION})", 
            style='UpdateBanner.TLabel',
            padding="8"
        )
        banner_label.pack(side='left', fill='x', expand=True)
        
        if url:
            download_btn = ttk.Button(
                self.update_banner_frame, 
                text="Download Now", 
                command=lambda: webbrowser.open(url)
            )
            download_btn.pack(side='right', padx=(10, 5))
            
    def create_profile_checkboxes(self):
        """Create checkboxes for each available profile."""
        # Clear existing checkboxes
        for widget in self.multi_select_scrollframe.winfo_children():
            widget.destroy()
        self.profile_checkboxes.clear()
        self.profile_vars.clear()
        
        # Create a checkbox for each profile
        for profile in self.available_profiles:
            var = tk.BooleanVar(value=True)  # Default: all selected
            self.profile_vars[profile] = var
            
            cb = ttk.Checkbutton(
                self.multi_select_scrollframe,
                text=profile,
                variable=var,
                command=self.update_distribution_preview
            )
            cb.pack(anchor='w', pady=2)
            self.profile_checkboxes[profile] = cb
    
    def get_selected_profiles(self):
        """Get list of selected profiles from checkboxes."""
        selected = []
        for profile, var in self.profile_vars.items():
            if var.get():
                selected.append(profile)
        return selected
    
    def get_edge_profiles(self):
        """Detect available Edge browser profiles on the system."""
        edge_data_paths = [
            os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data"),
            os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge Beta\\User Data"),
            os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge Dev\\User Data")
        ]
        profiles = []
        self.edge_data_path = None
        
        # Find the first valid Edge data path
        for data_path in edge_data_paths:
            if os.path.exists(data_path):
                self.edge_data_path = data_path
                self.log_message(f"✅ Found Edge installation at: {data_path}")
                break
        
        if not self.edge_data_path:
            self.log_message("❌ No Edge installation found!")
            return ["1 - Default Profile"]
        
        # Check for Default profile
        default_path = os.path.join(self.edge_data_path, "Default")
        if os.path.exists(default_path):
            # Verify it's a valid profile by checking for essential files
            if os.path.exists(os.path.join(default_path, "Preferences")) or \
               os.path.exists(os.path.join(default_path, "History")):
                profiles.append("1 - Default Profile")
                self.log_message("   ✓ Default Profile detected")
        
        # Check for numbered profiles (Profile 1, Profile 2, etc.)
        profile_dirs = glob.glob(os.path.join(self.edge_data_path, "Profile *"))
        for profile_dir in sorted(profile_dirs):
            profile_name = os.path.basename(profile_dir)
            if profile_name.startswith("Profile "):
                # Verify it's a valid profile
                if os.path.exists(os.path.join(profile_dir, "Preferences")) or \
                   os.path.exists(os.path.join(profile_dir, "History")):
                    profile_num = profile_name.split(" ")[1]
                    try:
                        display_num = int(profile_num) + 1
                        profiles.append(f"{display_num} - {profile_name}")
                        self.log_message(f"   ✓ {profile_name} detected")
                    except ValueError:
                        continue
        
        if not profiles:
            self.log_message("⚠️ No valid profiles found, using default")
            return ["1 - Default Profile"]
        
        return profiles
    
    def log_message(self, message):
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert('end', log_entry)
        self.log_text.see('end')
        self.root.update()
    
    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update()
    
    def update_progress(self, current, total):
        if total > 0:
            progress = (current / total) * 100
            self.progress_var.set(progress)
        self.root.update()
    
    def start_search(self):
        if not self.file_path.get():
            messagebox.showerror("Error", "Please select a text file!")
            return
        if not os.path.exists(self.file_path.get()):
            messagebox.showerror("Error", "Selected file does not exist!")
            return
        if not self.profile_var.get():
            messagebox.showerror("Error", "Please select an Edge profile!")
            return
        if self.total_sentences == 0:
            messagebox.showerror("Error", "The selected file contains no sentences!")
            return
        self.is_running = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress_var.set(0)
        self.log_text.delete('1.0', 'end')
        self.search_thread = threading.Thread(target=self.run_search, daemon=True)
        self.search_thread.start()
    
    def stop_search(self):
        self.is_running = False
        self.log_message("🛑 Stopping search...")
        self.update_status("Stopping...")
        try:
            winsound.PlaySound("SystemExclamation", winsound.SND_alias)
        except:
            pass
    
    def run_search(self):
        try:
            profile_selection = self.profile_var.get()
            
            with open(self.file_path.get(), 'r', encoding='utf-8') as file:
                content = file.read()
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            # Custom selection mode
            if "CUSTOM" in profile_selection.upper():
                selected_profiles = self.get_selected_profiles()
                if not selected_profiles:
                    messagebox.showerror("Error", "Please select at least one profile!")
                    return
                self.run_custom_profiles(lines, selected_profiles)
            # All profiles mode
            elif profile_selection.startswith("0"):
                self.run_all_profiles(lines)
            # Single profile mode
            else:
                profile_number = int(profile_selection.split(" - ")[0])
                try:
                    sentences_to_search = self.single_account_sentences.get()
                except:
                    sentences_to_search = 30
                sentences_to_search = min(sentences_to_search, len(lines))
                selected_lines = lines[:sentences_to_search]
                self.run_single_profile(selected_lines, profile_number)
        except Exception as e:
            self.log_message(f"❌ Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.is_running = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            # Ensure the Selenium driver is safely quit and process is closed
            try:
                if hasattr(self, 'driver') and self.driver:
                    self.log_message("🔌 Closing browser session...")
                    self.driver.quit()
                    self.driver = None
            except:
                pass
    
    def run_all_profiles(self, lines):
        self.log_message("🔄 Starting ALL PROFILES mode...")
        self.update_status("Running all profiles...")
        try:
            sentences_per_profile = self.sentences_per_account.get()
        except:
            sentences_per_profile = 30
        total_profiles = len(self.available_profiles)
        total_available = len(lines)
        max_possible_per_profile = total_available // total_profiles if total_profiles > 0 else 0
        actual_per_profile = min(sentences_per_profile, max_possible_per_profile)
        if actual_per_profile < sentences_per_profile:
            self.log_message(f"⚠️ Adjusted to {actual_per_profile} sentences per profile (file limitation)")
        current_index = 0
        for profile_idx, profile_info in enumerate(self.available_profiles, 1):
            if not self.is_running:
                break
            profile_number = int(profile_info.split(" - ")[0])
            end_index = min(current_index + actual_per_profile, len(lines))
            profile_lines = lines[current_index:end_index]
            if not profile_lines:
                self.log_message(f"⚠️ No more sentences for Profile {profile_number}")
                break
            self.log_message(f"🚀 Starting Profile {profile_number} - Sentences {current_index + 1} to {end_index}")
            self.update_status(f"Profile {profile_number} of {total_profiles}")
            self.run_single_profile(profile_lines, profile_number, is_multi_profile=True)
            current_index = end_index
            if profile_idx < total_profiles and self.is_running:
                self.log_message(f"✅ Profile {profile_number} completed!")
                
                # Close Edge browser before switching to next profile
                self.log_message("🔄 Closing browser to switch profiles...")
                try:
                    if hasattr(self, 'driver') and self.driver:
                        self.driver.quit()
                        self.driver = None
                    time.sleep(2)
                except:
                    pass
                
                try:
                    winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
                except:
                    pass
                self.log_message("⏱️ 3 second break before next profile...")
                for i in range(3):
                    if not self.is_running:
                        break
                    time.sleep(1)
        if self.is_running:
            self.log_message("🎉 ALL PROFILES COMPLETED!")
            self.update_status("All profiles completed!")
            try:
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
                time.sleep(0.5)
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
            except:
                pass
    
    def run_custom_profiles(self, lines, selected_profiles):
        """Run searches through custom selected profiles."""
        self.log_message("🔄 Starting CUSTOM SELECTION mode...")
        self.update_status("Running selected profiles...")
        
        try:
            sentences_per_profile = self.sentences_per_account.get()
        except:
            sentences_per_profile = 30
        
        total_profiles = len(selected_profiles)
        total_available = len(lines)
        max_possible_per_profile = total_available // total_profiles if total_profiles > 0 else 0
        actual_per_profile = min(sentences_per_profile, max_possible_per_profile)
        
        if actual_per_profile < sentences_per_profile:
            self.log_message(f"⚠️ Adjusted to {actual_per_profile} sentences per profile (file limitation)")
        
        profile_list = ", ".join([p.split(" - ")[0] for p in selected_profiles])
        self.log_message(f"📋 Selected profiles: {profile_list}")
        
        current_index = 0
        for profile_idx, profile_info in enumerate(selected_profiles, 1):
            if not self.is_running:
                break
            
            profile_number = int(profile_info.split(" - ")[0])
            end_index = min(current_index + actual_per_profile, len(lines))
            profile_lines = lines[current_index:end_index]
            
            if not profile_lines:
                self.log_message(f"⚠️ No more sentences for Profile {profile_number}")
                break
            
            self.log_message(f"🚀 Starting Profile {profile_number} - Sentences {current_index + 1} to {end_index}")
            self.update_status(f"Profile {profile_number} ({profile_idx}/{total_profiles})")
            
            self.run_single_profile(profile_lines, profile_number, is_multi_profile=True)
            
            current_index = end_index
            
            if profile_idx < total_profiles and self.is_running:
                self.log_message(f"✅ Profile {profile_number} completed!")
                
                # Close Edge browser before switching to next profile
                self.log_message("🔄 Closing browser to switch profiles...")
                try:
                    if hasattr(self, 'driver') and self.driver:
                        self.driver.quit()
                        self.driver = None
                    time.sleep(2)
                except:
                    pass
                
                try:
                    winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
                except:
                    pass
                self.log_message("⏱️ 3 second break before next profile...")
                for i in range(3):
                    if not self.is_running:
                        break
                    time.sleep(1)
        
        if self.is_running:
            self.log_message("🎉 CUSTOM SELECTION COMPLETED!")
            self.update_status("Selected profiles completed!")
            try:
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
                time.sleep(0.5)
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
            except:
                pass
    
    def close_tabs(self):
        """Closes all tabs except the first/current one using Selenium."""
        try:
            if hasattr(self, 'driver') and self.driver:
                original_handle = self.driver.current_window_handle
                handles = self.driver.window_handles
                for handle in handles:
                    if handle != original_handle:
                        self.driver.switch_to.window(handle)
                        self.driver.close()
                self.driver.switch_to.window(original_handle)
                self.log_message("✅ Secondary tabs closed successfully.")
        except Exception as e:
            self.log_message(f"❌ Error closing tabs: {str(e)}")
    
    def type_human_like(self, element, text, typing_delay):
        """Type text character by character with human-like delays into a Selenium element."""
        try:
            for char in text:
                element.send_keys(char)
                # Add variable delay to simulate human typing
                actual_delay = typing_delay + random.uniform(-0.02, 0.03)
                actual_delay = max(0.01, actual_delay)  # Ensure minimum delay
                time.sleep(actual_delay)
            return True
        except Exception as e:
            self.log_message(f"❌ Error typing: {str(e)}")
            return False
    
    def search_in_current_tab(self, search_term, typing_delay):
        """Perform search in the current active tab by typing in the search box."""
        try:
            # Check if we are currently on Bing, otherwise load it
            if not hasattr(self, 'driver') or not self.driver:
                return False
                
            if "bing.com" not in self.driver.current_url:
                self.driver.get("https://www.bing.com")
                time.sleep(2)
            
            # Locate search box by name 'q' (standard Bing search box input)
            try:
                search_box = self.driver.find_element(By.NAME, "q")
                search_box.clear()
                time.sleep(0.3)
                
                # Type using human-like delays
                self.type_human_like(search_box, search_term, typing_delay)
                time.sleep(0.3)
                
                # Submit search
                search_box.send_keys(Keys.ENTER)
                return True
            except Exception as elem_err:
                # Fallback: direct navigation to search URL
                self.log_message("⚠️ Bing search input element not found. Running direct search query fallback...")
                search_url = f"https://www.bing.com/search?q={urllib.parse.quote_plus(search_term)}"
                self.driver.get(search_url)
                return True
        except Exception as e:
            self.log_message(f"❌ Error performing search: {str(e)}")
            return False
    
    def run_single_profile(self, lines, profile_number, is_multi_profile=False):
        if not is_multi_profile:
            self.log_message(f"🚀 Starting search with Profile {profile_number}...")
        
        total_lines = len(lines)
        delay = self.delay_var.get()
        typing_delay = self.typing_delay_var.get()
        
        # Determine profile directory
        if profile_number == 1:
            profile_dir = "Default"
        elif profile_number == 2:
            profile_dir = "Profile 1"
        else:
            profile_dir = f"Profile {profile_number - 1}"
            
        self.log_message(f"🌐 Launching Edge with Profile: {profile_dir}...")
        
        options = Options()
        
        # Point to the actual user data directory to preserve profile states/cookies
        if hasattr(self, 'edge_data_path') and self.edge_data_path:
            options.add_argument(f"--user-data-dir={self.edge_data_path}")
        else:
            default_data_path = os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data")
            options.add_argument(f"--user-data-dir={default_data_path}")
            
        options.add_argument(f"--profile-directory={profile_dir}")
        
        # Add headless mode if checked
        if self.headless_var.get():
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            self.log_message("👁️ Running in HEADLESS mode (invisible browser window)")
            
        # Standard performance arguments
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--remote-debugging-port=0")  # Avoid DevTools port conflicts in headless mode
        options.add_argument("--disable-extensions")  # Disable extensions to prevent crashes in headless mode
        
        # Exclude automation switch to prevent detection banners
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        try:
            # Selenium 4.6+ automatically manages the driver executable
            self.driver = webdriver.Edge(options=options)
            self.driver.set_page_load_timeout(30)
            self.log_message("✅ Browser opened, loading Bing...")
            self.driver.get("https://www.bing.com")
            time.sleep(3)
        except Exception as e:
            self.log_message(f"❌ Error launching Edge driver: {e}")
            
            # Check for profile lock signatures in error message
            error_str = str(e).lower()
            if "chrome instance exited" in error_str or "already in use" in error_str or "session not created" in error_str:
                response = messagebox.askyesno(
                    "Edge Profile Locked",
                    "Microsoft Edge appears to be running (either actively or as a background Startup Boost process).\n\n"
                    "Selenium cannot automate Edge while your profile is locked by another running Edge session.\n\n"
                    "Would you like to automatically close all running Microsoft Edge processes and retry?"
                )
                if response:
                    self.log_message("🔄 Closing background Edge processes...")
                    try:
                        # Close Edge and EdgeDriver processes using taskkill
                        subprocess.run(["taskkill", "/f", "/im", "msedge.exe"], 
                                       stdout=subprocess.DEVNULL, 
                                       stderr=subprocess.DEVNULL)
                        subprocess.run(["taskkill", "/f", "/im", "msedgedriver.exe"], 
                                       stdout=subprocess.DEVNULL, 
                                       stderr=subprocess.DEVNULL)
                        
                        # Remove stale lock files inside the profile directory
                        try:
                            profile_path = self.edge_data_path if hasattr(self, 'edge_data_path') and self.edge_data_path else os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data")
                            lock_file = os.path.join(profile_path, profile_dir, "SingletonLock")
                            if os.path.exists(lock_file):
                                os.remove(lock_file)
                                self.log_message("✓ Stale profile lock file removed.")
                        except Exception as lock_err:
                            print(f"Lock file removal skipped: {lock_err}")
                            
                        time.sleep(2.5) # Wait for locks to fully release
                        
                        self.log_message("🔄 Retrying browser launch...")
                        self.driver = webdriver.Edge(options=options)
                        self.driver.set_page_load_timeout(30)
                        self.log_message("✅ Browser opened on retry, loading Bing...")
                        self.driver.get("https://www.bing.com")
                        time.sleep(3)
                        # Succeeded on retry, proceed!
                    except Exception as retry_err:
                        self.log_message(f"❌ Retry failed: {retry_err}")
                        self.log_message("💡 Tips: Make sure ALL Microsoft Edge browser windows are closed before running, as Edge locks the profile when open.")
                        return
                else:
                    return
            else:
                self.log_message("💡 Tips: Make sure ALL Microsoft Edge browser windows are closed before running, as Edge locks the profile when open.")
                return
            
        # Process each sentence in the same tab
        for i, sentence in enumerate(lines, 1):
            if not self.is_running:
                break
            
            if not is_multi_profile:
                self.update_progress(i, total_lines)
                self.update_status(f"Searching {i}/{total_lines}")
            
            search_term = sentence.strip()
            search_preview = search_term[:50] + "..." if len(search_term) > 50 else search_term
            self.log_message(f"[{i}/{total_lines}] Typing: {search_preview}")
            
            # Perform search in current tab with human-like typing
            success = self.search_in_current_tab(search_term, typing_delay)
            
            if not success:
                self.log_message(f"⚠️ Failed to search sentence {i}, skipping...")
            
            # Wait before next search (if not the last one)
            if i < total_lines and self.is_running:
                self.log_message(f"⏱️ Waiting {delay} seconds before next search...")
                for _ in range(delay):
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
        # Clean up browser driver if single-profile run completes or gets stopped
        if (not is_multi_profile or not self.is_running) and hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
                self.driver = None
            except:
                pass
        
        if not is_multi_profile and self.is_running:
            self.log_message("✅ Search completed!")
            self.update_status("Search completed!")
            self.update_progress(total_lines, total_lines)
            try:
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
            except:
                pass

def main():
    root = tk.Tk()
    app = EdgeSearchGUI(root)
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    root.mainloop()

if __name__ == "__main__":
    main()