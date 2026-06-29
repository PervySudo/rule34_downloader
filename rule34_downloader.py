import tkinter as tk
from tkinter import filedialog, scrolledtext
import customtkinter as ctk
import threading
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import os
import json
import sys
import ctypes

# ================== CONFIG ==================
BASE_URL = "https://rule34.xxx"
NEW_STATE_FILE = "config_state.json"
OLD_STATE_FILE = "download_state.json"
DELAY_BETWEEN_PAGES = 3
ICON_NAME = "icon.ico"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

try:
    myappid = 'mycompany.r34downloader.version1' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green") 

class DownloaderGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("R34 Pro Downloader")
        self.geometry("950x700")
        self.resizable(False, True)
        
        # --- SET ICON ---
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
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=5, sticky="nsew", padx=(0, 20))
        self.sidebar.grid_propagate(False)
        ctk.CTkLabel(self.sidebar, text="SETTINGS", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        ctk.CTkLabel(self.sidebar, text="Search Tags:").pack(anchor="w", padx=20)
        self.tag_entry = ctk.CTkEntry(self.sidebar, placeholder_text="e.g. sakura_haruno -cheating")
        self.tag_entry.pack(fill="x", padx=20, pady=(0, 5))
        ctk.CTkLabel(self.sidebar, text="Tip: Use - to exclude tags", font=ctk.CTkFont(size=10), text_color="#888").pack(anchor="w", padx=20, pady=(0, 10))
        ctk.CTkLabel(self.sidebar, text="Start at Page:").pack(anchor="w", padx=20)
        self.page_entry = ctk.CTkEntry(self.sidebar, width=100)
        self.page_entry.insert(0, "1")
        self.page_entry.pack(anchor="w", padx=20, pady=(0, 15))
        self.delay_label = ctk.CTkLabel(self.sidebar, text="Request Delay: 15s")
        self.delay_label.pack(anchor="w", padx=20)
        self.delay_var = tk.IntVar(value=15)
        self.delay_slider = ctk.CTkSlider(self.sidebar, from_=2, to=60, number_of_steps=58, variable=self.delay_var, command=self.update_delay_label)
        self.delay_slider.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkLabel(self.sidebar, text="Download Location:").pack(anchor="w", padx=20)
        self.path_label = ctk.CTkLabel(self.sidebar, text=self.download_dir, font=ctk.CTkFont(size=10), wraplength=220, text_color="gray")
        self.path_label.pack(anchor="w", padx=20)
        self.browse_btn = ctk.CTkButton(self.sidebar, text="📁 Browse Folder", command=self.browse_folder, fg_color="transparent", border_width=1)
        self.browse_btn.pack(fill="x", padx=20, pady=10)
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
        ctk.CTkLabel(self, text="Activity Log:", font=ctk.CTkFont(size=12)).grid(row=3, column=1, sticky="w", padx=25)
        self.log_text = scrolledtext.ScrolledText(self, bg="#111", fg="#4ade80", font=("Consolas", 10), borderwidth=0, padx=10, pady=10)
        self.log_text.grid(row=4, column=1, sticky="nsew", padx=20, pady=(0, 20))

    def update_delay_label(self, value):
        self.delay_label.configure(text=f"Request Delay: {int(value)}s")

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
        if os.path.exists(NEW_STATE_FILE):
            try:
                with open(NEW_STATE_FILE, "r") as f:
                    data = json.load(f)
                    self.current_page = data.get("page", 1)
                    self.download_dir = data.get("path", os.getcwd())
                    self.downloaded_ids = set(map(str, data.get("downloaded_ids", [])))
                    self.tag_entry.delete(0, "end")
                    self.tag_entry.insert(0, data.get("tag", "sakura_haruno"))
            except Exception as e:
                self.log(f"Config load error: {e}")
        if os.path.exists(OLD_STATE_FILE):
            try:
                with open(OLD_STATE_FILE, "r") as f:
                    old_data = json.load(f)
                    old_ids = list(map(str, old_data.get("downloaded", [])))
                    self.downloaded_ids.update(old_ids)
                    if self.current_page == 1: self.current_page = old_data.get("page", 1)
                self.log(f"Migrated {len(old_ids)} IDs from old save file.")
            except Exception as e: self.log(f"Migration error: {e}")
        self.page_entry.delete(0, "end")
        self.page_entry.insert(0, str(self.current_page))
        self.path_label.configure(text=self.download_dir)
        self.update_progress_stats()

    def save_state(self):
        try:
            state = {"page": int(self.page_entry.get()), "path": self.download_dir, "tag": self.tag_entry.get(), "downloaded_ids": list(self.downloaded_ids)}
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
            try: self.current_page = int(self.page_entry.get())
            except: self.log("❌ Invalid page!"); return
            self.is_running = True
            self.start_btn.configure(text="PAUSE", fg_color="orange")
            self.thread = threading.Thread(target=self.download_worker, daemon=True)
            self.thread.start()

    def stop_download(self):
        self.is_running = False
        self.start_btn.configure(text="START / RESUME", fg_color=["#2fa572", "#106a43"])

    def download_worker(self):
        tag_input = self.tag_entry.get().strip()
        while self.is_running:
            delay = self.delay_var.get()
            try:
                self.log(f"🔍 Searching Page {self.current_page}...")
                html = self.get_search_page(self.current_page, tag_input)
                post_ids = self.parse_post_ids(html)
                if not post_ids: self.log("✨ End of search."); break
                for pid in post_ids:
                    if not self.is_running: break
                    if pid in self.downloaded_ids or self.file_exists_on_disk(pid):
                        self.downloaded_ids.add(pid); continue
                    try:
                        url = self.get_original_url(pid)
                        if url:
                            self.download_image(url, pid)
                            self.downloaded_ids.add(pid)
                            self.update_progress_stats()
                            self.log(f"✅ Saved {pid}")
                        for _ in range(delay):
                            if not self.is_running: break
                            time.sleep(1)
                    except Exception as e: self.log(f"❌ Error {pid}: {e}")
                self.current_page += 1
                self.page_entry.delete(0, "end")
                self.page_entry.insert(0, str(self.current_page))
                self.save_state()
                time.sleep(DELAY_BETWEEN_PAGES)
            except Exception as e: self.log(f"🚨 Page Error: {e}"); time.sleep(5)
        self.is_running = False
        self.after(0, lambda: self.start_btn.configure(text="START / RESUME"))

    def file_exists_on_disk(self, pid):
        if not os.path.exists(self.download_dir): return False
        for file in os.listdir(self.download_dir):
            if file.startswith(str(pid)): return True
        return False

    def get_search_page(self, page, tag_string):
        formatted_tags = quote(tag_string).replace("%20", "+")
        url = f"{BASE_URL}/index.php?page=post&s=list&tags={formatted_tags}&pid={(page-1)*42}"
        return requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text

    def parse_post_ids(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        return [thumb.find('a')['href'].split('id=')[-1] for thumb in soup.select('span.thumb')]

    def get_original_url(self, post_id):
        url = f"{BASE_URL}/index.php?page=post&s=view&id={post_id}"
        soup = BeautifulSoup(requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text, 'html.parser')
        orig = soup.find('a', string=lambda t: t and "Original image" in t)
        if orig: return urljoin(BASE_URL, orig['href'])
        img = soup.find('img', id='image')
        return urljoin(BASE_URL, img['src']) if img else None

    def download_image(self, url, post_id):
        ext = url.split('.')[-1].split('?')[0]
        filepath = os.path.join(self.download_dir, f"{post_id}.{ext}")
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, stream=True)
        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(8192): f.write(chunk)

if __name__ == "__main__":
    app = DownloaderGUI()
    app.mainloop()