"""Status bar shown under the canvas."""

from tkinter import Label


class StatusBar:
    """Image size / zoom, cursor position, and the usage hint."""

    def __init__(self, parent):
        self.dim_label = Label(
            parent,
            text="",
            bg="#323946",
            fg="white",
            font=("poppins", 10, "bold"),
        )
        self.dim_label.grid(row=0, column=0, sticky="w", padx=(0, 16))

        self.coord_label = Label(
            parent,
            text="Cursor: X: 0, Y: 0 px",
            bg="#323946",
            fg="#00ffcc",
            font=("poppins", 10, "bold"),
        )
        self.coord_label.grid(row=0, column=1, sticky="w")

        Label(
            parent,
            text="Mouse Wheel: Zoom  |  Right/Middle Drag: Pan",
            bg="#323946",
            fg="gray",
            font=("poppins", 9, "italic"),
        ).grid(row=0, column=2, sticky="e")

    def show_dimensions(self, image_width, image_height, zoom_level):
        self.dim_label.config(
            text=(
                f"Image Size: {image_width} x {image_height} px"
                f"  |  Zoom: {int(zoom_level * 100)}%"
            )
        )

    def show_cursor(self, text):
        self.coord_label.config(text=text)
