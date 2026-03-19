"""
AlzHelp - Patient Recognition System
Modern GUI Application
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import os
import datetime
import base64
import io

try:
    import cv2
    import face_recognition
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: cv2 or face_recognition not installed. Camera features disabled.")

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from db_connection import (
    get_db_connection,
    insert_patients,
    insert_contact,
    insert_relatives_contacts,
    get_patient_by_id,
    get_relatives_by_patient,
    update_relative_image,
    update_patient_last_login,
    delete_patient,
    delete_relative,
    create_events_table,
    get_events_for_month,
    get_events_for_day,
    insert_event,
    update_event,
    delete_event,
)
from patient_input import collect_relatives_contact
from image_handler import save_image_for_patient, capture_face_from_camera

# ─── Absolute Paths (always relative to this script file) ────────────────────
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
KNOWN_FACES_DIR = os.path.join(BASE_DIR, "known_faces")
UNKNOWN_DIR     = os.path.join(BASE_DIR, "unknown_faces")
RELATIVE_DIR    = os.path.join(BASE_DIR, "relative_images")

os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
os.makedirs(UNKNOWN_DIR,     exist_ok=True)
os.makedirs(RELATIVE_DIR,    exist_ok=True)

print(f"[Paths] known_faces    → {KNOWN_FACES_DIR}")
print(f"[Paths] unknown_faces  → {UNKNOWN_DIR}")
print(f"[Paths] relative_images→ {RELATIVE_DIR}")

# ─── Color Palette ───────────────────────────────────────────────────────────
BG_DARK      = "#0D1117"
BG_CARD      = "#161B22"
BG_SIDEBAR   = "#0D1117"
ACCENT_TEAL  = "#2DD4BF"
ACCENT_WARM  = "#FB923C"
TEXT_PRIMARY = "#F0F6FC"
TEXT_MUTED   = "#8B949E"
TEXT_DIM     = "#484F58"
BORDER       = "#30363D"
SUCCESS      = "#3FB950"
WARNING      = "#D29922"
DANGER       = "#F85149"

FONT_HEADING  = ("Georgia", 22, "bold")
FONT_SUBHEAD  = ("Georgia", 14)
FONT_LABEL    = ("Helvetica Neue", 11)
FONT_SMALL    = ("Helvetica Neue", 9)
FONT_MONO     = ("Courier New", 10)
FONT_CARD_TTL = ("Georgia", 13, "bold")
FONT_CARD_SUB = ("Helvetica Neue", 10)


# ─── Helpers ─────────────────────────────────────────────────────────────────
def make_round_frame(parent, bg, width, height, radius=16):
    """Return a Canvas that draws a rounded rectangle as background."""
    c = tk.Canvas(parent, width=width, height=height,
                  bg=parent["bg"], highlightthickness=0)
    x1, y1, x2, y2 = 0, 0, width, height
    r = radius
    c.create_polygon(
        x1+r, y1, x2-r, y1,
        x2, y1, x2, y1+r,
        x2, y2-r, x2, y2,
        x2-r, y2, x1+r, y2,
        x1, y2, x1, y2-r,
        x1, y1+r, x1, y1,
        smooth=True, fill=bg, outline=BORDER
    )
    return c


def avatar_label(parent, text, size=48, bg=BG_CARD, fg=ACCENT_TEAL):
    """Circular avatar with initials."""
    canvas = tk.Canvas(parent, width=size, height=size,
                       bg=parent["bg"], highlightthickness=0)
    canvas.create_oval(2, 2, size-2, size-2, fill=bg, outline=ACCENT_TEAL, width=2)
    canvas.create_text(size//2, size//2, text=text,
                       font=("Georgia", size//3, "bold"), fill=fg)
    return canvas


# ─── Main Application ─────────────────────────────────────────────────────────
class AlzheimerCareApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AlzHelp — Patient Recognition System")
        self.geometry("1200x780")
        self.configure(bg=BG_DARK)
        self.resizable(True, True)

        # State
        self.current_patient = None
        self.camera_thread = None
        self.camera_running = False
        self.cap = None
        self.known_face_encodings = []
        self.known_faces_names = []
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.last_recognized_name = None  # track who is currently shown in the info card

        # ── Performance: face recognition runs on its own thread ─────────────
        self._recog_thread    = None          # background recognition worker
        self._recog_queue     = queue.Queue(maxsize=1)  # latest frame to recognise
        self._result_queue    = queue.Queue()            # results back to UI thread
        self._frame_counter   = 0             # used for frame-skipping
        self._face_boxes      = []            # last known face boxes to draw every frame
        self._patient_cache   = {}            # name → patient dict, avoids repeat DB hits

        self._load_known_faces()
        try:
            create_events_table()
        except Exception as e:
            print(f"[Calendar] Could not create events table: {e}")
        self._build_ui()
        self.show_page("home")

    # ── Face Loading ─────────────────────────────────────────────────────────
    def _load_known_faces(self):
        if not CV2_AVAILABLE:
            return

        for filename in os.listdir(KNOWN_FACES_DIR):
            if filename.lower().endswith((".jpg", ".png", ".jpeg")):
                path = os.path.join(KNOWN_FACES_DIR, filename)
                image = face_recognition.load_image_file(path)
                encs = face_recognition.face_encodings(image)
                if encs:
                    self.known_face_encodings.append(encs[0])
                    self.known_faces_names.append(os.path.splitext(filename)[0])

    # ── UI Construction ──────────────────────────────────────────────────────
    def _build_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=BG_SIDEBAR, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        logo_frame.pack(fill="x", padx=20, pady=(28, 10))
        tk.Label(logo_frame, text="◈", font=("Georgia", 24), fg=ACCENT_TEAL,
                 bg=BG_SIDEBAR).pack(side="left")
        tk.Label(logo_frame, text=" AlzFocus", font=("Georgia", 18, "bold"),
                 fg=TEXT_PRIMARY, bg=BG_SIDEBAR).pack(side="left")

        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=20, pady=12)

        # Nav items
        self.nav_buttons = {}
        nav_items = [
            ("home",      "⌂  Home",             "Recognize Patient"),
            ("register",  "＋  Register",          "New Patient"),
            ("patient",   "♥  Patient Info",       "View Details"),
            ("relatives", "◉  Relatives",          "Family Members"),
            ("calendar",  "▦  Calendar",           "Patient Schedule"),
        ]
        for key, label, sub in nav_items:
            self._nav_button(key, label, sub)

        # Bottom section
        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=20, pady=12, side="bottom")
        status_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        status_frame.pack(side="bottom", fill="x", padx=16, pady=10)
        self.status_dot = tk.Label(status_frame, text="●", fg=SUCCESS, bg=BG_SIDEBAR,
                                   font=("Helvetica", 9))
        self.status_dot.pack(side="left")
        tk.Label(status_frame, text=" System Active", fg=TEXT_MUTED, bg=BG_SIDEBAR,
                 font=FONT_SMALL).pack(side="left")

        # Content area
        self.content = tk.Frame(self, bg=BG_DARK)
        self.content.pack(side="right", fill="both", expand=True)

        # Pages dict
        self.pages = {}

    def _nav_button(self, key, label, sub):
        f = tk.Frame(self.sidebar, bg=BG_SIDEBAR, cursor="hand2")
        f.pack(fill="x", padx=10, pady=2)

        lbl = tk.Label(f, text=label, font=("Helvetica Neue", 11, "bold"),
                       fg=TEXT_MUTED, bg=BG_SIDEBAR, anchor="w", padx=14, pady=8)
        lbl.pack(fill="x")

        def on_enter(e, fl=f, ll=lbl):
            fl.config(bg="#1C2128")
            ll.config(bg="#1C2128", fg=TEXT_PRIMARY)

        def on_leave(e, fl=f, ll=lbl, k=key):
            is_active = (self.active_page == k if hasattr(self, 'active_page') else False)
            fl.config(bg="#1a3344" if is_active else BG_SIDEBAR)
            ll.config(bg="#1a3344" if is_active else BG_SIDEBAR,
                      fg=ACCENT_TEAL if is_active else TEXT_MUTED)

        def on_click(e, k=key):
            self.show_page(k)

        f.bind("<Enter>", on_enter)
        f.bind("<Leave>", on_leave)
        f.bind("<Button-1>", on_click)
        lbl.bind("<Enter>", on_enter)
        lbl.bind("<Leave>", on_leave)
        lbl.bind("<Button-1>", on_click)

        self.nav_buttons[key] = (f, lbl)

    def show_page(self, key):
        self.active_page = key

        # Update nav highlighting
        for k, (f, l) in self.nav_buttons.items():
            if k == key:
                f.config(bg="#1a3344")
                l.config(bg="#1a3344", fg=ACCENT_TEAL)
            else:
                f.config(bg=BG_SIDEBAR)
                l.config(bg=BG_SIDEBAR, fg=TEXT_MUTED)

        # Clear content
        for w in self.content.winfo_children():
            w.destroy()

        pages = {
            "home":      self._build_home_page,
            "register":  self._build_register_page,
            "patient":   self._build_patient_page,
            "relatives": self._build_relatives_page,
            "calendar":  self._build_calendar_page,
        }
        if key in pages:
            pages[key]()

    # ── Page: Home (Camera / Recognition) ────────────────────────────────────
    def _build_home_page(self):
        page = tk.Frame(self.content, bg=BG_DARK)
        page.pack(fill="both", expand=True, padx=30, pady=25)

        # Header
        hdr = tk.Frame(page, bg=BG_DARK)
        hdr.pack(fill="x", pady=(0, 20))
        tk.Label(hdr, text="Patient Recognition", font=FONT_HEADING,
                 fg=TEXT_PRIMARY, bg=BG_DARK).pack(side="left")
        tk.Label(hdr, text=f"  {datetime.datetime.now().strftime('%B %d, %Y')}",
                 font=FONT_LABEL, fg=TEXT_MUTED, bg=BG_DARK).pack(side="left", pady=6)

        body = tk.Frame(page, bg=BG_DARK)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # Camera panel
        cam_card = tk.Frame(body, bg=BG_CARD, bd=0)
        cam_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        cam_header = tk.Frame(cam_card, bg=BG_CARD)
        cam_header.pack(fill="x", padx=20, pady=(16, 8))
        tk.Label(cam_header, text="Live Camera Feed", font=FONT_CARD_TTL,
                 fg=TEXT_PRIMARY, bg=BG_CARD).pack(side="left")
        self.cam_status_lbl = tk.Label(cam_header, text="● Inactive",
                                        font=FONT_SMALL, fg=TEXT_DIM, bg=BG_CARD)
        self.cam_status_lbl.pack(side="right")

        # Camera canvas
        self.cam_canvas = tk.Canvas(cam_card, bg="#080C10",
                                     width=480, height=340,
                                     highlightthickness=0)
        self.cam_canvas.pack(padx=20, pady=(0, 12))
        self._draw_camera_placeholder()

        # Camera controls
        ctrl = tk.Frame(cam_card, bg=BG_CARD)
        ctrl.pack(fill="x", padx=20, pady=(0, 16))

        self.cam_btn = self._styled_button(
            ctrl, "▶  Start Camera", self._toggle_camera,
            bg=ACCENT_TEAL, fg=BG_DARK
        )
        self.cam_btn.pack(side="left", padx=(0, 8))

        self._styled_button(ctrl, "Register Face (R)", self._manual_register,
                             bg=BG_DARK, fg=TEXT_MUTED, outline=True).pack(side="left")

        # Right panel: recognized patient
        right = tk.Frame(body, bg=BG_DARK)
        right.grid(row=0, column=1, sticky="nsew")

        tk.Label(right, text="Recognized Patient", font=FONT_CARD_TTL,
                 fg=TEXT_MUTED, bg=BG_DARK).pack(anchor="w", pady=(8, 12))

        self.recognized_card = tk.Frame(right, bg=BG_CARD)
        self.recognized_card.pack(fill="both", expand=True)
        self._draw_no_patient_card(self.recognized_card)

        # Instructions
        instr = tk.Frame(right, bg="#0D1F2D")
        instr.pack(fill="x", pady=(12, 0))
        tk.Label(instr, text="  Keyboard Shortcuts", font=("Helvetica Neue", 9, "bold"),
                 fg=ACCENT_TEAL, bg="#0D1F2D", anchor="w").pack(fill="x", padx=12, pady=(6,2))
        for tip in [
            "R — Register face in frame",
            "Q — Stop camera",
            "Space — Save snapshot",
        ]:
            tk.Label(instr, text=f"  {tip}", font=FONT_SMALL, fg=TEXT_MUTED,
                     bg="#0D1F2D", anchor="w").pack(fill="x", padx=12, pady=1)

    def _load_patient_photo(self, patient, size=(90, 90)):
        """Try to load the patient's face photo from known_faces/. Returns ImageTk.PhotoImage or None."""
        if not PIL_AVAILABLE:
            return None
        first = patient.get("first_name", "")
        last  = patient.get("last_name", "")
        # Check common filename patterns
        candidates = [
            os.path.join(KNOWN_FACES_DIR, f"{first} {last}.jpg"),
            os.path.join(KNOWN_FACES_DIR, f"{first} {last}.jpeg"),
            os.path.join(KNOWN_FACES_DIR, f"{first} {last}.png"),
            os.path.join(KNOWN_FACES_DIR, f"{first}_{last}.jpg"),
        ]
        # Also scan the folder for any filename containing their full name
        try:
            for fname in os.listdir(KNOWN_FACES_DIR):
                fpath = os.path.join(KNOWN_FACES_DIR, fname)
                if fpath not in candidates and (
                    first.lower() in fname.lower() and last.lower() in fname.lower()
                ):
                    candidates.append(fpath)
        except Exception:
            pass

        for path in candidates:
            if os.path.exists(path):
                try:
                    img = Image.open(path).convert("RGB")
                    # Crop to square from center before resizing
                    w, h = img.size
                    min_dim = min(w, h)
                    left  = (w - min_dim) // 2
                    top   = (h - min_dim) // 2
                    img   = img.crop((left, top, left + min_dim, top + min_dim))
                    img   = img.resize(size, Image.LANCZOS)
                    return ImageTk.PhotoImage(img)
                except Exception as e:
                    print(f"[Photo] Could not load {path}: {e}")
        return None

    def _draw_camera_placeholder(self):
        self.cam_canvas.delete("all")
        self.cam_canvas.create_rectangle(0, 0, 480, 340, fill="#080C10", outline="")
        # Grid lines
        for x in range(0, 480, 40):
            self.cam_canvas.create_line(x, 0, x, 340, fill="#0F1820", width=1)
        for y in range(0, 340, 40):
            self.cam_canvas.create_line(0, y, 480, y, fill="#0F1820", width=1)
        # Center icon
        self.cam_canvas.create_text(240, 155, text="◎", font=("Helvetica", 48),
                                     fill=TEXT_DIM)
        self.cam_canvas.create_text(240, 215, text="Camera Inactive",
                                     font=FONT_SUBHEAD, fill=TEXT_DIM)
        self.cam_canvas.create_text(240, 240, text="Press 'Start Camera' to begin",
                                     font=FONT_SMALL, fill=TEXT_DIM)

    def _draw_no_patient_card(self, parent):
        for w in parent.winfo_children():
            w.destroy()
        tk.Label(parent, text="◉", font=("Helvetica", 36), fg=TEXT_DIM,
                 bg=BG_CARD).pack(pady=(40, 8))
        tk.Label(parent, text="No patient recognized yet",
                 font=FONT_LABEL, fg=TEXT_DIM, bg=BG_CARD).pack()
        tk.Label(parent, text="Start the camera and point it\nat a registered patient.",
                 font=FONT_SMALL, fg=TEXT_DIM, bg=BG_CARD, justify="center").pack(pady=6)

    def _draw_recognized_patient(self, patient_data):
        card = self.recognized_card
        for w in card.winfo_children():
            w.destroy()

        name = f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}"
        initials = (patient_data.get('first_name', '?')[0] +
                    patient_data.get('last_name', '?')[0]).upper()

        # ── Photo or initials avatar ──────────────────────────────────────────
        photo_img = self._load_patient_photo(patient_data, size=(90, 90))
        av_frame = tk.Frame(card, bg=BG_CARD)
        av_frame.pack(pady=(20, 8))
        if photo_img:
            lbl = tk.Label(av_frame, image=photo_img, bg=BG_CARD,
                           highlightthickness=2, highlightbackground=ACCENT_TEAL)
            lbl.pack()
            lbl._photo = photo_img          # prevent GC
        else:
            avatar_label(av_frame, initials, size=90).pack()

        tk.Label(card, text=name, font=("Georgia", 16, "bold"),
                 fg=TEXT_PRIMARY, bg=BG_CARD).pack()
        tk.Label(card, text=f"ID: {patient_data.get('personal_id', '—')}",
                 font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_CARD).pack()

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=20, pady=12)

        info_pairs = [
            ("Age", str(patient_data.get("age", "—"))),
            ("Sex", patient_data.get("sex", "—")),
            ("Phone", patient_data.get("phone_number", "—") or "—"),
            ("Email", patient_data.get("email", "—") or "—"),
            ("Last Login", str(patient_data.get("last_login", "—"))),
        ]
        for label, val in info_pairs:
            row = tk.Frame(card, bg=BG_CARD)
            row.pack(fill="x", padx=20, pady=2)
            tk.Label(row, text=label, font=FONT_SMALL, fg=TEXT_MUTED,
                     bg=BG_CARD, width=12, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=FONT_SMALL, fg=TEXT_PRIMARY,
                     bg=BG_CARD, anchor="w").pack(side="left")

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=20, pady=10)

        btn_frame = tk.Frame(card, bg=BG_CARD)
        btn_frame.pack(padx=20, pady=(0, 16))

        def go_to_patient():
            self.current_patient = patient_data
            self.show_page("patient")

        def go_to_relatives():
            self.current_patient = patient_data
            self.show_page("relatives")

        self._styled_button(btn_frame, "View Full Profile", go_to_patient,
                             bg=ACCENT_TEAL, fg=BG_DARK).pack(fill="x", pady=3)
        self._styled_button(btn_frame, "View Relatives", go_to_relatives,
                             bg=BG_DARK, fg=TEXT_MUTED, outline=True).pack(fill="x", pady=3)

    # ── Camera Logic ─────────────────────────────────────────────────────────
    def _toggle_camera(self):
        if self.camera_running:
            self._stop_camera()
        else:
            self._start_camera()

    def _start_camera(self):
        if not CV2_AVAILABLE:
            messagebox.showerror("Missing Library",
                                 "OpenCV (cv2) is required for camera features.")
            return

        # Show "Opening…" immediately so the UI doesn't feel frozen
        self.cam_btn.config(text="○  Opening…", bg=TEXT_DIM, fg=BG_DARK, state="disabled")
        self.cam_status_lbl.config(text="● Starting…", fg=WARNING)
        self.update_idletasks()

        # Open camera in a background thread so the UI stays responsive
        def open_camera():
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                cap = cv2.VideoCapture(1)

            # Set lower resolution for faster capture + recognition
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            # Limit internal buffer to 1 frame so we always get the freshest image
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Schedule the result back on the UI thread
            self.after(0, lambda: self._on_camera_opened(cap))

        threading.Thread(target=open_camera, daemon=True).start()

    def _on_camera_opened(self, cap):
        """Called on the UI thread once the camera has been opened."""
        if not cap.isOpened():
            messagebox.showerror("Camera Error", "No camera found.")
            self.cam_btn.config(text="▶  Start Camera", bg=ACCENT_TEAL,
                                fg=BG_DARK, state="normal")
            self.cam_status_lbl.config(text="● Inactive", fg=TEXT_DIM)
            return

        self.cap            = cap
        self.camera_running = True
        self._frame_counter = 0
        self._face_boxes    = []

        self.cam_btn.config(text="■  Stop Camera", bg=DANGER,
                            fg=TEXT_PRIMARY, state="normal")
        self.cam_status_lbl.config(text="● Active", fg=SUCCESS)

        # ── Bind keyboard shortcuts now that camera is live ───────────────────
        # Bind on the window itself so they work regardless of which widget has focus
        self.bind("<KeyPress-r>", self._key_register)
        self.bind("<KeyPress-R>", self._key_register)
        self.bind("<KeyPress-q>", self._key_quit_camera)
        self.bind("<KeyPress-Q>", self._key_quit_camera)
        self.bind("<space>",      self._key_capture)
        # Make sure the window can receive key events
        self.focus_set()

        # Thread 1: grabs frames from the camera as fast as possible
        self.camera_thread = threading.Thread(
            target=self._camera_loop, daemon=True)
        self.camera_thread.start()

        # Thread 2: runs face recognition in the background
        self._recog_thread = threading.Thread(
            target=self._recognition_loop, daemon=True)
        self._recog_thread.start()

        # UI loop: draws frames and picks up recognition results
        self._update_camera_frame()

    def _stop_camera(self):
        self.camera_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.last_recognized_name = None
        self._face_boxes = []

        # ── Remove key bindings when camera stops ─────────────────────────────
        for seq in ("<KeyPress-r>", "<KeyPress-R>",
                    "<KeyPress-q>", "<KeyPress-Q>", "<space>"):
            self.unbind(seq)

        # Drain queues so threads don't hang
        for q in (self._recog_queue, self._result_queue):
            while not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    break
        self.cam_btn.config(text="▶  Start Camera", bg=ACCENT_TEAL,
                            fg=BG_DARK, state="normal")
        self.cam_status_lbl.config(text="● Inactive", fg=TEXT_DIM)
        self._draw_camera_placeholder()

    # ── Keyboard shortcut handlers ────────────────────────────────────────────
    def _key_register(self, event=None):
        """R — register the face currently in frame."""
        if not self.camera_running:
            return
        with self.frame_lock:
            frame = self.latest_frame.copy() if self.latest_frame is not None else None
        if frame is None:
            messagebox.showwarning("No Frame", "No camera frame available.")
            return
        # Grab current face locations from the last recognition result
        face_locations = [box for box, _ in self._face_boxes] if self._face_boxes else []
        if not face_locations:
            messagebox.showwarning("No Face", "No face detected in frame.\nMake sure your face is visible.")
            return
        self._stop_camera()
        self.show_page("register")

    def _key_quit_camera(self, event=None):
        """Q — stop the camera."""
        if self.camera_running:
            self._stop_camera()

    def _key_capture(self, event=None):
        """Space — save a snapshot of the current frame."""
        if not self.camera_running:
            return
        with self.frame_lock:
            frame = self.latest_frame.copy() if self.latest_frame is not None else None
        if frame is None:
            return
        os.makedirs(UNKNOWN_DIR, exist_ok=True)
        filename  = datetime.datetime.now().strftime("snapshot_%Y-%m-%d_%H-%M-%S") + ".jpg"
        filepath  = os.path.join(UNKNOWN_DIR, filename)
        cv2.imwrite(filepath, frame)
        # Brief on-screen confirmation on the status label
        self.cam_status_lbl.config(text=f"📸 Saved!", fg=ACCENT_TEAL)
        self.after(2000, lambda: self.cam_status_lbl.config(
            text="● Active", fg=SUCCESS) if self.camera_running else None)
        print(f"[Snapshot] Saved to {filepath}")

    # ── Thread 1: capture frames ──────────────────────────────────────────────
    def _camera_loop(self):
        while self.camera_running and self.cap:
            ret, frame = self.cap.read()
            if ret:
                with self.frame_lock:
                    self.latest_frame = frame

    # ── Thread 2: face recognition worker ────────────────────────────────────
    def _recognition_loop(self):
        """
        Runs entirely off the UI thread.
        Pulls frames from _recog_queue, runs recognition, pushes results
        to _result_queue for the UI to pick up.
        """
        import numpy as np
        while self.camera_running:
            try:
                frame = self._recog_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            # ── Shrink to 1/4 size for much faster detection ─────────────────
            small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb   = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

            locations = face_recognition.face_locations(rgb)
            encodings = face_recognition.face_encodings(rgb, locations)

            results = []  # list of (box_full_scale, name)
            for (top, right, bottom, left), enc in zip(locations, encodings):
                # Scale coordinates back up to full frame size
                box = (top * 4, right * 4, bottom * 4, left * 4)
                name = "Unknown"
                if self.known_face_encodings:
                    dists    = face_recognition.face_distance(self.known_face_encodings, enc)
                    best_idx = int(np.argmin(dists))
                    if dists[best_idx] < 0.5:
                        name = self.known_faces_names[best_idx]
                results.append((box, name))

            # Only keep the latest result — drop stale ones
            while not self._result_queue.empty():
                try:
                    self._result_queue.get_nowait()
                except queue.Empty:
                    break
            self._result_queue.put(results)

    # ── UI loop: display frames + consume recognition results ─────────────────
    def _update_camera_frame(self):
        if not self.camera_running:
            return

        with self.frame_lock:
            frame = self.latest_frame.copy() if self.latest_frame is not None else None

        if frame is not None and PIL_AVAILABLE:
            self._frame_counter += 1

            # ── Every 4th frame: send to recognition thread (non-blocking) ───
            if self._frame_counter % 4 == 0:
                if self._recog_queue.empty():
                    try:
                        self._recog_queue.put_nowait(frame.copy())
                    except queue.Full:
                        pass

            # ── Pick up any finished recognition result ───────────────────────
            try:
                results = self._result_queue.get_nowait()
                self._face_boxes = results   # cache for drawing on every frame

                best_name = next(
                    (name for _, name in results if name != "Unknown"), None)

                if best_name != self.last_recognized_name:
                    self.last_recognized_name = best_name
                    if best_name:
                        patient = self._lookup_patient_by_name(best_name)
                        if patient:
                            self._draw_recognized_patient(patient)
                        else:
                            self._draw_no_patient_card(self.recognized_card)
                    else:
                        self._draw_no_patient_card(self.recognized_card)

            except queue.Empty:
                pass  # no new result yet — keep drawing cached boxes

            # ── Draw cached face boxes on the current frame every time ────────
            for (top, right, bottom, left), name in self._face_boxes:
                color = (45, 212, 191) if name != "Unknown" else (248, 81, 73)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 22), (right, bottom),
                              color, cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

            # ── Render frame to canvas ────────────────────────────────────────
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img   = Image.fromarray(frame_rgb).resize((480, 340), Image.NEAREST)
            photo = ImageTk.PhotoImage(img)
            self.cam_canvas.create_image(0, 0, anchor="nw", image=photo)
            self.cam_canvas._photo = photo

        self.after(30, self._update_camera_frame)  # ~33 fps display

    def _lookup_patient_by_name(self, name):
        """DB lookup with in-memory cache — only hits MySQL once per name per session."""
        if name in self._patient_cache:
            return self._patient_cache[name]
        try:
            parts = name.split()
            if len(parts) >= 2:
                from db_connection import get_patient_by_name
                results = get_patient_by_name(parts[0])
                if results:
                    self._patient_cache[name] = results[0]
                    return results[0]
        except Exception as e:
            print(f"Patient lookup error: {e}")
        self._patient_cache[name] = None
        return None

    def _manual_register(self):
        """Manual register button."""
        if not CV2_AVAILABLE:
            messagebox.showerror("Error", "cv2 not available.")
            return
        with self.frame_lock:
            frame = self.latest_frame.copy() if self.latest_frame is not None else None
        if frame is None:
            messagebox.showwarning("No Frame", "Start the camera first.")
            return
        self._open_register_dialog(frame)

    def _open_register_dialog(self, frame):
        """Open registration dialog for the current frame."""
        self._stop_camera()
        self.show_page("register")

    # ── Photo quality checker ─────────────────────────────────────────────────
    def _check_photo_quality(self, image_path):
        """
        Checks a photo for common problems that cause poor recognition.
        Returns (passed: bool, issues: list, score: int 0-100)
        """
        import numpy as np
        issues  = []
        score   = 100

        if not CV2_AVAILABLE:
            return True, [], 100

        img = cv2.imread(image_path)
        if img is None:
            return False, ["Could not read image file."], 0

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = img.shape[:2]

        # ── 1. Brightness check ───────────────────────────────────────────────
        brightness = float(np.mean(gray))
        if brightness < 50:
            issues.append("⚠  Too dark — move to a brighter area or turn on a light")
            score -= 30
        elif brightness > 220:
            issues.append("⚠  Too bright — avoid direct light behind the person")
            score -= 20

        # ── 2. Blur / sharpness check (Laplacian variance) ────────────────────
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if blur_score < 80:
            issues.append("⚠  Image is blurry — hold the camera steady and retake")
            score -= 35

        # ── 3. Face detection + size + centering ─────────────────────────────
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)

        if not locations:
            issues.append("✕  No face detected — make sure face is clearly visible")
            score -= 100
        elif len(locations) > 1:
            issues.append("⚠  Multiple faces detected — only one person should be in frame")
            score -= 20
        else:
            top, right, bottom, left = locations[0]
            face_w = right - left
            face_h = bottom - top
            face_area_ratio = (face_w * face_h) / (w * h)

            # Face too small
            if face_area_ratio < 0.08:
                issues.append("⚠  Face is too small — move closer to the camera")
                score -= 25

            # Face too close / cut off
            if face_area_ratio > 0.70:
                issues.append("⚠  Face is too close — move slightly further back")
                score -= 15

            # Face not centered (center of face vs center of image)
            face_cx = (left + right) / 2
            face_cy = (top + bottom) / 2
            img_cx  = w / 2
            img_cy  = h / 2
            offset_x = abs(face_cx - img_cx) / w
            offset_y = abs(face_cy - img_cy) / h
            if offset_x > 0.30 or offset_y > 0.30:
                issues.append("⚠  Face is off-center — center the person in frame")
                score -= 15

        score = max(0, score)
        passed = score >= 60 and not any("✕" in i for i in issues)
        return passed, issues, score

    def _quality_score_color(self, score):
        if score >= 80:
            return SUCCESS
        elif score >= 60:
            return WARNING
        else:
            return DANGER

    # ── Page: Register New Patient ────────────────────────────────────────────
    def _build_register_page(self):
        page = tk.Frame(self.content, bg=BG_DARK)
        page.pack(fill="both", expand=True, padx=30, pady=25)

        tk.Label(page, text="Register New Patient", font=FONT_HEADING,
                 fg=TEXT_PRIMARY, bg=BG_DARK).pack(anchor="w")
        tk.Label(page, text="Add a new patient to the recognition system",
                 font=FONT_LABEL, fg=TEXT_MUTED, bg=BG_DARK).pack(anchor="w", pady=(4, 20))

        # Scrollable form container
        canvas_wrapper = tk.Frame(page, bg=BG_DARK)
        canvas_wrapper.pack(fill="both", expand=True)

        form_canvas = tk.Canvas(canvas_wrapper, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_wrapper, orient="vertical",
                                   command=form_canvas.yview)
        form_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        form_canvas.pack(side="left", fill="both", expand=True)

        form_frame = tk.Frame(form_canvas, bg=BG_DARK)
        form_canvas.create_window((0, 0), window=form_frame, anchor="nw")
        form_frame.bind("<Configure>",
                         lambda e: form_canvas.configure(
                             scrollregion=form_canvas.bbox("all")))

        # Two-column layout
        left_col = tk.Frame(form_frame, bg=BG_DARK)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 12))
        right_col = tk.Frame(form_frame, bg=BG_DARK)
        right_col.pack(side="right", fill="both", expand=True, padx=(12, 0))

        entries = {}

        def section_card(parent, title):
            card = tk.Frame(parent, bg=BG_CARD)
            card.pack(fill="x", pady=(0, 16))
            tk.Frame(card, bg=ACCENT_TEAL, height=2).pack(fill="x")
            tk.Label(card, text=title, font=FONT_CARD_TTL,
                     fg=TEXT_PRIMARY, bg=BG_CARD,
                     padx=16, pady=10).pack(anchor="w")
            return card

        def labeled_entry(parent, label, var_key, required=False, placeholder=""):
            f = tk.Frame(parent, bg=BG_CARD)
            f.pack(fill="x", padx=16, pady=(0, 12))
            lbl_text = label + (" *" if required else "")
            tk.Label(f, text=lbl_text, font=FONT_SMALL,
                     fg=ACCENT_TEAL if required else TEXT_MUTED,
                     bg=BG_CARD, anchor="w").pack(anchor="w", pady=(0, 3))
            var = tk.StringVar()
            entry = tk.Entry(f, textvariable=var, font=FONT_LABEL,
                              bg="#1C2128", fg=TEXT_PRIMARY,
                              insertbackground=ACCENT_TEAL,
                              relief="flat", bd=0,
                              highlightthickness=1,
                              highlightcolor=ACCENT_TEAL,
                              highlightbackground=BORDER)
            entry.pack(fill="x", ipady=7)
            if placeholder:
                entry.insert(0, placeholder)
                entry.config(fg=TEXT_DIM)
                def on_focus_in(e, en=entry, ph=placeholder):
                    if en.get() == ph:
                        en.delete(0, "end")
                        en.config(fg=TEXT_PRIMARY)
                def on_focus_out(e, en=entry, ph=placeholder):
                    if not en.get():
                        en.insert(0, ph)
                        en.config(fg=TEXT_DIM)
                entry.bind("<FocusIn>", on_focus_in)
                entry.bind("<FocusOut>", on_focus_out)
            entries[var_key] = var
            return var

        # Personal info card
        personal_card = section_card(left_col, "Personal Information")
        labeled_entry(personal_card, "First Name", "first_name", required=True)
        labeled_entry(personal_card, "Middle Name", "middle_name", placeholder="Optional")
        labeled_entry(personal_card, "Last Name", "last_name", required=True)
        labeled_entry(personal_card, "Age", "age", required=True)

        # Sex selection
        sex_frame = tk.Frame(personal_card, bg=BG_CARD)
        sex_frame.pack(fill="x", padx=16, pady=(0, 12))
        tk.Label(sex_frame, text="Sex *", font=FONT_SMALL, fg=ACCENT_TEAL,
                 bg=BG_CARD).pack(anchor="w", pady=(0, 4))

        sex_var = tk.StringVar(value="M")
        entries["sex"] = sex_var
        sex_other_var = tk.StringVar()
        entries["sex_other"] = sex_other_var

        sex_btn_frame = tk.Frame(sex_frame, bg=BG_CARD)
        sex_btn_frame.pack(anchor="w")

        sex_other_entry = None

        def update_sex_other_visibility(*args):
            if sex_var.get() == "Other" and sex_other_entry:
                sex_other_frame.pack(fill="x", padx=16, pady=(0, 12))
            elif sex_other_entry:
                sex_other_frame.pack_forget()

        for val, lbl in [("M", "Male"), ("F", "Female"), ("Other", "Other")]:
            rb = tk.Radiobutton(sex_btn_frame, text=lbl, variable=sex_var, value=val,
                                 bg=BG_CARD, fg=TEXT_PRIMARY, selectcolor=BG_DARK,
                                 activebackground=BG_CARD, font=FONT_SMALL,
                                 command=update_sex_other_visibility)
            rb.pack(side="left", padx=(0, 16))

        sex_other_frame = tk.Frame(personal_card, bg=BG_CARD)
        sex_other_entry_widget = tk.Entry(sex_other_frame, textvariable=sex_other_var,
                                           font=FONT_LABEL, bg="#1C2128", fg=TEXT_PRIMARY,
                                           insertbackground=ACCENT_TEAL, relief="flat",
                                           bd=0, highlightthickness=1,
                                           highlightcolor=ACCENT_TEAL,
                                           highlightbackground=BORDER)
        tk.Label(sex_other_frame, text="Specify:", font=FONT_SMALL,
                 fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")
        sex_other_entry_widget.pack(fill="x", ipady=7)
        sex_other_entry = sex_other_entry_widget

        tk.Frame(personal_card, bg=BG_CARD, height=8).pack()

        # Contact card
        contact_card = section_card(right_col, "Contact Information")
        labeled_entry(contact_card, "Phone Number", "phone", required=True,
                       placeholder="+1 (555) 000-0000")
        labeled_entry(contact_card, "Email Address", "email", placeholder="patient@email.com")

        # Face capture card
        face_card = section_card(right_col, "Face Capture  *")
        tk.Label(face_card,
                 text="A face photo is required for recognition.\nMake sure the face is clearly visible.",
                 font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_CARD,
                 wraplength=280, justify="left", padx=16).pack(anchor="w", pady=(0, 8))

        self.face_capture_path = tk.StringVar()

        # ── Preview + quality panel side by side ─────────────────────────────
        photo_row = tk.Frame(face_card, bg=BG_CARD)
        photo_row.pack(fill="x", padx=16, pady=(0, 8))

        # Left: preview box
        preview_frame = tk.Frame(photo_row, bg="#0D1117", width=110, height=110)
        preview_frame.pack(side="left")
        preview_frame.pack_propagate(False)
        self.face_preview_lbl = tk.Label(preview_frame, bg="#0D1117",
                                          text="No photo\ncaptured yet",
                                          font=FONT_SMALL, fg=TEXT_DIM,
                                          justify="center")
        self.face_preview_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Right: quality panel
        quality_panel = tk.Frame(photo_row, bg=BG_CARD)
        quality_panel.pack(side="left", fill="both", expand=True, padx=(12, 0))

        tk.Label(quality_panel, text="Photo Quality", font=FONT_SMALL,
                 fg=TEXT_MUTED, bg=BG_CARD, anchor="w").pack(anchor="w")

        # Score bar background
        bar_bg = tk.Frame(quality_panel, bg=BORDER, height=8)
        bar_bg.pack(fill="x", pady=(4, 2))
        bar_bg.pack_propagate(False)
        self.quality_bar = tk.Frame(bar_bg, bg=TEXT_DIM, height=8, width=0)
        self.quality_bar.place(x=0, y=0, relheight=1.0)

        self.quality_score_lbl = tk.Label(quality_panel, text="—",
                                           font=("Helvetica Neue", 9, "bold"),
                                           fg=TEXT_DIM, bg=BG_CARD, anchor="w")
        self.quality_score_lbl.pack(anchor="w")

        # Issues list — shows per-check results
        self.quality_issues_frame = tk.Frame(quality_panel, bg=BG_CARD)
        self.quality_issues_frame.pack(fill="x", pady=(4, 0))

        # Status label
        self.face_status_lbl = tk.Label(face_card, text="⚠  No photo selected",
                                         font=FONT_SMALL, fg=WARNING, bg=BG_CARD,
                                         padx=16, anchor="w")
        self.face_status_lbl.pack(fill="x", pady=(0, 8))

        face_btn_row = tk.Frame(face_card, bg=BG_CARD)
        face_btn_row.pack(fill="x", padx=16, pady=(0, 16))

        self._styled_button(face_btn_row, "📷  Camera Capture",
                             self._capture_registration_face,
                             bg=ACCENT_TEAL, fg=BG_DARK).pack(side="left", padx=(0, 8))
        self._styled_button(face_btn_row, "📂  Upload Photo",
                             self._upload_registration_face,
                             bg=BG_DARK, fg=TEXT_MUTED, outline=True).pack(side="left")
        self._styled_button(face_btn_row, "🔄  Retake",
                             self._capture_registration_face,
                             bg=BG_DARK, fg=TEXT_MUTED, outline=True).pack(side="left", padx=(8, 0))

        # Submit button
        submit_frame = tk.Frame(page, bg=BG_DARK)
        submit_frame.pack(fill="x", pady=(16, 0))

        def submit():
            first = entries["first_name"].get().strip()
            last = entries["last_name"].get().strip()
            age_str = entries["age"].get().strip()
            phone = entries["phone"].get().strip()
            sex = entries["sex"].get()

            if not first or not last or not age_str:
                messagebox.showerror("Validation", "First Name, Last Name, and Age are required.")
                return
            if not age_str.isdigit():
                messagebox.showerror("Validation", "Age must be a number.")
                return

            face_path = self.face_capture_path.get().strip()

            # ── Require a face photo ──────────────────────────────────────
            if not face_path:
                messagebox.showerror("Face Required",
                                     "Please capture or upload a face photo before registering.")
                return
            if not os.path.exists(face_path):
                messagebox.showerror("File Not Found",
                                     f"Photo file not found:\n{face_path}\n\nPlease capture again.")
                return

            # ── Validate face is detectable in the photo ─────────────────
            if CV2_AVAILABLE:
                passed, issues, score = self._check_photo_quality(face_path)
                if not passed:
                    issue_text = "\n".join(issues)
                    override = messagebox.askyesno(
                        "Poor Photo Quality",
                        f"This photo scored {score}/100 and has the following issues:\n\n"
                        f"{issue_text}\n\n"
                        f"Poor quality photos cause unreliable recognition.\n\n"
                        f"Retake photo?  (No = register anyway)"
                    )
                    if override:  # Yes = go back and retake
                        return

            middle = entries["middle_name"].get().strip() or None
            sex_other = entries["sex_other"].get().strip() or None
            email = entries["email"].get().strip() or None

            try:
                personal_id = insert_patients(
                    first_name=first, middle_name=middle, last_name=last,
                    age=int(age_str), sex=sex, sex_other=sex_other,
                    last_login=datetime.datetime.now()
                )
                if personal_id and phone:
                    insert_contact(personal_id=personal_id,
                                   phone_number=phone, email=email)

                # ── Save face to known_faces/ using absolute path ─────────
                dest = os.path.join(KNOWN_FACES_DIR, f"{first} {last}.jpg")
                import shutil
                shutil.copy(face_path, dest)
                print(f"[Register] Face photo saved to: {dest}")
                print(f"[Register] File exists after save: {os.path.exists(dest)}")

                # ── Load encoding into memory so camera works immediately ─
                if CV2_AVAILABLE:
                    img = face_recognition.load_image_file(dest)
                    encs = face_recognition.face_encodings(img)
                    if encs:
                        self.known_face_encodings.append(encs[0])
                        self.known_faces_names.append(f"{first} {last}")
                        print(f"[Register] Face encoding loaded for: {first} {last}")
                    else:
                        print(f"[Register] Warning: could not encode face from saved image.")

                messagebox.showinfo("Success",
                                    f"✓ Patient registered!\n\n"
                                    f"Name: {first} {last}\n"
                                    f"ID: {personal_id}\n"
                                    f"Photo saved to:\n{dest}")
                for var in entries.values():
                    var.set("")
                self.face_capture_path.set("")
                self.face_preview_lbl.config(image="", text="No photo\ncaptured yet", fg=TEXT_DIM)
                self.face_status_lbl.config(text="⚠  No photo selected", fg=WARNING)

            except Exception as e:
                print(f"[Register] Error: {e}")
                messagebox.showerror("Database Error", str(e))

        self._styled_button(submit_frame, "✓  Register Patient", submit,
                             bg=SUCCESS, fg=TEXT_PRIMARY).pack(side="left")
        self._styled_button(submit_frame, "✕  Cancel",
                             lambda: self.show_page("home"),
                             bg=BG_DARK, fg=TEXT_MUTED, outline=True).pack(side="left", padx=12)

    def _apply_quality_result(self, image_path):
        """Run quality check and update the quality panel UI."""
        # Update preview
        if PIL_AVAILABLE and os.path.exists(image_path):
            img   = Image.open(image_path).resize((110, 110), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.face_preview_lbl.config(image=photo, text="")
            self.face_preview_lbl._photo = photo

        # Run checks in background so UI doesn't freeze
        def run_check():
            passed, issues, score = self._check_photo_quality(image_path)
            self.after(0, lambda: self._update_quality_ui(passed, issues, score, image_path))

        threading.Thread(target=run_check, daemon=True).start()

        # Show "Checking..." immediately
        self.face_status_lbl.config(text="🔍  Checking photo quality…", fg=TEXT_MUTED)
        self.quality_score_lbl.config(text="Checking…", fg=TEXT_MUTED)

    def _update_quality_ui(self, passed, issues, score, image_path):
        """Called on UI thread after quality check completes."""
        color = self._quality_score_color(score)

        # Update score label
        grade = "Excellent" if score >= 85 else "Good" if score >= 70 else "Fair" if score >= 55 else "Poor"
        self.quality_score_lbl.config(
            text=f"{score}/100 — {grade}", fg=color)

        # Animate quality bar width
        try:
            bar_width = int(self.quality_bar.master.winfo_width() * score / 100)
            self.quality_bar.config(bg=color, width=max(bar_width, 2))
        except Exception:
            pass

        # Clear and rebuild issues list
        for w in self.quality_issues_frame.winfo_children():
            w.destroy()

        if issues:
            for issue in issues:
                issue_color = DANGER if "✕" in issue else WARNING
                tk.Label(self.quality_issues_frame, text=issue,
                         font=FONT_SMALL, fg=issue_color, bg=BG_CARD,
                         anchor="w", wraplength=200,
                         justify="left").pack(anchor="w", pady=1)
        else:
            tk.Label(self.quality_issues_frame,
                     text="✓  All checks passed",
                     font=FONT_SMALL, fg=SUCCESS, bg=BG_CARD,
                     anchor="w").pack(anchor="w")

        # Update main status label
        if passed:
            self.face_status_lbl.config(
                text=f"✓  Photo ready — {os.path.basename(image_path)}",
                fg=SUCCESS)
        else:
            self.face_status_lbl.config(
                text="✕  Photo has issues — please retake",
                fg=DANGER)
            # Don't block — let staff override if they choose,
            # but the submit will still warn them

    def _capture_registration_face(self):
        save_path = os.path.join(BASE_DIR, "temp_registration_face.jpg")
        print(f"[Capture] Saving temp photo to: {save_path}")
        success = capture_face_from_camera(save_path)
        if success and os.path.exists(save_path):
            self.face_capture_path.set(save_path)
            print(f"[Capture] Temp photo saved: {save_path}")
            self._apply_quality_result(save_path)
        else:
            print("[Capture] Camera capture failed or cancelled.")
            self.face_status_lbl.config(text="✕  Capture failed — try again", fg=DANGER)

    def _upload_registration_face(self):
        path = filedialog.askopenfilename(
            title="Select Patient Photo",
            filetypes=[("Images", "*.jpg *.jpeg *.png")]
        )
        if path:
            self.face_capture_path.set(path)
            print(f"[Upload] Photo selected: {path}")
            self._apply_quality_result(path)

    # ── Page: Patient Info ────────────────────────────────────────────────────
    def _build_patient_page(self):
        page = tk.Frame(self.content, bg=BG_DARK)
        page.pack(fill="both", expand=True, padx=30, pady=25)

        # Header with search
        hdr = tk.Frame(page, bg=BG_DARK)
        hdr.pack(fill="x", pady=(0, 20))
        tk.Label(hdr, text="Patient Information", font=FONT_HEADING,
                 fg=TEXT_PRIMARY, bg=BG_DARK).pack(side="left")

        search_frame = tk.Frame(hdr, bg=BG_CARD)
        search_frame.pack(side="right")
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var,
                                 font=FONT_LABEL, bg="#1C2128", fg=TEXT_DIM,
                                 insertbackground=ACCENT_TEAL,
                                 relief="flat", bd=0,
                                 highlightthickness=1,
                                 highlightcolor=ACCENT_TEAL,
                                 highlightbackground=BORDER,
                                 width=22)
        search_entry.pack(side="left", padx=12, ipady=7, pady=6)

        PLACEHOLDER = "Search by ID or name..."
        search_entry.insert(0, PLACEHOLDER)

        def on_focus_in(e):
            if search_var.get() == PLACEHOLDER:
                search_entry.delete(0, "end")
                search_entry.config(fg=TEXT_PRIMARY)

        def on_focus_out(e):
            if not search_var.get().strip():
                search_entry.insert(0, PLACEHOLDER)
                search_entry.config(fg=TEXT_DIM)

        search_entry.bind("<FocusIn>",  on_focus_in)
        search_entry.bind("<FocusOut>", on_focus_out)
        search_entry.bind("<Return>",   lambda e: do_search())

        def do_search():
            q = search_var.get().strip()
            if not q or q == PLACEHOLDER:
                return
            try:
                if q.isdigit():
                    patient = get_patient_by_id(int(q))
                    if patient:
                        self._display_patient_info(info_area, patient)
                    else:
                        messagebox.showinfo("Not Found", "No patient with that ID.")
                else:
                    from db_connection import get_patient_by_name
                    results = get_patient_by_name(q)
                    if results:
                        self._display_patient_info(info_area, results[0])
                    else:
                        messagebox.showinfo("Not Found", "No matching patients.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        self._styled_button(search_frame, "Search", do_search,
                             bg=ACCENT_TEAL, fg=BG_DARK).pack(side="left", padx=(0, 8), pady=6)

        # Main area
        info_area = tk.Frame(page, bg=BG_DARK)
        info_area.pack(fill="both", expand=True)

        if self.current_patient:
            self._display_patient_info(info_area, self.current_patient)
        else:
            tk.Label(info_area, text="Search for a patient above, or recognize one via camera.",
                     font=FONT_LABEL, fg=TEXT_MUTED, bg=BG_DARK).pack(pady=60)

    def _display_patient_info(self, parent, patient):
        for w in parent.winfo_children():
            w.destroy()

        self.current_patient = patient

        body = tk.Frame(parent, bg=BG_DARK)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        # Profile card
        profile = tk.Frame(body, bg=BG_CARD)
        profile.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        tk.Frame(profile, bg=ACCENT_TEAL, height=3).pack(fill="x")

        name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
        initials = (patient.get("first_name", "?")[0] +
                    patient.get("last_name", "?")[0]).upper()

        # ── Photo or initials avatar ──────────────────────────────────────────
        av_frame = tk.Frame(profile, bg=BG_CARD)
        av_frame.pack(pady=(24, 8))
        photo_img = self._load_patient_photo(patient, size=(110, 110))
        if photo_img:
            lbl = tk.Label(av_frame, image=photo_img, bg=BG_CARD,
                           highlightthickness=2, highlightbackground=ACCENT_TEAL)
            lbl.pack()
            lbl._photo = photo_img
        else:
            avatar_label(av_frame, initials, size=110, bg=BG_CARD, fg=ACCENT_TEAL).pack()

        tk.Label(profile, text=name, font=("Georgia", 18, "bold"),
                 fg=TEXT_PRIMARY, bg=BG_CARD).pack()
        tk.Label(profile, text=f"Patient ID: {patient.get('personal_id', '—')}",
                 font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_CARD).pack(pady=(2, 16))

        # Fields
        fields = [
            ("First Name", patient.get("first_name", "—")),
            ("Middle Name", patient.get("middle_name") or "—"),
            ("Last Name", patient.get("last_name", "—")),
            ("Age", str(patient.get("age", "—"))),
            ("Sex", patient.get("sex", "—")),
            ("Last Login", str(patient.get("last_login", "—"))),
        ]
        for lbl, val in fields:
            row = tk.Frame(profile, bg=BG_CARD)
            row.pack(fill="x", padx=20, pady=3)
            tk.Label(row, text=lbl, font=FONT_SMALL, fg=TEXT_MUTED,
                     bg=BG_CARD, width=13, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=FONT_SMALL, fg=TEXT_PRIMARY,
                     bg=BG_CARD, anchor="w").pack(side="left")

        tk.Frame(profile, bg=BORDER, height=1).pack(fill="x", padx=20, pady=12)

        # Action buttons
        btn_area = tk.Frame(profile, bg=BG_CARD)
        btn_area.pack(padx=20, pady=(0, 20), fill="x")
        self._styled_button(btn_area, "◉  View Relatives",
                             lambda: self.show_page("relatives"),
                             bg=ACCENT_TEAL, fg=BG_DARK).pack(fill="x", pady=3)
        self._styled_button(btn_area, "▦  View Calendar",
                             lambda: self.show_page("calendar"),
                             bg=ACCENT_TEAL, fg=BG_DARK).pack(fill="x", pady=3)
        self._styled_button(btn_area, "✎  Edit Patient",
                             lambda p=patient: self._open_edit_patient_dialog(p),
                             bg=BG_DARK, fg=TEXT_MUTED, outline=True).pack(fill="x", pady=3)

        tk.Frame(btn_area, bg=BORDER, height=1).pack(fill="x", pady=8)

        # Delete button — red, separated from the others so it can't be
        # accidentally clicked alongside normal actions
        self._styled_button(btn_area, "🗑  Delete Patient",
                             lambda p=patient: self._confirm_delete_patient(p),
                             bg=DANGER, fg=TEXT_PRIMARY).pack(fill="x", pady=3)

        # Contact / detail card
        detail = tk.Frame(body, bg=BG_CARD)
        detail.grid(row=0, column=1, sticky="nsew")
        tk.Frame(detail, bg=ACCENT_WARM, height=3).pack(fill="x")

        tk.Label(detail, text="Contact & Details", font=FONT_CARD_TTL,
                 fg=TEXT_PRIMARY, bg=BG_CARD,
                 padx=20, pady=14).pack(anchor="w")

        contact_fields = [
            ("📞 Phone", patient.get("phone_number") or "—"),
            ("✉ Email", patient.get("email") or "—"),
        ]
        for lbl, val in contact_fields:
            row = tk.Frame(detail, bg="#1C2128")
            row.pack(fill="x", padx=20, pady=4)
            tk.Label(row, text=lbl, font=FONT_LABEL, fg=TEXT_MUTED,
                     bg="#1C2128", width=12, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=FONT_LABEL, fg=TEXT_PRIMARY,
                     bg="#1C2128", anchor="w").pack(side="left")

        if patient.get("sex_other"):
            row = tk.Frame(detail, bg="#1C2128")
            row.pack(fill="x", padx=20, pady=4)
            tk.Label(row, text="Gender ID", font=FONT_LABEL, fg=TEXT_MUTED,
                     bg="#1C2128", width=12, anchor="w").pack(side="left")
            tk.Label(row, text=patient["sex_other"], font=FONT_LABEL,
                     fg=TEXT_PRIMARY, bg="#1C2128").pack(side="left")

    def _confirm_delete_patient(self, patient):
        """Two-step confirmation dialog before deleting a patient."""
        name        = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
        personal_id = patient.get("personal_id")

        # ── Step 1: Initial confirm ───────────────────────────────────────────
        confirmed = messagebox.askyesno(
            "Delete Patient",
            f"Are you sure you want to delete:\n\n"
            f"  {name}  (ID: {personal_id})\n\n"
            f"This will permanently remove the patient,\n"
            f"all their contacts, and all relative records.\n\n"
            f"This cannot be undone.",
            icon="warning"
        )
        if not confirmed:
            return

        # ── Step 2: Type name to confirm (prevents accidental deletion) ───────
        dialog = tk.Toplevel(self)
        dialog.title("Confirm Deletion")
        dialog.geometry("420x260")
        dialog.configure(bg=BG_DARK)
        dialog.resizable(False, False)
        dialog.grab_set()

        tk.Frame(dialog, bg=DANGER, height=3).pack(fill="x")

        tk.Label(dialog, text="⚠  Final Confirmation",
                 font=("Georgia", 14, "bold"), fg=DANGER, bg=BG_DARK
                 ).pack(anchor="w", padx=24, pady=(16, 4))

        tk.Label(dialog,
                 text=f"Type the patient's full name to confirm deletion:\n\"{name}\"",
                 font=FONT_LABEL, fg=TEXT_MUTED, bg=BG_DARK,
                 wraplength=370, justify="left"
                 ).pack(anchor="w", padx=24, pady=(0, 12))

        confirm_var = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=confirm_var,
                         font=FONT_LABEL, bg="#1C2128", fg=TEXT_PRIMARY,
                         insertbackground=DANGER, relief="flat", bd=0,
                         highlightthickness=1,
                         highlightcolor=DANGER, highlightbackground=BORDER)
        entry.pack(fill="x", padx=24, ipady=8)
        entry.focus_set()

        match_lbl = tk.Label(dialog, text="", font=FONT_SMALL, bg=BG_DARK)
        match_lbl.pack(anchor="w", padx=24, pady=4)

        def on_type(*args):
            if confirm_var.get().strip().lower() == name.lower():
                match_lbl.config(text="✓  Name matches", fg=SUCCESS)
                delete_btn.config(bg=DANGER, state="normal")
            else:
                match_lbl.config(text="Name does not match yet…", fg=TEXT_DIM)
                delete_btn.config(bg=TEXT_DIM, state="disabled")

        confirm_var.trace_add("write", on_type)

        btn_row = tk.Frame(dialog, bg=BG_DARK)
        btn_row.pack(fill="x", padx=24, pady=(8, 20))

        def do_delete():
            dialog.destroy()
            try:
                success = delete_patient(personal_id)
                if success:
                    # Remove from known_faces folder and in-memory encodings
                    self._remove_patient_face_files(name)
                    # Clear cache and current patient
                    self._patient_cache.pop(name, None)
                    if self.current_patient and \
                       self.current_patient.get("personal_id") == personal_id:
                        self.current_patient = None
                    messagebox.showinfo("Deleted",
                                        f"{name} has been successfully removed from the system.")
                    self.show_page("patient")
                else:
                    messagebox.showerror("Error", "Could not delete patient. They may not exist in the database.")
            except Exception as e:
                messagebox.showerror("Database Error", str(e))

        delete_btn = tk.Button(btn_row, text="🗑  Permanently Delete",
                               font=("Helvetica Neue", 10, "bold"),
                               fg=TEXT_PRIMARY, bg=TEXT_DIM,
                               relief="flat", bd=0, padx=14, pady=6,
                               state="disabled", cursor="hand2",
                               command=do_delete)
        delete_btn.pack(side="left")

        self._styled_button(btn_row, "Cancel", dialog.destroy,
                             bg=BG_DARK, fg=TEXT_MUTED, outline=True
                             ).pack(side="left", padx=12)

    def _remove_patient_face_files(self, name):
        """Remove the patient's photo from known_faces/ and their encoding from memory."""
        # Remove from known_faces folder
        for ext in (".jpg", ".jpeg", ".png"):
            path = os.path.join(KNOWN_FACES_DIR, f"{name}{ext}")
            if os.path.exists(path):
                try:
                    os.remove(path)
                    print(f"[Delete] Removed face file: {path}")
                except Exception as e:
                    print(f"[Delete] Could not remove {path}: {e}")

        # Remove from in-memory encodings so camera stops recognising them
        if name in self.known_faces_names:
            idx = self.known_faces_names.index(name)
            self.known_faces_names.pop(idx)
            self.known_face_encodings.pop(idx)
            print(f"[Delete] Removed encoding for: {name}")

    def _open_edit_patient_dialog(self, patient):
        """Edit patient name, age, sex, and contact info."""
        dialog = tk.Toplevel(self)
        dialog.title("Edit Patient")
        dialog.geometry("460x520")
        dialog.configure(bg=BG_DARK)
        dialog.grab_set()

        tk.Frame(dialog, bg=ACCENT_TEAL, height=3).pack(fill="x")
        tk.Label(dialog, text="Edit Patient", font=("Georgia", 14, "bold"),
                 fg=TEXT_PRIMARY, bg=BG_DARK).pack(anchor="w", padx=24, pady=(16, 4))

        tk.Frame(dialog, bg=BORDER, height=1).pack(fill="x", padx=24, pady=8)

        form = tk.Frame(dialog, bg=BG_DARK)
        form.pack(fill="both", expand=True, padx=24)

        fields = {}

        def dialog_entry(label, key, default=""):
            f = tk.Frame(form, bg=BG_DARK)
            f.pack(fill="x", pady=5)
            tk.Label(f, text=label, font=FONT_SMALL,
                     fg=TEXT_MUTED, bg=BG_DARK, anchor="w").pack(anchor="w")
            var = tk.StringVar(value=default)
            tk.Entry(f, textvariable=var, font=FONT_LABEL,
                     bg="#1C2128", fg=TEXT_PRIMARY,
                     insertbackground=ACCENT_TEAL, relief="flat", bd=0,
                     highlightthickness=1, highlightcolor=ACCENT_TEAL,
                     highlightbackground=BORDER).pack(fill="x", ipady=7)
            fields[key] = var

        dialog_entry("First Name", "first_name",  patient.get("first_name", ""))
        dialog_entry("Middle Name", "middle_name", patient.get("middle_name") or "")
        dialog_entry("Last Name",  "last_name",   patient.get("last_name", ""))
        dialog_entry("Age",        "age",          str(patient.get("age", "")))
        dialog_entry("Phone",      "phone",        patient.get("phone_number") or "")
        dialog_entry("Email",      "email",        patient.get("email") or "")

        tk.Frame(dialog, bg=BORDER, height=1).pack(fill="x", padx=24, pady=8)

        btn_row = tk.Frame(dialog, bg=BG_DARK)
        btn_row.pack(fill="x", padx=24, pady=(0, 20))

        def save_edit():
            first   = fields["first_name"].get().strip()
            last    = fields["last_name"].get().strip()
            age_str = fields["age"].get().strip()

            if not first or not last or not age_str:
                messagebox.showerror("Validation", "First Name, Last Name, and Age are required.")
                return
            if not age_str.isdigit():
                messagebox.showerror("Validation", "Age must be a number.")
                return

            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                # Update patient record
                cursor.execute("""
                    UPDATE patients
                    SET first_name=%s, middle_name=%s, last_name=%s, age=%s
                    WHERE personal_id=%s
                """, (first,
                      fields["middle_name"].get().strip() or None,
                      last,
                      int(age_str),
                      patient["personal_id"]))

                # Update or insert contact
                phone = fields["phone"].get().strip() or None
                email = fields["email"].get().strip() or None
                cursor.execute("""
                    INSERT INTO contacts (personal_id, phone_number, email)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE phone_number=%s, email=%s
                """, (patient["personal_id"], phone, email, phone, email))

                conn.commit()
                cursor.close()
                conn.close()

                # Rename known_faces file if name changed
                old_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
                new_name = f"{first} {last}".strip()
                if old_name != new_name:
                    self._rename_patient_face_file(old_name, new_name)

                # Update patient cache
                self._patient_cache.pop(old_name, None)
                self.current_patient = None

                dialog.destroy()
                messagebox.showinfo("Saved", f"Patient record updated successfully.")
                self.show_page("patient")

            except Exception as e:
                messagebox.showerror("Database Error", str(e))

        self._styled_button(btn_row, "✓  Save Changes", save_edit,
                             bg=SUCCESS, fg=TEXT_PRIMARY).pack(side="left")
        self._styled_button(btn_row, "Cancel", dialog.destroy,
                             bg=BG_DARK, fg=TEXT_MUTED, outline=True).pack(side="left", padx=12)

    def _rename_patient_face_file(self, old_name, new_name):
        """Rename the known_faces file and update in-memory encodings list."""
        for ext in (".jpg", ".jpeg", ".png"):
            old_path = os.path.join(KNOWN_FACES_DIR, f"{old_name}{ext}")
            if os.path.exists(old_path):
                new_path = os.path.join(KNOWN_FACES_DIR, f"{new_name}{ext}")
                try:
                    os.rename(old_path, new_path)
                    print(f"[Edit] Renamed face file: {old_name} → {new_name}")
                except Exception as e:
                    print(f"[Edit] Could not rename face file: {e}")
        # Update in-memory name
        if old_name in self.known_faces_names:
            idx = self.known_faces_names.index(old_name)
            self.known_faces_names[idx] = new_name
            print(f"[Edit] Updated encoding name: {old_name} → {new_name}")

    # ── Page: Calendar ────────────────────────────────────────────────────────
    def _build_calendar_page(self):
        import calendar as cal_mod
        page = tk.Frame(self.content, bg=BG_DARK)
        page.pack(fill="both", expand=True, padx=30, pady=25)

        # ── State for this page ───────────────────────────────────────────────
        today        = datetime.date.today()
        self._cal_year   = tk.IntVar(value=today.year)
        self._cal_month  = tk.IntVar(value=today.month)
        self._cal_page   = page
        self._cal_mod    = cal_mod

        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(page, bg=BG_DARK)
        hdr.pack(fill="x", pady=(0, 16))

        tk.Label(hdr, text="Calendar", font=FONT_HEADING,
                 fg=TEXT_PRIMARY, bg=BG_DARK).pack(side="left")

        # Patient selector on the right
        patient_frame = tk.Frame(hdr, bg=BG_DARK)
        patient_frame.pack(side="right")

        tk.Label(patient_frame, text="Patient:", font=FONT_LABEL,
                 fg=TEXT_MUTED, bg=BG_DARK).pack(side="left", padx=(0, 8))

        patient_name = "None selected"
        if self.current_patient:
            patient_name = (f"{self.current_patient.get('first_name','')} "
                           f"{self.current_patient.get('last_name','')}").strip()

        self._cal_patient_lbl = tk.Label(patient_frame, text=patient_name,
                                          font=("Helvetica Neue", 11, "bold"),
                                          fg=ACCENT_TEAL, bg=BG_DARK)
        self._cal_patient_lbl.pack(side="left", padx=(0, 16))

        self._styled_button(patient_frame, "＋ Add Event",
                             self._open_add_event_dialog,
                             bg=ACCENT_TEAL, fg=BG_DARK).pack(side="left")

        # ── Body: calendar grid + event list side by side ─────────────────────
        body = tk.Frame(page, bg=BG_DARK)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # Left: calendar grid
        self._cal_grid_frame = tk.Frame(body, bg=BG_CARD)
        self._cal_grid_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        # Right: event list
        self._cal_events_frame = tk.Frame(body, bg=BG_CARD)
        self._cal_events_frame.grid(row=0, column=1, sticky="nsew")

        self._render_calendar()

    def _render_calendar(self):
        """Draw the month grid and event list."""
        import calendar as cal_mod

        for w in self._cal_grid_frame.winfo_children():
            w.destroy()
        for w in self._cal_events_frame.winfo_children():
            w.destroy()

        year  = self._cal_year.get()
        month = self._cal_month.get()
        today = datetime.date.today()

        MONTH_NAMES = ["January","February","March","April","May","June",
                       "July","August","September","October","November","December"]
        DAY_NAMES   = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

        # Load events from DB
        events_by_day = {}
        if self.current_patient:
            try:
                events = get_events_for_month(
                    self.current_patient["personal_id"], year, month)
                for ev in events:
                    d = ev["event_date"]
                    day = d.day if hasattr(d, "day") else int(str(d)[8:10])
                    events_by_day.setdefault(day, []).append(ev)
            except Exception as e:
                print(f"[Calendar] Error loading events: {e}")

        # ── Month navigation bar ──────────────────────────────────────────────
        nav = tk.Frame(self._cal_grid_frame, bg=BG_CARD)
        nav.pack(fill="x", padx=16, pady=12)

        def prev_month():
            m, y = self._cal_month.get(), self._cal_year.get()
            if m == 1:
                self._cal_month.set(12); self._cal_year.set(y - 1)
            else:
                self._cal_month.set(m - 1)
            self._render_calendar()

        def next_month():
            m, y = self._cal_month.get(), self._cal_year.get()
            if m == 12:
                self._cal_month.set(1); self._cal_year.set(y + 1)
            else:
                self._cal_month.set(m + 1)
            self._render_calendar()

        def go_today():
            t = datetime.date.today()
            self._cal_year.set(t.year)
            self._cal_month.set(t.month)
            self._render_calendar()

        prev_btn = tk.Label(nav, text="‹", font=("Georgia", 20), fg=TEXT_PRIMARY,
                            bg=BG_CARD, cursor="hand2")
        prev_btn.pack(side="left")
        prev_btn.bind("<Button-1>", lambda e: prev_month())

        nav_lbl = tk.Label(nav, text=f"{MONTH_NAMES[month-1]}  {year}",
                           font=("Georgia", 16, "bold"),
                           fg=TEXT_PRIMARY, bg=BG_CARD)
        nav_lbl.pack(side="left", padx=16)

        next_btn = tk.Label(nav, text="›", font=("Georgia", 20), fg=TEXT_PRIMARY,
                            bg=BG_CARD, cursor="hand2")
        next_btn.pack(side="left")
        next_btn.bind("<Button-1>", lambda e: next_month())

        self._styled_button(nav, "Today", go_today,
                             bg=BG_DARK, fg=TEXT_MUTED, outline=True).pack(
            side="right")

        # ── Day-name header row ───────────────────────────────────────────────
        grid = tk.Frame(self._cal_grid_frame, bg=BG_CARD)
        grid.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        for c in range(7):
            grid.columnconfigure(c, weight=1)

        for c, day_name in enumerate(DAY_NAMES):
            color = DANGER if c >= 5 else TEXT_MUTED
            tk.Label(grid, text=day_name, font=("Helvetica Neue", 9, "bold"),
                     fg=color, bg=BG_CARD, anchor="center",
                     pady=6).grid(row=0, column=c, sticky="ew")

        # Separator
        tk.Frame(grid, bg=BORDER, height=1).grid(
            row=1, column=0, columnspan=7, sticky="ew", pady=(0, 4))

        # ── Calendar days ─────────────────────────────────────────────────────
        cal = cal_mod.monthcalendar(year, month)

        for r, week in enumerate(cal):
            grid.rowconfigure(r + 2, weight=1)
            for c, day in enumerate(week):
                cell = tk.Frame(grid, bg=BG_CARD, padx=2, pady=2)
                cell.grid(row=r + 2, column=c, sticky="nsew", padx=1, pady=1)

                if day == 0:
                    # Empty cell (padding days)
                    tk.Frame(cell, bg=BG_CARD, width=60, height=60).pack()
                    continue

                is_today    = (day == today.day and month == today.month
                               and year == today.year)
                has_events  = day in events_by_day
                is_weekend  = c >= 5

                # Cell background
                cell_bg = "#1a3344" if is_today else "#1C2128" if has_events else BG_CARD
                cell.config(bg=cell_bg, cursor="hand2",
                            highlightthickness=1,
                            highlightbackground=ACCENT_TEAL if is_today else BORDER)

                # Day number
                num_color = (ACCENT_TEAL if is_today
                             else DANGER if is_weekend
                             else TEXT_PRIMARY)
                num_font  = ("Helvetica Neue", 10, "bold") if is_today else FONT_SMALL

                num_lbl = tk.Label(cell, text=str(day), font=num_font,
                                   fg=num_color, bg=cell_bg,
                                   anchor="nw", padx=4, pady=2)
                num_lbl.pack(anchor="nw")

                # Event dots (up to 3)
                if has_events:
                    dot_row = tk.Frame(cell, bg=cell_bg)
                    dot_row.pack(anchor="w", padx=4)
                    shown = events_by_day[day][:3]
                    for ev in shown:
                        dot = tk.Frame(dot_row, bg=ev.get("color", ACCENT_TEAL),
                                       width=8, height=8)
                        dot.pack(side="left", padx=1)
                        dot.pack_propagate(False)

                    # Show first event title truncated
                    first_title = events_by_day[day][0]["title"]
                    if len(first_title) > 10:
                        first_title = first_title[:9] + "…"
                    tk.Label(cell, text=first_title, font=("Helvetica Neue", 7),
                             fg=TEXT_MUTED, bg=cell_bg, anchor="w",
                             padx=4).pack(anchor="w")

                # Click cell to show that day's events
                def on_day_click(d=day, e_list=events_by_day.get(day, [])):
                    self._show_day_events(d, month, year, e_list)

                for widget in [cell, num_lbl]:
                    widget.bind("<Button-1>", lambda e, fn=on_day_click: fn())
                    widget.bind("<Enter>", lambda e, fr=cell, bg=cell_bg:
                                fr.config(bg="#253040" if bg == BG_CARD else bg))
                    widget.bind("<Leave>", lambda e, fr=cell, bg=cell_bg:
                                fr.config(bg=bg))

        # ── Right panel: event list ───────────────────────────────────────────
        tk.Frame(self._cal_events_frame, bg=ACCENT_TEAL, height=3).pack(fill="x")
        tk.Label(self._cal_events_frame,
                 text=f"Events — {MONTH_NAMES[month-1]} {year}",
                 font=FONT_CARD_TTL, fg=TEXT_PRIMARY,
                 bg=BG_CARD, padx=16, pady=12).pack(anchor="w")

        if not self.current_patient:
            tk.Label(self._cal_events_frame,
                     text="Select a patient first\nto view their events.",
                     font=FONT_LABEL, fg=TEXT_DIM,
                     bg=BG_CARD, justify="center").pack(pady=40)
            return

        # Scrollable event list
        ev_canvas = tk.Canvas(self._cal_events_frame, bg=BG_CARD,
                              highlightthickness=0)
        ev_scroll = ttk.Scrollbar(self._cal_events_frame, orient="vertical",
                                   command=ev_canvas.yview)
        ev_canvas.configure(yscrollcommand=ev_scroll.set)
        ev_scroll.pack(side="right", fill="y")
        ev_canvas.pack(side="left", fill="both", expand=True)

        ev_inner = tk.Frame(ev_canvas, bg=BG_CARD)
        ev_canvas.create_window((0, 0), window=ev_inner, anchor="nw")
        ev_inner.bind("<Configure>",
                      lambda e: ev_canvas.configure(
                          scrollregion=ev_canvas.bbox("all")))

        all_events = []
        for day_evs in events_by_day.values():
            all_events.extend(day_evs)
        all_events.sort(key=lambda e: (e["event_date"], e.get("start_time") or ""))

        if not all_events:
            tk.Label(ev_inner, text="No events this month.",
                     font=FONT_LABEL, fg=TEXT_DIM,
                     bg=BG_CARD, padx=16).pack(pady=30)
        else:
            for ev in all_events:
                self._event_row(ev_inner, ev)

    def _event_row(self, parent, ev):
        """A single event row in the event list."""
        color = ev.get("color", ACCENT_TEAL)
        d     = ev["event_date"]
        date_str = d.strftime("%a, %b %d") if hasattr(d, "strftime") else str(d)

        if ev.get("all_day"):
            time_str = "All day"
        else:
            st = str(ev.get("start_time") or "")[:5]
            et = str(ev.get("end_time")   or "")[:5]
            time_str = f"{st} – {et}" if st and et else st or "—"

        row = tk.Frame(parent, bg=BG_CARD, cursor="hand2")
        row.pack(fill="x", padx=12, pady=4)

        # Color stripe
        tk.Frame(row, bg=color, width=4).pack(side="left", fill="y")

        content = tk.Frame(row, bg="#1C2128")
        content.pack(side="left", fill="both", expand=True, padx=(0, 0))

        top_row = tk.Frame(content, bg="#1C2128")
        top_row.pack(fill="x", padx=10, pady=(6, 2))

        tk.Label(top_row, text=ev["title"],
                 font=("Helvetica Neue", 10, "bold"),
                 fg=TEXT_PRIMARY, bg="#1C2128",
                 anchor="w").pack(side="left")

        tk.Label(top_row, text=date_str,
                 font=FONT_SMALL, fg=TEXT_MUTED,
                 bg="#1C2128").pack(side="right")

        bot_row = tk.Frame(content, bg="#1C2128")
        bot_row.pack(fill="x", padx=10, pady=(0, 6))

        tk.Label(bot_row, text=f"🕐 {time_str}",
                 font=FONT_SMALL, fg=TEXT_MUTED,
                 bg="#1C2128", anchor="w").pack(side="left")

        if ev.get("description"):
            desc = ev["description"]
            if len(desc) > 40:
                desc = desc[:39] + "…"
            tk.Label(bot_row, text=desc, font=FONT_SMALL,
                     fg=TEXT_DIM, bg="#1C2128").pack(side="left", padx=(8, 0))

        # Edit / delete on hover
        action_row = tk.Frame(content, bg="#1C2128")

        def on_enter(e, ar=action_row):
            ar.pack(fill="x", padx=10, pady=(0, 4))

        def on_leave(e, ar=action_row):
            ar.pack_forget()

        def edit_ev(event=ev):
            self._open_edit_event_dialog(event)

        def del_ev(event=ev):
            self._confirm_delete_event(event)

        self._styled_button(action_row, "✎ Edit", edit_ev,
                             bg=BG_DARK, fg=TEXT_MUTED,
                             outline=True).pack(side="left", padx=(0, 6))
        self._styled_button(action_row, "🗑 Delete", del_ev,
                             bg=DANGER, fg=TEXT_PRIMARY).pack(side="left")

        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)
        content.bind("<Enter>", on_enter)
        content.bind("<Leave>", on_leave)

    def _show_day_events(self, day, month, year, events):
        """Popup showing all events for a clicked day."""
        import calendar as cal_mod
        MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun",
                       "Jul","Aug","Sep","Oct","Nov","Dec"]
        dialog = tk.Toplevel(self)
        dialog.title(f"Events — {MONTH_NAMES[month-1]} {day}, {year}")
        dialog.geometry("400x380")
        dialog.configure(bg=BG_DARK)
        dialog.grab_set()

        tk.Frame(dialog, bg=ACCENT_TEAL, height=3).pack(fill="x")
        tk.Label(dialog,
                 text=f"{MONTH_NAMES[month-1]} {day}, {year}",
                 font=("Georgia", 14, "bold"),
                 fg=TEXT_PRIMARY, bg=BG_DARK).pack(anchor="w", padx=20, pady=(14, 4))

        tk.Frame(dialog, bg=BORDER, height=1).pack(fill="x", padx=20, pady=8)

        if not events:
            tk.Label(dialog, text="No events on this day.",
                     font=FONT_LABEL, fg=TEXT_DIM,
                     bg=BG_DARK).pack(pady=30)
        else:
            for ev in events:
                color = ev.get("color", ACCENT_TEAL)
                st    = str(ev.get("start_time") or "")[:5]
                et    = str(ev.get("end_time")   or "")[:5]
                time_str = "All day" if ev.get("all_day") else (
                    f"{st} – {et}" if st and et else st or "—")

                row = tk.Frame(dialog, bg="#1C2128")
                row.pack(fill="x", padx=20, pady=4)
                tk.Frame(row, bg=color, width=4).pack(side="left", fill="y")
                inner = tk.Frame(row, bg="#1C2128")
                inner.pack(side="left", fill="x", expand=True, padx=10, pady=8)
                tk.Label(inner, text=ev["title"],
                         font=("Helvetica Neue", 11, "bold"),
                         fg=TEXT_PRIMARY, bg="#1C2128").pack(anchor="w")
                tk.Label(inner, text=f"🕐 {time_str}",
                         font=FONT_SMALL, fg=TEXT_MUTED,
                         bg="#1C2128").pack(anchor="w")
                if ev.get("description"):
                    tk.Label(inner, text=ev["description"],
                             font=FONT_SMALL, fg=TEXT_DIM,
                             bg="#1C2128", wraplength=300,
                             justify="left").pack(anchor="w", pady=(2, 0))

        btn_row = tk.Frame(dialog, bg=BG_DARK)
        btn_row.pack(fill="x", padx=20, pady=(12, 16))
        self._styled_button(btn_row, "＋ Add Event for this Day",
                             lambda: (dialog.destroy(),
                                      self._open_add_event_dialog(
                                          preset_date=datetime.date(year, month, day))),
                             bg=ACCENT_TEAL, fg=BG_DARK).pack(side="left")
        self._styled_button(btn_row, "Close", dialog.destroy,
                             bg=BG_DARK, fg=TEXT_MUTED, outline=True).pack(side="left", padx=10)

    def _open_add_event_dialog(self, preset_date=None):
        """Dialog to create a new calendar event."""
        if not self.current_patient:
            messagebox.showwarning("No Patient",
                                   "Please select a patient first.")
            return
        self._event_dialog(mode="add", event=None, preset_date=preset_date)

    def _open_edit_event_dialog(self, event):
        """Dialog to edit an existing event."""
        self._event_dialog(mode="edit", event=event)

    def _event_dialog(self, mode="add", event=None, preset_date=None):
        """Shared add/edit dialog for calendar events."""
        today = datetime.date.today()
        dialog = tk.Toplevel(self)
        dialog.title("Add Event" if mode == "add" else "Edit Event")
        dialog.geometry("460x540")
        dialog.configure(bg=BG_DARK)
        dialog.grab_set()

        accent = ACCENT_TEAL if mode == "add" else ACCENT_WARM
        tk.Frame(dialog, bg=accent, height=3).pack(fill="x")
        tk.Label(dialog,
                 text="New Event" if mode == "add" else "Edit Event",
                 font=("Georgia", 14, "bold"),
                 fg=TEXT_PRIMARY, bg=BG_DARK).pack(anchor="w", padx=24, pady=(14, 4))
        tk.Frame(dialog, bg=BORDER, height=1).pack(fill="x", padx=24, pady=8)

        form = tk.Frame(dialog, bg=BG_DARK)
        form.pack(fill="both", expand=True, padx=24)

        def field(label, default=""):
            f = tk.Frame(form, bg=BG_DARK)
            f.pack(fill="x", pady=5)
            tk.Label(f, text=label, font=FONT_SMALL,
                     fg=TEXT_MUTED, bg=BG_DARK, anchor="w").pack(anchor="w")
            var = tk.StringVar(value=default)
            tk.Entry(f, textvariable=var, font=FONT_LABEL,
                     bg="#1C2128", fg=TEXT_PRIMARY,
                     insertbackground=accent, relief="flat", bd=0,
                     highlightthickness=1, highlightcolor=accent,
                     highlightbackground=BORDER).pack(fill="x", ipady=7)
            return var

        # Pre-fill if editing
        default_date  = (event["event_date"].strftime("%Y-%m-%d")
                         if event and hasattr(event["event_date"], "strftime")
                         else str(event["event_date"]) if event
                         else preset_date.strftime("%Y-%m-%d") if preset_date
                         else today.strftime("%Y-%m-%d"))
        default_start = str(event.get("start_time") or "")[:5] if event else ""
        default_end   = str(event.get("end_time")   or "")[:5] if event else ""

        v_title = field("Event Title *", event["title"] if event else "")
        v_date  = field("Date (YYYY-MM-DD) *", default_date)
        v_start = field("Start Time (HH:MM)", default_start)
        v_end   = field("End Time   (HH:MM)", default_end)

        # Description
        f_desc = tk.Frame(form, bg=BG_DARK)
        f_desc.pack(fill="x", pady=5)
        tk.Label(f_desc, text="Description", font=FONT_SMALL,
                 fg=TEXT_MUTED, bg=BG_DARK).pack(anchor="w")
        v_desc = tk.Text(f_desc, font=FONT_LABEL,
                         bg="#1C2128", fg=TEXT_PRIMARY,
                         insertbackground=accent,
                         relief="flat", bd=0, height=3,
                         highlightthickness=1, highlightcolor=accent,
                         highlightbackground=BORDER)
        v_desc.pack(fill="x")
        if event and event.get("description"):
            v_desc.insert("1.0", event["description"])

        # All day toggle + color picker
        options_row = tk.Frame(form, bg=BG_DARK)
        options_row.pack(fill="x", pady=8)

        all_day_var = tk.BooleanVar(value=bool(event.get("all_day")) if event else False)
        tk.Checkbutton(options_row, text="All day event",
                       variable=all_day_var,
                       fg=TEXT_MUTED, bg=BG_DARK,
                       selectcolor=BG_DARK,
                       activebackground=BG_DARK,
                       font=FONT_SMALL).pack(side="left")

        # Color swatches
        tk.Label(options_row, text="Color:", font=FONT_SMALL,
                 fg=TEXT_MUTED, bg=BG_DARK).pack(side="left", padx=(20, 6))

        COLORS = [
            ("#2DD4BF", "Teal"),
            ("#FB923C", "Orange"),
            ("#3FB950", "Green"),
            ("#F85149", "Red"),
            ("#A371F7", "Purple"),
            ("#58A6FF", "Blue"),
        ]
        color_var = tk.StringVar(
            value=event.get("color", "#2DD4BF") if event else "#2DD4BF")

        swatch_frames = {}
        for hex_color, name in COLORS:
            sw = tk.Frame(options_row, bg=hex_color, width=20, height=20,
                          cursor="hand2",
                          highlightthickness=2,
                          highlightbackground=(
                              TEXT_PRIMARY if hex_color == color_var.get() else hex_color))
            sw.pack(side="left", padx=2)
            sw.pack_propagate(False)
            swatch_frames[hex_color] = sw

            def pick(c=hex_color):
                color_var.set(c)
                for hc, sf in swatch_frames.items():
                    sf.config(highlightbackground=(
                        TEXT_PRIMARY if hc == c else hc))

            sw.bind("<Button-1>", lambda e, fn=pick: fn())

        # ── Save ──────────────────────────────────────────────────────────────
        tk.Frame(dialog, bg=BORDER, height=1).pack(fill="x", padx=24, pady=8)
        btn_row = tk.Frame(dialog, bg=BG_DARK)
        btn_row.pack(fill="x", padx=24, pady=(0, 16))

        def save():
            title = v_title.get().strip()
            date_s = v_date.get().strip()
            if not title:
                messagebox.showerror("Validation", "Event title is required.")
                return
            try:
                ev_date = datetime.datetime.strptime(date_s, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showerror("Validation",
                                     "Date must be in YYYY-MM-DD format.\nExample: 2026-03-15")
                return

            def parse_time(t_str):
                t_str = t_str.strip()
                if not t_str:
                    return None
                try:
                    return datetime.datetime.strptime(t_str, "%H:%M").time()
                except ValueError:
                    return None

            start_t = parse_time(v_start.get())
            end_t   = parse_time(v_end.get())
            desc    = v_desc.get("1.0", "end-1c").strip() or None
            color   = color_var.get()
            all_day = int(all_day_var.get())

            try:
                if mode == "add":
                    insert_event(
                        self.current_patient["personal_id"],
                        title, desc, ev_date, start_t, end_t, color, all_day)
                else:
                    update_event(
                        event["event_id"],
                        title, desc, ev_date, start_t, end_t, color, all_day)
                dialog.destroy()
                self._render_calendar()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        self._styled_button(btn_row,
                             "✓  Save Event" if mode == "add" else "✓  Save Changes",
                             save, bg=SUCCESS, fg=TEXT_PRIMARY).pack(side="left")
        self._styled_button(btn_row, "Cancel", dialog.destroy,
                             bg=BG_DARK, fg=TEXT_MUTED,
                             outline=True).pack(side="left", padx=10)

    def _confirm_delete_event(self, event):
        confirmed = messagebox.askyesno(
            "Delete Event",
            f"Delete event:\n\n  \"{event['title']}\"\n\nThis cannot be undone.",
            icon="warning"
        )
        if confirmed:
            try:
                delete_event(event["event_id"])
                self._render_calendar()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ── Page: Relatives ──────────────────────────────────────────────────────
    def _build_relatives_page(self):
        page = tk.Frame(self.content, bg=BG_DARK)
        page.pack(fill="both", expand=True, padx=30, pady=25)

        # Header
        hdr = tk.Frame(page, bg=BG_DARK)
        hdr.pack(fill="x", pady=(0, 16))

        name = ""
        if self.current_patient:
            name = f" — {self.current_patient.get('first_name', '')} {self.current_patient.get('last_name', '')}"

        tk.Label(hdr, text=f"Family & Relatives{name}", font=FONT_HEADING,
                 fg=TEXT_PRIMARY, bg=BG_DARK).pack(side="left")

        def add_relative():
            if not self.current_patient:
                messagebox.showwarning("No Patient",
                                       "Please recognize or select a patient first.")
                return
            self._open_add_relative_dialog()

        self._styled_button(hdr, "＋  Add Relative", add_relative,
                             bg=ACCENT_TEAL, fg=BG_DARK).pack(side="right")

        if not self.current_patient:
            tk.Label(page, text="No patient selected. Recognize a patient via camera first.",
                     font=FONT_LABEL, fg=TEXT_MUTED, bg=BG_DARK).pack(pady=60)
            return

        personal_id = self.current_patient.get("personal_id")

        # Relatives list area
        list_frame = tk.Frame(page, bg=BG_DARK)
        list_frame.pack(fill="both", expand=True)

        try:
            relatives = get_relatives_by_patient(personal_id)
        except Exception as e:
            relatives = []
            tk.Label(list_frame, text=f"Error loading relatives: {e}",
                     fg=DANGER, bg=BG_DARK, font=FONT_LABEL).pack()

        if not relatives:
            empty = tk.Frame(list_frame, bg=BG_CARD)
            empty.pack(fill="x", pady=8)
            tk.Label(empty, text="No relatives added yet.",
                     font=FONT_LABEL, fg=TEXT_MUTED, bg=BG_CARD).pack(pady=40)
            return

        # Grid of relative cards
        cols = 3
        for i, rel in enumerate(relatives):
            row_idx = i // cols
            col_idx = i % cols
            self._relative_card(list_frame, rel, row_idx, col_idx)

        # Configure columns
        for c in range(cols):
            list_frame.columnconfigure(c, weight=1)

    def _relative_card(self, parent, rel, row, col):
        card = tk.Frame(parent, bg=BG_CARD, padx=0, pady=0)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        tk.Frame(card, bg=ACCENT_WARM, height=3).pack(fill="x")

        name = f"{rel.get('relative_first_name', '')} {rel.get('relative_last_name', '')}".strip()
        initials = (rel.get("relative_first_name", "?")[0] +
                    rel.get("relative_last_name", "?")[0]).upper()

        # Try to show thumbnail
        img_shown = False
        if PIL_AVAILABLE and rel.get("thumbnail"):
            try:
                thumb_data = rel["thumbnail"]
                img = Image.open(io.BytesIO(thumb_data)).resize((80, 80), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(card, image=photo, bg=BG_CARD)
                lbl.pack(pady=(16, 4))
                lbl._photo = photo
                img_shown = True
            except Exception:
                pass

        if not img_shown:
            av_frame = tk.Frame(card, bg=BG_CARD)
            av_frame.pack(pady=(16, 4))
            avatar_label(av_frame, initials, size=64,
                         bg=BG_CARD, fg=ACCENT_WARM).pack()

        tk.Label(card, text=name, font=FONT_CARD_TTL,
                 fg=TEXT_PRIMARY, bg=BG_CARD).pack()
        tk.Label(card, text=rel.get("relationship_type", "—"),
                 font=FONT_SMALL, fg=ACCENT_WARM, bg=BG_CARD).pack(pady=(2, 8))

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=16, pady=4)

        info_frame = tk.Frame(card, bg=BG_CARD)
        info_frame.pack(fill="x", padx=16, pady=(0, 4))

        for icon, field in [("📞", "phone_number"), ("✉", "email")]:
            val = rel.get(field) or "—"
            row_f = tk.Frame(info_frame, bg=BG_CARD)
            row_f.pack(fill="x", pady=1)
            tk.Label(row_f, text=f"{icon} {val}", font=FONT_SMALL,
                     fg=TEXT_MUTED, bg=BG_CARD, anchor="w").pack(anchor="w")

        def add_photo(r=rel):
            self._add_relative_photo(r)

        def remove_relative(r=rel):
            self._confirm_delete_relative(r)

        self._styled_button(card, "📷  Update Photo", add_photo,
                             bg=BG_DARK, fg=TEXT_MUTED, outline=True).pack(
            fill="x", padx=16, pady=(8, 4))
        self._styled_button(card, "🗑  Remove Relative", remove_relative,
                             bg=DANGER, fg=TEXT_PRIMARY).pack(
            fill="x", padx=16, pady=(0, 16))

    def _add_relative_photo(self, rel):
        """Capture or upload photo for a relative."""
        choice = messagebox.askyesno("Add Photo",
                                      "Capture from camera?\n\n"
                                      "Yes = Camera  |  No = Upload file")
        relative_id = rel.get("relative_id")
        personal_id = self.current_patient.get("personal_id") if self.current_patient else 0

        if choice:
            save_path = os.path.join(BASE_DIR, f"temp_relative_{relative_id}.jpg")
            success = capture_face_from_camera(save_path)
            if success:
                thumb, full_path = save_image_for_patient(personal_id, relative_id, save_path)
                if thumb:
                    update_relative_image(relative_id, thumb, full_path)
                    messagebox.showinfo("Success", "Photo updated!")
                    self.show_page("relatives")
        else:
            path = filedialog.askopenfilename(
                title="Select Photo",
                filetypes=[("Images", "*.jpg *.jpeg *.png")]
            )
            if path:
                thumb, full_path = save_image_for_patient(personal_id, relative_id, path)
                if thumb:
                    update_relative_image(relative_id, thumb, full_path)
                    messagebox.showinfo("Success", "Photo updated!")
                    self.show_page("relatives")

    def _confirm_delete_relative(self, rel):
        """Single confirm dialog to delete a relative record."""
        name        = f"{rel.get('relative_first_name', '')} {rel.get('relative_last_name', '')}".strip()
        rel_type    = rel.get("relationship_type", "")
        relative_id = rel.get("relative_id")

        confirmed = messagebox.askyesno(
            "Remove Relative",
            f"Remove the following relative?\n\n"
            f"  {name}  ({rel_type})\n\n"
            f"Their record and photo will be permanently deleted.\n"
            f"This cannot be undone.",
            icon="warning"
        )
        if not confirmed:
            return

        try:
            success = delete_relative(relative_id)
            if success:
                # Delete their image file from disk if it exists
                full_path = rel.get("full_image_path")
                if full_path and os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                        print(f"[Delete] Removed relative image: {full_path}")
                    except Exception as e:
                        print(f"[Delete] Could not remove image: {e}")
                messagebox.showinfo("Removed", f"{name} has been removed.")
                self.show_page("relatives")
            else:
                messagebox.showerror("Error", "Could not remove relative.")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def _open_add_relative_dialog(self):
        """Modal dialog to add a relative."""
        dialog = tk.Toplevel(self)
        dialog.title("Add Relative")
        dialog.geometry("480x580")
        dialog.configure(bg=BG_DARK)
        dialog.grab_set()

        tk.Label(dialog, text="Add Family Member", font=FONT_HEADING,
                 fg=TEXT_PRIMARY, bg=BG_DARK).pack(anchor="w", padx=24, pady=(20, 4))
        tk.Label(dialog, text="Enter the relative's information below.",
                 font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_DARK).pack(anchor="w", padx=24)

        tk.Frame(dialog, bg=BORDER, height=1).pack(fill="x", padx=24, pady=12)

        form = tk.Frame(dialog, bg=BG_DARK)
        form.pack(fill="both", expand=True, padx=24)

        fields = {}

        def dialog_entry(label, key, placeholder=""):
            f = tk.Frame(form, bg=BG_DARK)
            f.pack(fill="x", pady=6)
            tk.Label(f, text=label, font=FONT_SMALL, fg=TEXT_MUTED,
                     bg=BG_DARK, anchor="w").pack(anchor="w")
            var = tk.StringVar()
            e = tk.Entry(f, textvariable=var, font=FONT_LABEL,
                          bg="#1C2128", fg=TEXT_PRIMARY,
                          insertbackground=ACCENT_TEAL,
                          relief="flat", bd=0, highlightthickness=1,
                          highlightcolor=ACCENT_TEAL, highlightbackground=BORDER)
            e.pack(fill="x", ipady=7)
            fields[key] = var
            return var

        dialog_entry("First Name *", "first_name")
        dialog_entry("Last Name *", "last_name")
        dialog_entry("Relationship (e.g. Son, Daughter, Spouse) *", "relationship")
        dialog_entry("Phone Number", "phone")
        dialog_entry("Email", "email")

        # Photo option
        photo_var = tk.StringVar()
        photo_frame = tk.Frame(form, bg=BG_DARK)
        photo_frame.pack(fill="x", pady=8)
        tk.Label(photo_frame, text="Photo (optional)", font=FONT_SMALL,
                 fg=TEXT_MUTED, bg=BG_DARK).pack(anchor="w")
        photo_btn_row = tk.Frame(photo_frame, bg=BG_DARK)
        photo_btn_row.pack(fill="x", pady=4)

        self._styled_button(photo_btn_row, "📷 Camera",
                             lambda: self._quick_capture(photo_var),
                             bg=BG_CARD, fg=TEXT_MUTED, outline=True).pack(side="left", padx=(0, 8))
        self._styled_button(photo_btn_row, "📂 Upload",
                             lambda: self._quick_upload(photo_var),
                             bg=BG_CARD, fg=TEXT_MUTED, outline=True).pack(side="left")

        photo_status = tk.Label(photo_frame, textvariable=photo_var,
                                 font=FONT_SMALL, fg=ACCENT_TEAL, bg=BG_DARK)
        photo_status.pack(anchor="w")

        def submit():
            first = fields["first_name"].get().strip()
            last = fields["last_name"].get().strip()
            rel = fields["relationship"].get().strip()
            phone = fields["phone"].get().strip() or None
            email = fields["email"].get().strip() or None

            if not first or not last or not rel:
                messagebox.showerror("Validation",
                                     "First Name, Last Name, and Relationship are required.")
                return

            personal_id = self.current_patient["personal_id"]
            try:
                relative_id = insert_relatives_contacts(
                    personal_id=personal_id,
                    relative_first_name=first,
                    relative_last_name=last,
                    relationship_type=rel,
                    phone_number=phone,
                    email=email,
                    thumbnail=None,
                    full_image_path=None
                )

                # Save photo if provided
                face_path = photo_var.get()
                if face_path and os.path.exists(face_path) and relative_id:
                    thumb, full_path = save_image_for_patient(
                        personal_id, relative_id, face_path)
                    if thumb:
                        update_relative_image(relative_id, thumb, full_path)

                dialog.destroy()
                messagebox.showinfo("Success", f"Relative {first} {last} added!")
                self.show_page("relatives")

            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Frame(dialog, bg=BORDER, height=1).pack(fill="x", padx=24, pady=12)
        btn_row = tk.Frame(dialog, bg=BG_DARK)
        btn_row.pack(fill="x", padx=24, pady=(0, 20))
        self._styled_button(btn_row, "✓  Save Relative", submit,
                             bg=SUCCESS, fg=TEXT_PRIMARY).pack(side="left")
        self._styled_button(btn_row, "Cancel", dialog.destroy,
                             bg=BG_DARK, fg=TEXT_MUTED, outline=True).pack(side="left", padx=10)

    def _quick_capture(self, path_var):
        save_path = os.path.join(BASE_DIR, "temp_relative_photo.jpg")
        if capture_face_from_camera(save_path):
            path_var.set(save_path)

    def _quick_upload(self, path_var):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if path:
            path_var.set(path)

    # ── Reusable Styled Button ────────────────────────────────────────────────
    def _styled_button(self, parent, text, command, bg=ACCENT_TEAL,
                        fg=BG_DARK, outline=False):
        if outline:
            btn = tk.Label(parent, text=text, font=("Helvetica Neue", 10, "bold"),
                            fg=fg, bg=parent["bg"], cursor="hand2",
                            padx=14, pady=6,
                            relief="flat", bd=1)
            btn.config(highlightthickness=1, highlightbackground=BORDER,
                        highlightcolor=ACCENT_TEAL)
        else:
            btn = tk.Label(parent, text=text, font=("Helvetica Neue", 10, "bold"),
                            fg=fg, bg=bg, cursor="hand2", padx=14, pady=6)

        def on_enter(e):
            btn.config(bg=ACCENT_TEAL if not outline else "#1C2128", fg=BG_DARK if not outline else TEXT_PRIMARY)

        def on_leave(e):
            btn.config(bg=bg if not outline else parent["bg"], fg=fg)

        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def on_close(self):
        self._stop_camera()
        self.destroy()


# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = AlzheimerCareApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()