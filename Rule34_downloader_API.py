import tkinter as tk
from tkinter import filedialog, scrolledtext
import customtkinter as ctk
import threading
import time
import requests
from urllib.parse import quote
import os
import json
import sys
import ctypes

# ================== CONFIG ==================
API_URL = "https://api.rule34.xxx/index.php?page=dapi&s=post&q=index"
NEW_STATE_FILE = "config_state.json"
OLD_STATE_FILE = "download_state.json"
DELAY_BETWEEN_PAGES = 2 
ICON_NAME = "icon.ico"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

try:
    myappid = 'archiver.r34.pro.v2.1' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green") 

class DownloaderGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("R34 Pro Archiver (JSON API)")
        self.geometry("1000x750")
        self.resizable(False, True)
        
        if os.path.exists(resource_path(ICON_NAME)):
            self.iconbitmap(resource_path(ICON_NAME))
        
        self.is_running = False
        self.thread = None
        self.current_page = 1
        self.downloaded_ids = set() 
        self.download_dir = os.getcwd()

        self.setup_ui()
        self.migrate_and_load()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=5, sticky="nsew", padx=(0, 20))
        self.sidebar.grid_propagate(False)
        
        ctk.CTkLabel(self.sidebar, text="AUTH (Required)", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 5))
        
        # User ID Input
        ctk.CTkLabel(self.sidebar, text="User ID:").pack(anchor="w", padx=20)
        self.uid_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Your User ID")
        self.uid_entry.pack(fill="x", padx=20, pady=(0, 10))

        # API Key Input
        ctk.CTkLabel(self.sidebar, text="API Key:").pack(anchor="w", padx=20)
        self.key_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Your API Key", show="*")
        self.key_entry.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkFrame(self.sidebar, height=2, fg_color="gray30").pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(self.sidebar, text="SEARCH", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # Tag Input
        ctk.CTkLabel(self.sidebar, text="Tags:").pack(anchor="w", padx=20)
        self.tag_entry = ctk.CTkEntry(self.sidebar, placeholder_text="e.g. sakura_haruno -video")
        self.tag_entry.pack(fill="x", padx=20, pady=(0, 5))
        
        # Page Input
        ctk.CTkLabel(self.sidebar, text="Start Page:").pack(anchor="w", padx=20)
        self.page_entry = ctk.CTkEntry(self.sidebar, width=100)
        self.page_entry.insert(0, "1")
        self.page_entry.pack(anchor="w", padx=20, pady=(0, 15))

        # Delay Slider
        self.delay_label = ctk.CTkLabel(self.sidebar, text="Delay: 5s")
        self.delay_label.pack(anchor="w", padx=20)
        self.delay_var = tk.IntVar(value=5)
        self.delay_slider = ctk.CTkSlider(self.sidebar, from_=1, to=30, number_of_steps=29, variable=self.delay_var, command=self.update_delay_label)
        self.delay_slider.pack(fill="x", padx=20, pady=(0, 20))

        # Folder Selection
        ctk.CTkLabel(self.sidebar, text="Location:").pack(anchor="w", padx=20)
        self.path_label = ctk.CTkLabel(self.sidebar, text=self.download_dir, font=ctk.CTkFont(size=10), wraplength=250, text_color="gray")
        self.path_label.pack(anchor="w", padx=20)
        self.browse_btn = ctk.CTkButton(self.sidebar, text="📁 Browse Folder", command=self.browse_folder, fg_color="transparent", border_width=1)
        self.browse_btn.pack(fill="x", padx=20, pady=10)

        # --- Main View ---
        self.stat_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stat_frame.grid(row=0, column=1, sticky="ew", pady=(20, 10), padx=20)
        
        self.page_stat = ctk.CTkLabel(self.stat_frame, text="Page: 1", font=ctk.CTkFont(size=16, weight="bold"))
        self.page_stat.pack(side="left", padx=20)
        
        self.count_stat = ctk.CTkLabel(self.stat_frame, text="History: 0", font=ctk.CTkFont(size=16, weight="bold"))
        self.count_stat.pack(side="left", padx=20)

        self.ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.ctrl_frame.grid(row=1, column=1, sticky="ew", padx=20, pady=10)

        self.start_btn = ctk.CTkButton(self.ctrl_frame, text="START / RESUME", font=ctk.CTkFont(weight="bold"), height=45, command=self.toggle_download)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.stop_btn = ctk.CTkButton(self.ctrl_frame, text="STOP", height=45, width=100, fg_color="#922", hover_color="#711", command=self.stop_download)
        self.stop_btn.pack(side="left")

        self.log_text = scrolledtext.ScrolledText(self, bg="#111", fg="#4ade80", font=("Consolas", 10), borderwidth=0, padx=10, pady=10)
        self.log_text.grid(row=4, column=1, sticky="nsew", padx=20, pady=(0, 20))

    def update_delay_label(self, value):
        self.delay_label.configure(text=f"Delay: {int(value)}s")

    def browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.download_dir = path
            self.path_label.configure(text=path)
            self.save_state()

    def log(self, message):
        self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see("end")

    def migrate_and_load(self):
        self.tag_entry.delete(0, "end")
        if os.path.exists(NEW_STATE_FILE):
            try:
                with open(NEW_STATE_FILE, "r") as f:
                    data = json.load(f)
                    self.current_page = data.get("page", 1)
                    self.download_dir = data.get("path", os.getcwd())
                    self.downloaded_ids = set(map(str, data.get("downloaded_ids", [])))
                    
                    self.uid_entry.insert(0, data.get("user_id", ""))
                    self.key_entry.insert(0, data.get("api_key", ""))
                    
                    saved_tags = data.get("tag", "").strip()
                    if saved_tags: self.tag_entry.insert(0, saved_tags)
            except Exception as e:
                self.log(f"Config load error: {e}")

        if os.path.exists(OLD_STATE_FILE):
            try:
                with open(OLD_STATE_FILE, "r") as f:
                    old_data = json.load(f)
                    old_ids = list(map(str, old_data.get("downloaded", [])))
                    self.downloaded_ids.update(old_ids)
                    if self.current_page == 1: self.current_page = old_data.get("page", 1)
                self.log(f"Migrated {len(old_ids)} IDs from legacy file.")
            except: pass

        self.page_entry.delete(0, "end")
        self.page_entry.insert(0, str(self.current_page))
        self.path_label.configure(text=self.download_dir)
        self.update_progress_stats()

    def save_state(self):
        try:
            state = {
                "page": int(self.page_entry.get()),
                "path": self.download_dir,
                "tag": self.tag_entry.get().strip(),
                "user_id": self.uid_entry.get().strip(),
                "api_key": self.key_entry.get().strip(),
                "downloaded_ids": list(self.downloaded_ids)
            }
            with open(NEW_STATE_FILE, "w") as f: json.dump(state, f, indent=2)
        except: pass

    def update_progress_stats(self):
        self.page_stat.configure(text=f"Page: {self.current_page}")
        self.count_stat.configure(text=f"History: {len(self.downloaded_ids)}")

    def toggle_download(self):
        if self.is_running:
            self.is_running = False
            self.start_btn.configure(text="RESUME", fg_color=["#2fa572", "#106a43"])
        else:
            if not self.tag_entry.get().strip():
                self.log("❌ Error: Tag field is empty."); return
            if not self.uid_entry.get().strip() or not self.key_entry.get().strip():
                self.log("⚠ Warning: No API credentials. You may be blocked at high pages.")
            
            try:
                self.current_page = int(self.page_entry.get())
            except:
                self.log("❌ Invalid page number!"); return
                
            self.save_state()
            self.is_running = True
            self.start_btn.configure(text="PAUSE", fg_color="orange")
            self.thread = threading.Thread(target=self.download_worker, daemon=True)
            self.thread.start()

    def stop_download(self):
        self.is_running = False
        self.start_btn.configure(text="START / RESUME", fg_color=["#2fa572", "#106a43"])
        self.log("⏹ Stopped.")

    def download_worker(self):
        tag_input = self.tag_entry.get().strip()
        uid = self.uid_entry.get().strip()
        key = self.key_entry.get().strip()
        
        while self.is_running:
            delay = self.delay_var.get()
            try:
                self.log(f"🔍 API Fetch: Page {self.current_page}...")
                
                posts = self.get_api_data(self.current_page, tag_input, uid, key)

                if not posts:
                    self.log("✨ End of results or API limit reached.")
                    break

                for post in posts:
                    if not self.is_running: break
                    
                    pid = str(post.get('id'))
                    img_url = post.get('file_url')

                    if pid in self.downloaded_ids or self.file_exists_on_disk(pid):
                        self.downloaded_ids.add(pid); continue

                    try:
                        self.download_image(img_url, pid)
                        self.downloaded_ids.add(pid)
                        self.update_progress_stats()
                        self.log(f"✅ Saved {pid}")
                        
                        for _ in range(delay):
                            if not self.is_running: break
                            time.sleep(1)
                    except Exception as e:
                        self.log(f"❌ Error on {pid}: {e}")

                self.current_page += 1
                self.page_entry.delete(0, "end")
                self.page_entry.insert(0, str(self.current_page))
                self.save_state()
                time.sleep(DELAY_BETWEEN_PAGES)

            except Exception as e:
                self.log(f"🚨 API Error: {e}")
                time.sleep(5)

        self.is_running = False
        self.after(0, lambda: self.start_btn.configure(text="START / RESUME"))

    def get_api_data(self, page, tag_string, uid, key):
        params = {
            "tags": tag_string,
            "pid": page - 1,
            "limit": 42,
            "json": 1
        }
        
        if uid and key:
            params["user_id"] = uid
            params["api_key"] = key

        headers = {"User-Agent": "R34ProArchiver/2.0 (Windows NT 10.0)"}
        
        try:
            resp = requests.get(API_URL, params=params, headers=headers, timeout=30)
            if resp.status_code == 403:
                self.log("❌ 403 Forbidden: API key/ID might be wrong.")
                return []
            
            if not resp.text or resp.text.strip() == "" or resp.text.strip() == "[]":
                return []
                
            return resp.json()
        except Exception as e:
            self.log(f"Request failed: {e}")
            return []

    def file_exists_on_disk(self, pid):
        if not os.path.exists(self.download_dir): return False
        for file in os.listdir(self.download_dir):
            if file.startswith(str(pid)): return True
        return False

    def download_image(self, url, post_id):
        ext = url.split('.')[-1].split('?')[0]
        filepath = os.path.join(self.download_dir, f"{post_id}.{ext}")
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, stream=True, timeout=60)
        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)

if __name__ == "__main__":
    app = DownloaderGUI()
    app.mainloop()