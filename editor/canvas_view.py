"""The image canvas: drawing, rulers, zoom, pan and cursor tracking."""

from tkinter import Canvas, CENTER

from PIL import Image, ImageTk, ImageDraw

from image_operations import get_resample_filter
from .viewport import Viewport


class ImageCanvas:
    """
    Draws the image on a Tkinter canvas and handles zoom / pan events.

    `editor` provides the current images (img, output_image), the
    crop/resize selection (editor.selection) and the status bar.
    """

    def __init__(self, parent, editor):
        self.editor = editor
        self.viewport = Viewport()

        self.panel = Canvas(
            parent,
            bg="#323946",
            highlightthickness=0,
        )
        self.panel.grid(row=0, column=0, sticky="nsew")

        # Display cache objects used by Tkinter.
        self.checkerboard_bg = None
        self.checkerboard_size = None
        self.clean_disp_img = None
        self.image_item_id = None
        self.preview_tk = None
        self.dispimage = None

    # ------------------------------------------------------------------
    # Event bindings
    # ------------------------------------------------------------------

    def bind_events(self, selection):
        """Connect mouse events to the canvas and the selection tool."""
        self.panel.bind("<ButtonPress-1>", selection.start_drag)
        self.panel.bind("<B1-Motion>", selection.drag)
        self.panel.bind("<ButtonRelease-1>", selection.end_drag)
        self.panel.bind("<Motion>", self.track_mouse)
        self.panel.bind("<Configure>", self.resize_canvas)

        self.panel.bind("<MouseWheel>", self.zoom)
        self.panel.bind("<Button-4>", self.zoom)
        self.panel.bind("<Button-5>", self.zoom)

        self.panel.bind("<ButtonPress-2>", self.start_pan)
        self.panel.bind("<B2-Motion>", self.do_pan)
        self.panel.bind("<ButtonPress-3>", self.start_pan)
        self.panel.bind("<B3-Motion>", self.do_pan)

    # ------------------------------------------------------------------
    # Viewport and display
    # ------------------------------------------------------------------

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
        canvas_width = self.panel.winfo_width()
        canvas_height = self.panel.winfo_height()

        canvas_width = canvas_width if canvas_width > 1 else 600
        canvas_height = canvas_height if canvas_height > 1 else 600

        self.viewport.reset(image.size, (canvas_width, canvas_height))

    def display_image(self, image_to_display):
        """Render the image, checkerboard, rulers, and active overlays."""
        vp = self.viewport

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
            int(original_width * vp.zoom_level),
        )
        display_height = max(
            1,
            int(original_height * vp.zoom_level),
        )

        display_image = image_to_display.resize(
            (display_width, display_height),
            get_resample_filter(),
        )

        self.clean_disp_img = display_image.copy()
        self.dispimage = ImageTk.PhotoImage(display_image)
        vp.scale_factor = vp.zoom_level

        vp.img_canvas_x = vp.pan_x - display_width / 2
        vp.img_canvas_y = vp.pan_y - display_height / 2

        self.panel.delete("all")
        self.panel.create_image(
            canvas_width / 2,
            canvas_height / 2,
            image=self.checkerboard_bg,
            anchor=CENTER,
        )
        self.image_item_id = self.panel.create_image(
            vp.pan_x,
            vp.pan_y,
            image=self.dispimage,
            anchor=CENTER,
        )
        self.panel.image = self.dispimage

        self.draw_rulers(original_width, original_height)

        if self.editor.selection.current_mode in ("crop", "resize"):
            self.editor.selection.draw_handles()

    def resize_canvas(self, event):
        """Keep the image centered and preserve active selection coordinates."""
        vp = self.viewport
        editor = self.editor
        selection = editor.selection

        if event.width <= 1 or event.height <= 1:
            return

        new_size = (event.width, event.height)

        if vp.last_canvas_size == new_size:
            return

        old_zoom = vp.zoom_level
        old_image_left = (
            vp.pan_x - editor.img.width * old_zoom / 2
        )
        old_image_top = (
            vp.pan_y - editor.img.height * old_zoom / 2
        )
        old_bbox = (
            tuple(selection.bbox)
            if selection.current_mode in ("crop", "resize")
            else None
        )

        if vp.last_canvas_size is None:
            vp.resize_zoom = 1.0

        vp.fit_zoom_level = vp.calculate_fit_zoom(
            editor.img.size,
            new_size,
        )
        vp.zoom_level = vp.fit_zoom_level * vp.resize_zoom
        vp.pan_x = event.width / 2
        vp.pan_y = event.height / 2

        if old_bbox is not None:
            new_image_left = (
                vp.pan_x - editor.img.width * vp.zoom_level / 2
            )
            new_image_top = (
                vp.pan_y - editor.img.height * vp.zoom_level / 2
            )

            selection.bbox[0] = (
                new_image_left
                + (old_bbox[0] - old_image_left)
                / old_zoom
                * vp.zoom_level
            )
            selection.bbox[2] = (
                new_image_left
                + (old_bbox[2] - old_image_left)
                / old_zoom
                * vp.zoom_level
            )
            selection.bbox[1] = (
                new_image_top
                + (old_bbox[1] - old_image_top)
                / old_zoom
                * vp.zoom_level
            )
            selection.bbox[3] = (
                new_image_top
                + (old_bbox[3] - old_image_top)
                / old_zoom
                * vp.zoom_level
            )

        vp.last_canvas_size = new_size
        self.display_image(editor.output_image)

    def draw_rulers(self, image_width, image_height):
        """Draw rulers and update the image dimensions status label."""
        vp = self.viewport

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
        if vp.zoom_level < 0.3:
            step = 500
        elif vp.zoom_level < 0.7:
            step = 200
        elif vp.zoom_level > 2.0:
            step = 50
        elif vp.zoom_level > 5.0:
            step = 10

        for x_value in range(0, image_width + 1, step):
            canvas_x = (
                vp.img_canvas_x
                + x_value * vp.scale_factor
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
                vp.img_canvas_y
                + y_value * vp.scale_factor
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

        self.editor.status_bar.show_dimensions(
            image_width,
            image_height,
            vp.zoom_level,
        )

    # ------------------------------------------------------------------
    # Mouse interaction
    # ------------------------------------------------------------------

    def track_mouse(self, event):
        """Show the image pixel coordinate under the mouse cursor."""
        vp = self.viewport

        if self.clean_disp_img is None:
            return

        image_x = int(
            (event.x - vp.img_canvas_x) / vp.scale_factor
        )
        image_y = int(
            (event.y - vp.img_canvas_y) / vp.scale_factor
        )

        width, height = self.editor.img.size

        if 0 <= image_x < width and 0 <= image_y < height:
            self.editor.status_bar.show_cursor(
                f"Cursor: X: {image_x}, Y: {image_y} px"
            )
        else:
            self.editor.status_bar.show_cursor("Cursor: Outside Image")

    def zoom(self, event):
        """Zoom around the current mouse position."""
        vp = self.viewport

        if self.editor.selection.current_mode in ("crop", "resize"):
            self.editor.selection.cancel()

        old_zoom = vp.zoom_level

        if event.num == 4 or getattr(event, "delta", 0) > 0:
            vp.zoom_level *= 1.15
        elif event.num == 5 or getattr(event, "delta", 0) < 0:
            vp.zoom_level /= 1.15

        vp.zoom_level = max(0.01, min(vp.zoom_level, 50.0))
        vp.resize_zoom = vp.zoom_level / vp.fit_zoom_level

        scale_ratio = vp.zoom_level / old_zoom
        vp.pan_x = event.x - (event.x - vp.pan_x) * scale_ratio
        vp.pan_y = event.y - (event.y - vp.pan_y) * scale_ratio

        self.display_image(self.editor.output_image)

    def start_pan(self, event):
        """Record the starting point for a middle/right-button pan."""
        self.viewport.last_pan_x = event.x
        self.viewport.last_pan_y = event.y

    def do_pan(self, event):
        """Move the image while panning."""
        vp = self.viewport

        vp.pan_x += event.x - vp.last_pan_x
        vp.pan_y += event.y - vp.last_pan_y
        vp.last_pan_x = event.x
        vp.last_pan_y = event.y

        self.display_image(self.editor.output_image)
