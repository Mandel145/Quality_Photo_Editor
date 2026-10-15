"""Zoom and pan state for the image canvas."""


class Viewport:
    """Holds how the image is scaled and positioned inside the canvas."""

    def __init__(self):
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

    def reset(self, image_size, canvas_size):
        """Fit a newly loaded or reset image to the given canvas size."""
        canvas_width, canvas_height = canvas_size

        self.fit_zoom_level = self.calculate_fit_zoom(
            image_size,
            (canvas_width, canvas_height),
        )
        self.zoom_level = self.fit_zoom_level
        self.resize_zoom = 1.0
        self.pan_x = canvas_width / 2
        self.pan_y = canvas_height / 2
        self.last_canvas_size = (canvas_width, canvas_height)
