"""
gui.py
CustomTkinter interface for reAlIty. Black & white, clean and minimal.
Lets the user browse to any image or video on their computer (no need to
drop it into the project folder), preview it, run detection, and see a
Human % vs AI % result.
"""

import os
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from detector import detect_image, detect_video
from media_utils import detect_media_type, load_image

ctk.set_appearance_mode("dark")

# --- Black & white palette -------------------------------------------------
BG_COLOR = "#0d0d0d"
CARD_COLOR = "#1a1a1a"
TEXT_COLOR = "#f5f5f5"
MUTED_COLOR = "#8a8a8a"
BORDER_COLOR = "#333333"
ACCENT = "#ffffff"
# ----------------------------------------------------------------------------


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("reAlIty")
        self.geometry("480x700")
        self.configure(fg_color=BG_COLOR)
        self.resizable(False, False)

        try:
            self.iconbitmap(os.path.join("assets", "icon.ico"))
        except Exception:
            pass  # no icon yet, not a big deal

        self.selected_path = None
        self.is_video = False

        self._build_layout()

    # ------------------------------------------------------------------ UI
    def _build_layout(self):
        ctk.CTkLabel(
            self, text="reAlIty",
            font=ctk.CTkFont(family="Georgia", size=34, weight="bold"),
            text_color=ACCENT,
        ).pack(pady=(30, 0))

        ctk.CTkLabel(
            self, text="AI or Not? Find out.",
            font=ctk.CTkFont(size=13), text_color=MUTED_COLOR,
        ).pack(pady=(2, 20))

        # --- preview card ---
        self.preview_frame = ctk.CTkFrame(
            self, width=380, height=260, fg_color=CARD_COLOR,
            border_color=BORDER_COLOR, border_width=1, corner_radius=12,
        )
        self.preview_frame.pack(pady=(0, 20))
        self.preview_frame.pack_propagate(False)

        self.preview_label = ctk.CTkLabel(
            self.preview_frame, text="No file selected",
            text_color=MUTED_COLOR, font=ctk.CTkFont(size=13),
        )
        self.preview_label.pack(expand=True)

        # --- buttons row ---
        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(pady=(0, 15))

        self.upload_btn = ctk.CTkButton(
            button_row, text="Upload Image / Video", width=170, height=40,
            fg_color="transparent", border_color=ACCENT, border_width=1,
            text_color=TEXT_COLOR, hover_color=CARD_COLOR, corner_radius=8,
            command=self.upload_file,
        )
        self.upload_btn.grid(row=0, column=0, padx=6)

        self.verify_btn = ctk.CTkButton(
            button_row, text="Verify", width=170, height=40,
            fg_color=ACCENT, text_color="#000000", hover_color="#cfcfcf",
            corner_radius=8, command=self.run_verification, state="disabled",
        )
        self.verify_btn.grid(row=0, column=1, padx=6)

        # --- progress bar + status ---
        self.progress_bar = ctk.CTkProgressBar(
            self, width=380, height=6, fg_color=BORDER_COLOR,
            progress_color=ACCENT,
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(5, 5))

        self.status_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), text_color=MUTED_COLOR,
        )
        self.status_label.pack(pady=(0, 15))

        # --- result card ---
        self.result_frame = ctk.CTkFrame(
            self, width=380, height=185, fg_color=CARD_COLOR,
            border_color=BORDER_COLOR, border_width=1, corner_radius=12,
        )
        self.result_frame.pack(pady=(0, 15))
        self.result_frame.pack_propagate(False)

        self.verdict_label = ctk.CTkLabel(
            self.result_frame, text="Awaiting analysis",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_COLOR,
        )
        self.verdict_label.pack(pady=(20, 12))

        self.ai_label = ctk.CTkLabel(
            self.result_frame, text="AI-Generated:  --%",
            font=ctk.CTkFont(size=14), text_color=TEXT_COLOR,
        )
        self.ai_label.pack()

        self.human_label = ctk.CTkLabel(
            self.result_frame, text="Human-Made:  --%",
            font=ctk.CTkFont(size=14), text_color=TEXT_COLOR,
        )
        self.human_label.pack(pady=(2, 10))

        self.warning_label = ctk.CTkLabel(
            self.result_frame, text="", font=ctk.CTkFont(size=11, slant="italic"),
            text_color=MUTED_COLOR, wraplength=340, justify="center",
        )
        self.warning_label.pack(pady=(0, 8))

        # --- clear button ---
        self.clear_btn = ctk.CTkButton(
            self, text="Clear", width=100, height=32, fg_color="transparent",
            border_color=MUTED_COLOR, border_width=1, text_color=MUTED_COLOR,
            hover_color=CARD_COLOR, corner_radius=8, command=self.clear_all,
        )
        self.clear_btn.pack(pady=(0, 20))

    # ------------------------------------------------------------- actions
    def upload_file(self):
        path = filedialog.askopenfilename(
            title="Select an image or video",
            filetypes=[
                ("All image and video files", "*.*"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return  # user cancelled the dialog

        try:
            media_type = detect_media_type(path)
        except ValueError as error:
            messagebox.showerror("Unsupported file", str(error))
            return

        self.selected_path = path
        self.is_video = media_type == "video"

        if self.is_video:
            self._show_video_placeholder(path)
        else:
            self._show_image_preview(path)

        self.verify_btn.configure(state="normal")
        self.status_label.configure(text=f"Selected: {os.path.basename(path)}")

    def _show_image_preview(self, path):
        try:
            img = load_image(path)
            img.thumbnail((360, 240))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self.preview_label.configure(image=ctk_img, text="")
            self.preview_label.image = ctk_img  # keep a reference
        except Exception:
            self.preview_label.configure(text="Could not load preview", image=None)

    def _show_video_placeholder(self, path):
        self.preview_label.configure(
            image=None, text=f"Video selected:\n{os.path.basename(path)}"
        )

    def run_verification(self):
        if not self.selected_path:
            return

        self.verify_btn.configure(state="disabled")
        self.upload_btn.configure(state="disabled")
        self.verdict_label.configure(text="Analyzing...", text_color=TEXT_COLOR)
        self.ai_label.configure(text="AI-Generated:  --%")
        self.human_label.configure(text="Human-Made:  --%")
        self.warning_label.configure(text="")
        self.status_label.configure(text="Loading model (first run may take a moment)...")

        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()

        threading.Thread(target=self._analyze, daemon=True).start()

    def _analyze(self):
        try:
            if self.is_video:
                # switch to determinate mode once we know frame progress
                self.after(0, self._switch_to_determinate)

                def progress_cb(current, total):
                    self.after(0, lambda: self.progress_bar.set(current / total))
                    self.after(0, lambda: self.status_label.configure(
                        text=f"Analyzing frame {current}/{total}..."
                    ))

                result = detect_video(self.selected_path, progress_callback=progress_cb)
            else:
                result = detect_image(self.selected_path)
        except Exception as e:
            result = {"error": str(e)}

        self.after(0, lambda: self._show_result(result))

    def _switch_to_determinate(self):
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)

    def _show_result(self, result):
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.verify_btn.configure(state="normal")
        self.upload_btn.configure(state="normal")

        if "error" in result:
            self.verdict_label.configure(text="Something went wrong")
            self.status_label.configure(text=result["error"])
            self.progress_bar.set(0)
            return

        ai_score = result.get("ai", 0)
        hum_score = result.get("hum", 0)

        self.progress_bar.set(ai_score / 100)
        self.ai_label.configure(text=f"AI-Generated:  {ai_score}%")
        self.human_label.configure(text=f"Human-Made:  {hum_score}%")

        if ai_score > hum_score:
            self.verdict_label.configure(text="Likely AI-Generated")
        else:
            self.verdict_label.configure(text="Likely Human-Made")

        if result.get("overlay_detected"):
            self.warning_label.configure(
                text="⚠ Heavy text, arrows, circles, or graphic overlays detected "
                     "on this file — that tends to reduce detection accuracy, so "
                     "treat this result with extra caution."
            )
        else:
            self.warning_label.configure(text="")

        self.status_label.configure(text="Analysis complete")

    def clear_all(self):
        self.selected_path = None
        self.is_video = False
        self.preview_label.configure(image=None, text="No file selected")
        self.verify_btn.configure(state="disabled")
        self.verdict_label.configure(text="Awaiting analysis", text_color=TEXT_COLOR)
        self.ai_label.configure(text="AI-Generated:  --%")
        self.human_label.configure(text="Human-Made:  --%")
        self.warning_label.configure(text="")
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)
        self.status_label.configure(text="")
