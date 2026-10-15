"""Crop and resize selection box: state, dragging, drawing and applying."""

from PIL import Image, ImageTk


class SelectionTool:
    """
    Handles the interactive crop / resize rectangle.

    `editor` provides the canvas (editor.canvas), the current image
    (editor.img / editor.output_image) and add_action() to record the edit.
    """

    def __init__(self, editor):
        self.editor = editor

        self.current_mode = None
        self.bbox = [0, 0, 0, 0]
        self.active_handle = None
        self.handle_size = 12

    # ------------------------------------------------------------------
    # Entering / leaving a mode
    # ------------------------------------------------------------------

    def activate_crop(self):
        """Start crop selection mode."""
        self._activate("crop")

    def activate_resize(self):
        """Start resize selection mode."""
        self._activate("resize")

    def _activate(self, mode):
        canvas = self.editor.canvas
        vp = canvas.viewport

        self.current_mode = mode

        if not hasattr(canvas.panel, "image"):
            return

        width = canvas.clean_disp_img.width
        height = canvas.clean_disp_img.height

        self.bbox = [
            vp.img_canvas_x,
            vp.img_canvas_y,
            vp.img_canvas_x + width,
            vp.img_canvas_y + height,
        ]
        canvas.panel.config(cursor="crosshair")
        canvas.display_image(self.editor.output_image)

    def cancel(self, event=None):
        """Cancel an active crop or resize operation."""
        if self.current_mode in ("crop", "resize"):
            canvas = self.editor.canvas

            self.current_mode = None
            canvas.panel.config(cursor="")
            canvas.display_image(self.editor.output_image)

    # ------------------------------------------------------------------
    # Dragging
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Applying
    # ------------------------------------------------------------------

    def apply(self, event=None):
        """Apply the current crop or resize selection."""
        if self.current_mode not in ("crop", "resize"):
            return

        editor = self.editor
        canvas = editor.canvas
        vp = canvas.viewport

        x1, x2 = sorted([self.bbox[0], self.bbox[2]])
        y1, y2 = sorted([self.bbox[1], self.bbox[3]])

        original_x1 = (x1 - vp.img_canvas_x) / vp.scale_factor
        original_y1 = (y1 - vp.img_canvas_y) / vp.scale_factor
        original_x2 = (x2 - vp.img_canvas_x) / vp.scale_factor
        original_y2 = (y2 - vp.img_canvas_y) / vp.scale_factor

        width, height = editor.img.size

        original_x1 = max(0, int(original_x1))
        original_y1 = max(0, int(original_y1))
        original_x2 = min(width, int(original_x2))
        original_y2 = min(height, int(original_y2))

        temporary_mode = self.current_mode
        self.current_mode = None
        canvas.panel.config(cursor="")

        if original_x2 - original_x1 < 5:
            canvas.display_image(editor.output_image)
            return

        if original_y2 - original_y1 < 5:
            canvas.display_image(editor.output_image)
            return

        if temporary_mode == "crop":
            editor.add_action(
                "crop",
                value=(
                    original_x1,
                    original_y1,
                    original_x2,
                    original_y2,
                ),
            )
        else:
            editor.add_action(
                "resize",
                value=(
                    original_x2 - original_x1,
                    original_y2 - original_y1,
                ),
            )

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw_handles(self):
        """Draw selection handles and the crop/resize preview."""
        canvas = self.editor.canvas
        panel = canvas.panel
        vp = canvas.viewport

        panel.delete("overlay")

        x1, x2 = sorted([self.bbox[0], self.bbox[2]])
        y1, y2 = sorted([self.bbox[1], self.bbox[3]])

        if self.current_mode == "resize":
            color = "cyan"
            width = int(max(1, x2 - x1))
            height = int(max(1, y2 - y1))

            if canvas.clean_disp_img is not None and canvas.image_item_id:
                preview = canvas.clean_disp_img.resize(
                    (width, height),
                    Image.NEAREST,
                )
                canvas.preview_tk = ImageTk.PhotoImage(preview)
                panel.itemconfig(
                    canvas.image_item_id,
                    image=canvas.preview_tk,
                )
                panel.coords(
                    canvas.image_item_id,
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                )

        elif self.current_mode == "crop":
            color = "magenta"

            if canvas.clean_disp_img is not None:
                image_left = vp.img_canvas_x
                image_top = vp.img_canvas_y
                image_right = (
                    vp.img_canvas_x + canvas.clean_disp_img.width
                )
                image_bottom = (
                    vp.img_canvas_y + canvas.clean_disp_img.height
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

                panel.create_rectangle(
                    image_left,
                    image_top,
                    image_right,
                    crop_y1,
                    fill="black",
                    stipple="gray50",
                    outline="",
                    tags="overlay",
                )
                panel.create_rectangle(
                    image_left,
                    crop_y2,
                    image_right,
                    image_bottom,
                    fill="black",
                    stipple="gray50",
                    outline="",
                    tags="overlay",
                )
                panel.create_rectangle(
                    image_left,
                    image_top,
                    crop_x1,
                    crop_y2,
                    fill="black",
                    stipple="gray50",
                    outline="",
                    tags="overlay",
                )
                panel.create_rectangle(
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

        panel.create_rectangle(
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
            panel.create_rectangle(
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
        text_id = panel.create_text(
            panel.winfo_width() / 2,
            35,
            text=(
                f"Drag corners to {action_text}. "
                "Press ENTER to apply. (ESC to cancel)"
            ),
            fill="black",
            font=("poppins", 11, "bold"),
            tags="overlay",
        )
        text_bbox = panel.bbox(text_id)

        panel.create_rectangle(
            text_bbox[0] - 5,
            text_bbox[1] - 2,
            text_bbox[2] + 5,
            text_bbox[3] + 2,
            fill="white",
            tags="overlay",
            outline="",
        )
        panel.tag_raise(text_id)
