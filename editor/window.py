"""The main Tkinter window and its top-level frames."""

import os
from tkinter import Tk, Frame, PhotoImage


class MainWindow:
    """Creates the root window, optional icon, and the four main frames."""

    BG = "#323946"

    def __init__(self, script_dir, on_close):
        self.root = Tk()
        self.root.geometry("1200x800")
        self.root.minsize(760, 580)
        self.root.title("Image Editor")
        self.root.configure(bg=self.BG)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self.root.protocol("WM_DELETE_WINDOW", on_close)

        # Load the optional application icon.
        try:
            icon_path = os.path.join(script_dir, "icon.png")
            self.app_icon = PhotoImage(file=icon_path)
            self.root.iconphoto(False, self.app_icon)
        except Exception:
            self.app_icon = None

        self._create_frames()

    def _create_frames(self):
        self.toolbar = Frame(self.root, bg=self.BG)
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        self.toolbar.grid_columnconfigure(4, weight=1)

        self.editor_frame = Frame(self.root, bg=self.BG)
        self.editor_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(12, 6),
            pady=6,
        )
        self.editor_frame.grid_rowconfigure(0, weight=1)
        self.editor_frame.grid_columnconfigure(0, weight=1)

        self.controls_frame = Frame(self.root, bg=self.BG)
        self.controls_frame.grid(
            row=1,
            column=1,
            sticky="nsew",
            padx=(6, 12),
            pady=6,
        )
        self.controls_frame.grid_columnconfigure(
            0,
            weight=1,
            uniform="controls",
        )
        self.controls_frame.grid_columnconfigure(
            1,
            weight=1,
            uniform="controls",
        )

        self.status_frame = Frame(self.root, bg=self.BG)
        self.status_frame.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=12,
            pady=(4, 10),
        )
        self.status_frame.grid_columnconfigure(1, weight=1)
