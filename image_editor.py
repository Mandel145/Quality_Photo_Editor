"""
Object-oriented Tkinter image editor.

The original global variables and standalone functions have been
organized into the ImageEditor class. The visible interface and
editing behavior remain the same.
"""

import os
from tkinter import (
    Tk,
    Frame,
    Canvas,
    Label,
    Button,
    Scale,
    PhotoImage,
    CENTER,
    HORIZONTAL,
    NORMAL,
    DISABLED,
    filedialog,
    messagebox,
)

from PIL import (
    Image,
    ImageTk,
    ImageEnhance,
    ImageDraw,
)

from image_operations import apply_modifier, get_resample_filter


class ImageEditor:
    """Main application class containing the UI and editor state."""

    def __init__(self):
        # Directory containing this Python file and optional image assets.
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        # Current crop/resize interaction state.
        self.current_mode = None
        self.bbox = [0, 0, 0, 0]
        self.active_handle = None
        self.handle_size = 12

        # Image viewport state.
        self.img_canvas_x = 0
        self.img_canvas_y = 0
        self.scale_factor = 1.0
        self.zoom_level = 1.0
        self.fit_zoom_level = 1.0
        self.resize_zoom = 1.0
        self.pan_x = 300
        self.pan_y = 300
        self.last_pan_x = 0
        self.last_pan_y = 0
        self.last_canvas_size = None

        # Display cache objects used by Tkinter.
        self.checkerboard_bg = None
        self.checkerboard_size = None
        self.clean_disp_img = None
        self.image_item_id = None
        self.preview_tk = None
        self.dispimage = None

        # Undo/redo state.
        self.action_history = []
        self.current_step = 0
        self.is_rendering = False
        self.slider_start_vals = {}
        self.unsaved_changes = False

        # Create the root window and initialize the image.
        self.create_window()
        self.load_startup_image()
        self.create_layout()
        self.create_bindings()
        self.create_widgets()

        # Display the initial image after all widgets exist.
        self.display_image(self.img)
        self.update_button_states()

    # ------------------------------------------------------------------
    # Window and startup setup
    # ------------------------------------------------------------------

    def create_window(self):
        """Create and configure the main Tkinter window."""
        self.mains = Tk()
        self.mains.geometry("1200x800")
        self.mains.minsize(760, 580)
        self.mains.title("Image Editor")
        self.mains.configure(bg="#323946")
        self.mains.grid_columnconfigure(0, weight=1)
        self.mains.grid_rowconfigure(1, weight=1)

        self.mains.protocol("WM_DELETE_WINDOW", self.close)

        # Load the optional application icon.
        try:
            icon_path = os.path.join(self.script_dir, "icon.png")
            self.app_icon = PhotoImage(file=icon_path)
            self.mains.iconphoto(False, self.app_icon)
        except Exception:
            self.app_icon = None

    def load_startup_image(self):
        """Load logo.png or create the same fallback image as the original."""
        try:
            logo_path = os.path.join(self.script_dir, "logo.png")
            initial_img = Image.open(logo_path)
        except FileNotFoundError:
            initial_img = Image.new("RGB", (600, 600), color="#323946")

        self.original_img = initial_img.copy()
        self.base_image = initial_img.copy()
        self.img = initial_img.copy()
        self.output_image = initial_img.copy()

    def create_layout(self):
        """Create the main frames and canvas."""
        self.toolbar = Frame(self.mains, bg="#323946")
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        self.toolbar.grid_columnconfigure(4, weight=1)

        self.editor_frame = Frame(self.mains, bg="#323946")
        self.editor_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(12, 6),
            pady=6,
        )
        self.editor_frame.grid_rowconfigure(0, weight=1)
        self.editor_frame.grid_columnconfigure(0, weight=1)

        self.controls_frame = Frame(self.mains, bg="#323946")
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

        self.status_frame = Frame(self.mains, bg="#323946")
        self.status_frame.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=12,
            pady=(4, 10),
        )
        self.status_frame.grid_columnconfigure(1, weight=1)

        self.panel = Canvas(
            self.editor_frame,
            bg="#323946",
            highlightthickness=0,
        )
        self.panel.grid(row=0, column=0, sticky="nsew")

        self.dim_label = Label(
            self.status_frame,
            text="",
            bg="#323946",
            fg="white",
            font=("poppins", 10, "bold"),
        )
        self.dim_label.grid(row=0, column=0, sticky="w", padx=(0, 16))

        self.coord_label = Label(
            self.status_frame,
            text="Cursor: X: 0, Y: 0 px",
            bg="#323946",
            fg="#00ffcc",
            font=("poppins", 10, "bold"),
        )
        self.coord_label.grid(row=0, column=1, sticky="w")

        Label(
            self.status_frame,
            text="Mouse Wheel: Zoom  |  Right/Middle Drag: Pan",
            bg="#323946",
            fg="gray",
            font=("poppins", 9, "italic"),
        ).grid(row=0, column=2, sticky="e")

    def create_bindings(self):
        """Connect mouse, keyboard, and window events to editor methods."""
        self.panel.bind("<ButtonPress-1>", self.start_drag)
        self.panel.bind("<B1-Motion>", self.drag)
        self.panel.bind("<ButtonRelease-1>", self.end_drag)
        self.panel.bind("<Motion>", self.track_mouse)
        self.panel.bind("<Configure>", self.resize_canvas)

        self.panel.bind("<MouseWheel>", self.zoom)
        self.panel.bind("<Button-4>", self.zoom)
        self.panel.bind("<Button-5>", self.zoom)

        self.panel.bind("<ButtonPress-2>", self.start_pan)
        self.panel.bind("<B2-Motion>", self.do_pan)
        self.panel.bind("<ButtonPress-3>", self.start_pan)
        self.panel.bind("<B3-Motion>", self.do_pan)

        self.mains.bind("<Return>", self.apply_action)
        self.mains.bind("<Escape>", self.cancel_action)

    def create_widgets(self):
        """Create all sliders and buttons used by the original interface."""
        self.brightness_slider = self.create_slider(
            "Brightness",
            row=0,
            slider_type="brightness",
        )
        self.contrast_slider = self.create_slider(
            "Contrast",
            row=1,
            slider_type="contrast",
        )
        self.sharpness_slider = self.create_slider(
            "Sharpness",
            row=2,
            slider_type="sharpness",
        )
        self.color_slider = self.create_slider(
            "Colors",
            row=3,
            slider_type="color",
        )

        self.btn_rotate = self.create_control_button(
            "Rotate",
            self.rotate,
            4,
            0,
        )
        self.btn_change_image = self.create_control_button(
            "Change Image",
            self.change_image,
            4,
            1,
            activebackground="ORANGE",
        )
        self.btn_flip = self.create_control_button("Flip", self.flip, 5, 0)
        self.btn_resize = self.create_control_button(
            "Resize",
            self.activate_resize,
            5,
            1,
        )
        self.btn_crop = self.create_control_button(
            "Crop",
            self.activate_crop,
            6,
            0,
        )
        self.btn_blur = self.create_control_button(
            "Blur",
            self.blur,
            6,
            1,
        )
        self.btn_emboss = self.create_control_button(
            "Emboss",
            self.emboss,
            7,
            0,
        )
        self.btn_edge_enhance = self.create_control_button(
            "EdgeEnhance",
            self.edge_enhance,
            7,
            1,
        )

        self.btn_save = Button(
            self.controls_frame,
            text="Save",
            width=16,
            command=self.save,
            bg="black",
        )
        self.btn_save.configure(
            font=("poppins", 11, "bold"),
            foreground="white",
        )
        self.btn_save.grid(
            row=8,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=4,
            pady=3,
        )

        self.reset_button = Button(
            self.toolbar,
            text="Reset",
            command=self.reset,
            bg="black",
            activebackground="ORANGE",
        )
        self.reset_button.configure(
            font=("poppins", 10, "bold"),
            foreground="white",
        )
        self.reset_button.grid(row=0, column=0, padx=3)

        self.btn_close = Button(
            self.toolbar,
            text="Close",
            command=self.close,
            bg="black",
            activebackground="ORANGE",
        )
        self.btn_close.configure(
            font=("poppins", 10, "bold"),
            foreground="white",
        )
        self.btn_close.grid(row=0, column=1, padx=3)

        self.btn_undo = Button(
            self.toolbar,
            text="Undo",
            command=self.undo,
            bg="black",
            activebackground="ORANGE",
        )
        self.btn_undo.configure(
            font=("poppins", 10, "bold"),
            foreground="white",
        )
        self.btn_undo.grid(row=0, column=2, padx=3)

        self.btn_redo = Button(
            self.toolbar,
            text="Redo",
            command=self.redo,
            bg="black",
            activebackground="ORANGE",
        )
        self.btn_redo.configure(
            font=("poppins", 10, "bold"),
            foreground="white",
        )
        self.btn_redo.grid(row=0, column=3, padx=3)

    def create_slider(self, label, row, slider_type):
        """Create one adjustment slider with its mouse event handlers."""
        slider = Scale(
            self.controls_frame,
            label=label,
            from_=0,
            to=2,
            orient=HORIZONTAL,
            length=120,
            resolution=0.1,
            command=self.on_slider_move,
            bg="#1f242d",
        )
        slider.set(1)
        slider.configure(
            font=("poppins", 11, "bold"),
            foreground="white",
        )
        slider.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=4,
            pady=2,
        )
        slider.bind(
            "<ButtonPress-1>",
            lambda event: self.on_slider_press(
                slider_type,
                slider,
            ),
        )
        slider.bind(
            "<ButtonRelease-1>",
            lambda event: self.on_slider_release(
                slider_type,
                slider,
            ),
        )
        return slider

    def create_control_button(
        self,
        text,
        command,
        row,
        column,
        activebackground=None,
    ):
        """Create one of the two-column editing buttons."""
        options = {
            "text": text,
            "width": 16,
            "command": command,
            "bg": "#1f242d",
        }

        if activebackground is not None:
            options["activebackground"] = activebackground

        button = Button(self.controls_frame, **options)
        button.configure(
            font=("poppins", 11, "bold"),
            foreground="white",
        )
        button.grid(
            row=row,
            column=column,
            sticky="ew",
            padx=4,
            pady=3,
        )
        return button

    # ------------------------------------------------------------------
    # Viewport and display methods
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_fit_zoom(image_size, canvas_size):
        """Calculate a proportional zoom that fits an image in the canvas."""
        image_width, image_height = image_size
        canvas_width, canvas_height = canvas_size

        available_width = max(1, canvas_width - 40)
        available_height = max(1, canvas_height - 40)

        return min(
            available_width / image_width,
            available_height / image_height,
            1.0,
        )

    def generate_checkerboard(self, width, height):
        """Generate the gray-and-white transparency background."""
        base = Image.new("RGB", (40, 40), color="#ffffff")
        draw = ImageDraw.Draw(base)
        draw.rectangle([20, 0, 39, 19], fill="#cccccc")
        draw.rectangle([0, 20, 19, 39], fill="#cccccc")

        checkerboard = Image.new("RGB", (width, height))

        for y in range(0, height, 40):
            for x in range(0, width, 40):
                checkerboard.paste(base, (x, y))

        return ImageTk.PhotoImage(checkerboard)

    def reset_viewport(self, image):
        """Fit a newly loaded or reset image to the visible canvas."""
        width, height = image.size
        canvas_width = self.panel.winfo_width()
        canvas_height = self.panel.winfo_height()

        canvas_width = canvas_width if canvas_width > 1 else 600
        canvas_height = canvas_height if canvas_height > 1 else 600

        self.fit_zoom_level = self.calculate_fit_zoom(
            (width, height),
            (canvas_width, canvas_height),
        )
        self.zoom_level = self.fit_zoom_level
        self.resize_zoom = 1.0
        self.pan_x = canvas_width / 2
        self.pan_y = canvas_height / 2
        self.last_canvas_size = (canvas_width, canvas_height)

    def display_image(self, image_to_display):
        """Render the image, checkerboard, rulers, and active overlays."""
        canvas_width = max(1, self.panel.winfo_width())
        canvas_height = max(1, self.panel.winfo_height())

        if (
            self.checkerboard_bg is None
            or self.checkerboard_size != (canvas_width, canvas_height)
        ):
            self.checkerboard_bg = self.generate_checkerboard(
                canvas_width,
                canvas_height,
            )
            self.checkerboard_size = (canvas_width, canvas_height)

        original_width, original_height = image_to_display.size
        display_width = max(
            1,
            int(original_width * self.zoom_level),
        )
        display_height = max(
            1,
            int(original_height * self.zoom_level),
        )

        display_image = image_to_display.resize(
            (display_width, display_height),
            get_resample_filter(),
        )

        self.clean_disp_img = display_image.copy()
        self.dispimage = ImageTk.PhotoImage(display_image)
        self.scale_factor = self.zoom_level

        self.img_canvas_x = self.pan_x - display_width / 2
        self.img_canvas_y = self.pan_y - display_height / 2

        self.panel.delete("all")
        self.panel.create_image(
            canvas_width / 2,
            canvas_height / 2,
            image=self.checkerboard_bg,
            anchor=CENTER,
        )
        self.image_item_id = self.panel.create_image(
            self.pan_x,
            self.pan_y,
            image=self.dispimage,
            anchor=CENTER,
        )
        self.panel.image = self.dispimage

        self.draw_rulers(original_width, original_height)

        if self.current_mode in ("crop", "resize"):
            self.draw_handles()

    def resize_canvas(self, event):
        """Keep the image centered and preserve active selection coordinates."""
        if event.width <= 1 or event.height <= 1:
            return

        new_size = (event.width, event.height)

        if self.last_canvas_size == new_size:
            return

        old_zoom = self.zoom_level
        old_image_left = (
            self.pan_x - self.img.width * old_zoom / 2
        )
        old_image_top = (
            self.pan_y - self.img.height * old_zoom / 2
        )
        old_bbox = (
            tuple(self.bbox)
            if self.current_mode in ("crop", "resize")
            else None
        )

        if self.last_canvas_size is None:
            self.resize_zoom = 1.0

        self.fit_zoom_level = self.calculate_fit_zoom(
            self.img.size,
            new_size,
        )
        self.zoom_level = self.fit_zoom_level * self.resize_zoom
        self.pan_x = event.width / 2
        self.pan_y = event.height / 2

        if old_bbox is not None:
            new_image_left = (
                self.pan_x - self.img.width * self.zoom_level / 2
            )
            new_image_top = (
                self.pan_y - self.img.height * self.zoom_level / 2
            )

            self.bbox[0] = (
                new_image_left
                + (old_bbox[0] - old_image_left)
                / old_zoom
                * self.zoom_level
            )
            self.bbox[2] = (
                new_image_left
                + (old_bbox[2] - old_image_left)
                / old_zoom
                * self.zoom_level
            )
            self.bbox[1] = (
                new_image_top
                + (old_bbox[1] - old_image_top)
                / old_zoom
                * self.zoom_level
            )
            self.bbox[3] = (
                new_image_top
                + (old_bbox[3] - old_image_top)
                / old_zoom
                * self.zoom_level
            )

        self.last_canvas_size = new_size
        self.display_image(self.output_image)

    def draw_rulers(self, image_width, image_height):
        """Draw rulers and update the image dimensions status label."""
        canvas_width = max(1, self.panel.winfo_width())
        canvas_height = max(1, self.panel.winfo_height())

        self.panel.create_rectangle(
            0,
            0,
            canvas_width,
            22,
            fill="#1f242d",
            outline="#4f5b66",
        )
        self.panel.create_rectangle(
            0,
            0,
            22,
            canvas_height,
            fill="#1f242d",
            outline="#4f5b66",
        )
        self.panel.create_rectangle(
            0,
            0,
            22,
            22,
            fill="#14181d",
            outline="#4f5b66",
        )

        step = 100
        if self.zoom_level < 0.3:
            step = 500
        elif self.zoom_level < 0.7:
            step = 200
        elif self.zoom_level > 2.0:
            step = 50
        elif self.zoom_level > 5.0:
            step = 10

        for x_value in range(0, image_width + 1, step):
            canvas_x = (
                self.img_canvas_x
                + x_value * self.scale_factor
            )
            if 22 <= canvas_x <= canvas_width:
                self.panel.create_line(
                    canvas_x,
                    15,
                    canvas_x,
                    22,
                    fill="white",
                )
                if x_value > 0:
                    self.panel.create_text(
                        canvas_x,
                        8,
                        text=str(x_value),
                        fill="#a0a0a0",
                        font=("Arial", 7),
                    )

        for y_value in range(0, image_height + 1, step):
            canvas_y = (
                self.img_canvas_y
                + y_value * self.scale_factor
            )
            if 22 <= canvas_y <= canvas_height:
                self.panel.create_line(
                    15,
                    canvas_y,
                    22,
                    canvas_y,
                    fill="white",
                )
                if y_value > 0:
                    self.panel.create_text(
                        10,
                        canvas_y,
                        text=str(y_value),
                        fill="#a0a0a0",
                        font=("Arial", 7),
                        angle=90,
                    )

        self.dim_label.config(
            text=(
                f"Image Size: {image_width} x {image_height} px"
                f"  |  Zoom: {int(self.zoom_level * 100)}%"
            )
        )

    def track_mouse(self, event):
        """Show the image pixel coordinate under the mouse cursor."""
        if self.clean_disp_img is None:
            return

        image_x = int(
            (event.x - self.img_canvas_x) / self.scale_factor
        )
        image_y = int(
            (event.y - self.img_canvas_y) / self.scale_factor
        )

        width, height = self.img.size

        if 0 <= image_x < width and 0 <= image_y < height:
            self.coord_label.config(
                text=f"Cursor: X: {image_x}, Y: {image_y} px"
            )
        else:
            self.coord_label.config(text="Cursor: Outside Image")

    # ------------------------------------------------------------------
    # Zoom, pan, crop, and resize interactions
    # ------------------------------------------------------------------

    def zoom(self, event):
        """Zoom around the current mouse position."""
        if self.current_mode in ("crop", "resize"):
            self.cancel_action()

        old_zoom = self.zoom_level

        if event.num == 4 or getattr(event, "delta", 0) > 0:
            self.zoom_level *= 1.15
        elif event.num == 5 or getattr(event, "delta", 0) < 0:
            self.zoom_level /= 1.15

        self.zoom_level = max(0.01, min(self.zoom_level, 50.0))
        self.resize_zoom = self.zoom_level / self.fit_zoom_level

        scale_ratio = self.zoom_level / old_zoom
        self.pan_x = event.x - (event.x - self.pan_x) * scale_ratio
        self.pan_y = event.y - (event.y - self.pan_y) * scale_ratio

        self.display_image(self.output_image)

    def start_pan(self, event):
        """Record the starting point for a middle/right-button pan."""
        self.last_pan_x = event.x
        self.last_pan_y = event.y

    def do_pan(self, event):
        """Move the image while panning."""
        self.pan_x += event.x - self.last_pan_x
        self.pan_y += event.y - self.last_pan_y
        self.last_pan_x = event.x
        self.last_pan_y = event.y

        self.display_image(self.output_image)

    def draw_handles(self):
        """Draw selection handles and the crop/resize preview."""
        self.panel.delete("overlay")

        x1, x2 = sorted([self.bbox[0], self.bbox[2]])
        y1, y2 = sorted([self.bbox[1], self.bbox[3]])

        if self.current_mode == "resize":
            color = "cyan"
            width = int(max(1, x2 - x1))
            height = int(max(1, y2 - y1))

            if self.clean_disp_img is not None and self.image_item_id:
                preview = self.clean_disp_img.resize(
                    (width, height),
                    Image.NEAREST,
                )
                self.preview_tk = ImageTk.PhotoImage(preview)
                self.panel.itemconfig(
                    self.image_item_id,
                    image=self.preview_tk,
                )
                self.panel.coords(
                    self.image_item_id,
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                )

        elif self.current_mode == "crop":
            color = "magenta"

            if self.clean_disp_img is not None:
                image_left = self.img_canvas_x
                image_top = self.img_canvas_y
                image_right = (
                    self.img_canvas_x + self.clean_disp_img.width
                )
                image_bottom = (
                    self.img_canvas_y + self.clean_disp_img.height
                )

                crop_x1 = max(
                    image_left,
                    min(image_right, x1),
                )
                crop_y1 = max(
                    image_top,
                    min(image_bottom, y1),
                )
                crop_x2 = max(
                    image_left,
                    min(image_right, x2),
                )
                crop_y2 = max(
                    image_top,
                    min(image_bottom, y2),
                )

                self.panel.create_rectangle(
                    image_left,
                    image_top,
                    image_right,
                    crop_y1,
                    fill="black",
                    stipple="gray50",
                    outline="",
                    tags="overlay",
                )
                self.panel.create_rectangle(
                    image_left,
                    crop_y2,
                    image_right,
                    image_bottom,
                    fill="black",
                    stipple="gray50",
                    outline="",
                    tags="overlay",
                )
                self.panel.create_rectangle(
                    image_left,
                    image_top,
                    crop_x1,
                    crop_y2,
                    fill="black",
                    stipple="gray50",
                    outline="",
                    tags="overlay",
                )
                self.panel.create_rectangle(
                    crop_x2,
                    crop_y1,
                    image_right,
                    crop_y2,
                    fill="black",
                    stipple="gray50",
                    outline="",
                    tags="overlay",
                )
        else:
            color = "cyan"

        self.panel.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            outline=color,
            width=2,
            dash=(4, 4),
            tags="overlay",
        )

        size = self.handle_size / 2

        for x, y in (
            (x1, y1),
            (x2, y1),
            (x1, y2),
            (x2, y2),
        ):
            self.panel.create_rectangle(
                x - size,
                y - size,
                x + size,
                y + size,
                fill=color,
                tags="overlay",
            )

        action_text = (
            "Resize"
            if self.current_mode == "resize"
            else "Crop"
        )
        text_id = self.panel.create_text(
            self.panel.winfo_width() / 2,
            35,
            text=(
                f"Drag corners to {action_text}. "
                "Press ENTER to apply. (ESC to cancel)"
            ),
            fill="black",
            font=("poppins", 11, "bold"),
            tags="overlay",
        )
        text_bbox = self.panel.bbox(text_id)

        self.panel.create_rectangle(
            text_bbox[0] - 5,
            text_bbox[1] - 2,
            text_bbox[2] + 5,
            text_bbox[3] + 2,
            fill="white",
            tags="overlay",
            outline="",
        )
        self.panel.tag_raise(text_id)

    def activate_crop(self):
        """Start crop selection mode."""
        self.current_mode = "crop"

        if not hasattr(self.panel, "image"):
            return

        width = self.clean_disp_img.width
        height = self.clean_disp_img.height

        self.bbox = [
            self.img_canvas_x,
            self.img_canvas_y,
            self.img_canvas_x + width,
            self.img_canvas_y + height,
        ]
        self.panel.config(cursor="crosshair")
        self.display_image(self.output_image)

    def activate_resize(self):
        """Start resize selection mode."""
        self.current_mode = "resize"

        if not hasattr(self.panel, "image"):
            return

        width = self.clean_disp_img.width
        height = self.clean_disp_img.height

        self.bbox = [
            self.img_canvas_x,
            self.img_canvas_y,
            self.img_canvas_x + width,
            self.img_canvas_y + height,
        ]
        self.panel.config(cursor="crosshair")
        self.display_image(self.output_image)

    def start_drag(self, event):
        """Determine which selection handle the user grabbed."""
        if self.current_mode not in ("crop", "resize"):
            return

        x1, y1, x2, y2 = self.bbox
        size = self.handle_size

        if abs(event.x - x1) <= size and abs(event.y - y1) <= size:
            self.active_handle = "TL"
        elif abs(event.x - x2) <= size and abs(event.y - y1) <= size:
            self.active_handle = "TR"
        elif abs(event.x - x1) <= size and abs(event.y - y2) <= size:
            self.active_handle = "BL"
        elif abs(event.x - x2) <= size and abs(event.y - y2) <= size:
            self.active_handle = "BR"
        else:
            self.active_handle = "NEW"
            self.bbox[0] = event.x
            self.bbox[2] = event.x
            self.bbox[1] = event.y
            self.bbox[3] = event.y

    def drag(self, event):
        """Update the crop or resize selection while dragging."""
        if not self.current_mode or not self.active_handle:
            return

        if self.active_handle == "TL":
            self.bbox[0], self.bbox[1] = event.x, event.y
        elif self.active_handle == "TR":
            self.bbox[2], self.bbox[1] = event.x, event.y
        elif self.active_handle == "BL":
            self.bbox[0], self.bbox[3] = event.x, event.y
        elif self.active_handle == "BR":
            self.bbox[2], self.bbox[3] = event.x, event.y
        elif self.active_handle == "NEW":
            self.bbox[2], self.bbox[3] = event.x, event.y

        self.draw_handles()

    def end_drag(self, event):
        """Finish moving a crop or resize handle."""
        self.active_handle = None

    def apply_action(self, event=None):
        """Apply the current crop or resize selection."""
        if self.current_mode not in ("crop", "resize"):
            return

        x1, x2 = sorted([self.bbox[0], self.bbox[2]])
        y1, y2 = sorted([self.bbox[1], self.bbox[3]])

        original_x1 = (x1 - self.img_canvas_x) / self.scale_factor
        original_y1 = (y1 - self.img_canvas_y) / self.scale_factor
        original_x2 = (x2 - self.img_canvas_x) / self.scale_factor
        original_y2 = (y2 - self.img_canvas_y) / self.scale_factor

        width, height = self.img.size

        original_x1 = max(0, int(original_x1))
        original_y1 = max(0, int(original_y1))
        original_x2 = min(width, int(original_x2))
        original_y2 = min(height, int(original_y2))

        temporary_mode = self.current_mode
        self.current_mode = None
        self.panel.config(cursor="")

        if original_x2 - original_x1 < 5:
            self.display_image(self.output_image)
            return

        if original_y2 - original_y1 < 5:
            self.display_image(self.output_image)
            return

        if temporary_mode == "crop":
            self.add_action(
                "crop",
                value=(
                    original_x1,
                    original_y1,
                    original_x2,
                    original_y2,
                ),
            )
        else:
            self.add_action(
                "resize",
                value=(
                    original_x2 - original_x1,
                    original_y2 - original_y1,
                ),
            )

    def cancel_action(self, event=None):
        """Cancel an active crop or resize operation."""
        if self.current_mode in ("crop", "resize"):
            self.current_mode = None
            self.panel.config(cursor="")
            self.display_image(self.output_image)

    # ------------------------------------------------------------------
    # Undo, redo, filters, and sliders
    # ------------------------------------------------------------------

    def update_button_states(self):
        """Enable or disable Undo and Redo based on history position."""
        self.btn_undo.configure(
            state=NORMAL if self.current_step > 0 else DISABLED
        )
        self.btn_redo.configure(
            state=(
                NORMAL
                if self.current_step < len(self.action_history)
                else DISABLED
            )
        )

    def render_state(self):
        """Rebuild the image from the base image and recorded actions."""
        self.is_rendering = True

        temp_image = self.base_image.copy()
        slider_state = {
            "brightness": 1.0,
            "contrast": 1.0,
            "sharpness": 1.0,
            "color": 1.0,
        }

        for action in self.action_history[:self.current_step]:
            if action["action"] == "slider":
                slider_state[action["type"]] = action["value"]
            else:
                temp_image = apply_modifier(temp_image, action)

        self.img = temp_image

        self.brightness_slider.set(slider_state["brightness"])
        self.contrast_slider.set(slider_state["contrast"])
        self.sharpness_slider.set(slider_state["sharpness"])
        self.color_slider.set(slider_state["color"])

        self.is_rendering = False
        self.apply_sliders_to_image()

    def add_action(self, action_name, value=None, slider_type=None):
        """Add an edit to history and rebuild the current image."""
        self.unsaved_changes = True
        self.action_history = self.action_history[:self.current_step]

        entry = {
            "action": action_name,
            "value": value,
        }

        if slider_type:
            entry["type"] = slider_type

        self.action_history.append(entry)
        self.current_step += 1

        # Keep the same maximum history size as the original editor.
        if len(self.action_history) > 50:
            oldest = self.action_history[0]

            if oldest["action"] != "slider":
                self.base_image = apply_modifier(
                    self.base_image,
                    oldest,
                )

            self.action_history.pop(0)
            self.current_step -= 1

        self.render_state()
        self.update_button_states()

    def undo(self):
        """Move one step backward in the edit history."""
        if self.current_step > 0:
            self.unsaved_changes = True
            self.current_step -= 1
            self.render_state()
            self.update_button_states()

    def redo(self):
        """Move one step forward in the edit history."""
        if self.current_step < len(self.action_history):
            self.unsaved_changes = True
            self.current_step += 1
            self.render_state()
            self.update_button_states()

    def on_slider_move(self, value):
        """Preview slider changes without adding every movement to history."""
        if not self.is_rendering:
            self.apply_sliders_to_image()

    def on_slider_press(self, slider_type, slider_widget):
        """Remember the slider value before the drag begins."""
        if not self.is_rendering:
            self.slider_start_vals[slider_type] = slider_widget.get()

    def on_slider_release(self, slider_type, slider_widget):
        """Record one history action after a slider drag finishes."""
        if self.is_rendering:
            return

        start_value = self.slider_start_vals.get(slider_type, 1.0)
        end_value = slider_widget.get()

        if start_value != end_value:
            self.add_action(
                "slider",
                value=end_value,
                slider_type=slider_type,
            )

    def apply_sliders_to_image(self):
        """Apply the current slider values to the displayed image."""
        temp_image = self.img.copy()

        brightness = self.brightness_slider.get()
        if brightness != 1.0:
            temp_image = ImageEnhance.Brightness(
                temp_image
            ).enhance(brightness)

        contrast = self.contrast_slider.get()
        if contrast != 1.0:
            temp_image = ImageEnhance.Contrast(
                temp_image
            ).enhance(contrast)

        sharpness = self.sharpness_slider.get()
        if sharpness != 1.0:
            temp_image = ImageEnhance.Sharpness(
                temp_image
            ).enhance(sharpness)

        color = self.color_slider.get()
        if color != 1.0:
            temp_image = ImageEnhance.Color(
                temp_image
            ).enhance(color)

        self.output_image = temp_image
        self.display_image(self.output_image)

    # ------------------------------------------------------------------
    # Public editing commands
    # ------------------------------------------------------------------

    def rotate(self):
        """Rotate the image 90 degrees clockwise."""
        self.add_action("rotate")

    def flip(self):
        """Flip the image horizontally."""
        self.add_action("flip")

    def blur(self):
        """Apply the blur filter."""
        self.add_action("blur")

    def emboss(self):
        """Apply the emboss filter."""
        self.add_action("emboss")

    def edge_enhance(self):
        """Apply the edge-enhancement filter."""
        self.add_action("edgeEnhance")

    def reset(self):
        """Restore the original image and clear the edit history."""
        self.current_mode = None
        self.panel.config(cursor="")

        self.base_image = self.original_img.copy()
        self.reset_viewport(self.base_image)

        self.action_history = []
        self.current_step = 0
        self.unsaved_changes = False

        self.render_state()
        self.update_button_states()

    def change_image(self):
        """Open a new image and clear the current edit history."""
        image_name = filedialog.askopenfilename(
            initialdir=self.script_dir,
            title="Change Image",
        )

        if image_name:
            self.base_image = Image.open(image_name)
            self.original_img = self.base_image.copy()
            self.reset_viewport(self.base_image)

            self.action_history = []
            self.current_step = 0
            self.unsaved_changes = False

            self.render_state()
            self.update_button_states()

    def save(self):
        """Save the current displayed image as JPEG or PNG."""
        save_path = filedialog.asksaveasfilename(
            initialdir=self.script_dir,
            defaultextension=".jpg",
            filetypes=[
                ("JPEG", "*.jpg"),
                ("PNG", "*.png"),
                ("All Files", "*.*"),
            ],
        )

        if save_path:
            image_to_save = self.output_image

            if (
                save_path.lower().endswith((".jpg", ".jpeg"))
                and image_to_save.mode in ("RGBA", "P")
            ):
                image_to_save = image_to_save.convert("RGB")

            image_to_save.save(save_path)
            self.unsaved_changes = False

    def close(self):
        """Ask whether unsaved edits should be saved before closing."""
        if self.unsaved_changes:
            answer = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes.\n\n"
                "Do you want to save before closing?",
            )

            if answer is True:
                self.save()

                # The user may have canceled the save dialog.
                if self.unsaved_changes:
                    return

            elif answer is None:
                return

        self.mains.destroy()

    def run(self):
        """Start Tkinter's event loop."""
        self.mains.mainloop()
