"""
Object-oriented Tkinter image editor.

ImageEditor is the coordinator: it owns the images and wires together the
components in the `editor` package (window, canvas, selection tool,
history, controls). The visible interface and editing behavior are
unchanged from the single-file version.
"""

import os
from tkinter import filedialog, messagebox

from PIL import Image

from image_operations import apply_modifier, apply_adjustments
from editor.window import MainWindow
from editor.status_bar import StatusBar
from editor.canvas_view import ImageCanvas
from editor.selection_tool import SelectionTool
from editor.edit_history import EditHistory
from editor.control_panel import ControlPanel


class ImageEditor:
    """Main application class: image state plus the editing commands."""

    def __init__(self):
        # Directory containing this Python file and optional image assets.
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        # Render / undo state.
        self.history = EditHistory()
        self.is_rendering = False
        self.slider_start_vals = {}
        self.unsaved_changes = False

        # Create the root window and initialize the image.
        self.window = MainWindow(self.script_dir, on_close=self.close)
        self.mains = self.window.root
        self.load_startup_image()

        # Build the components. Each one reaches the others through `self`.
        self.selection = SelectionTool(self)
        self.canvas = ImageCanvas(self.window.editor_frame, self)
        self.status_bar = StatusBar(self.window.status_frame)
        self.create_bindings()
        self.controls = ControlPanel(
            self.window.controls_frame,
            self.window.toolbar,
            self,
        )

        # Display the initial image after all widgets exist.
        self.canvas.display_image(self.img)
        self.update_button_states()

    # ------------------------------------------------------------------
    # Startup
    # ------------------------------------------------------------------

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

    def create_bindings(self):
        """Connect mouse, keyboard, and window events to their handlers."""
        self.canvas.bind_events(self.selection)

        self.mains.bind("<Return>", self.selection.apply)
        self.mains.bind("<Escape>", self.selection.cancel)

    # ------------------------------------------------------------------
    # Undo, redo, and rendering
    # ------------------------------------------------------------------

    def update_button_states(self):
        """Enable or disable Undo and Redo based on history position."""
        self.controls.update_undo_redo_state(
            self.history.can_undo(),
            self.history.can_redo(),
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

        for action in self.history.active_actions():
            if action["action"] == "slider":
                slider_state[action["type"]] = action["value"]
            else:
                temp_image = apply_modifier(temp_image, action)

        self.img = temp_image

        self.controls.set_slider_values(slider_state)

        self.is_rendering = False
        self.apply_sliders_to_image()

    def add_action(self, action_name, value=None, slider_type=None):
        """Add an edit to history and rebuild the current image."""
        self.unsaved_changes = True

        entry = {
            "action": action_name,
            "value": value,
        }

        if slider_type:
            entry["type"] = slider_type

        # Keep the same maximum history size as the original editor.
        dropped = self.history.push(entry)

        if dropped is not None and dropped["action"] != "slider":
            self.base_image = apply_modifier(self.base_image, dropped)

        self.render_state()
        self.update_button_states()

    def undo(self):
        """Move one step backward in the edit history."""
        if self.history.can_undo():
            self.unsaved_changes = True
            self.history.undo()
            self.render_state()
            self.update_button_states()

    def redo(self):
        """Move one step forward in the edit history."""
        if self.history.can_redo():
            self.unsaved_changes = True
            self.history.redo()
            self.render_state()
            self.update_button_states()

    # ------------------------------------------------------------------
    # Sliders
    # ------------------------------------------------------------------

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
        self.output_image = apply_adjustments(
            self.img,
            *self.controls.get_slider_values(),
        )
        self.canvas.display_image(self.output_image)

    # ------------------------------------------------------------------
    # Editing commands
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
        self.selection.current_mode = None
        self.canvas.panel.config(cursor="")

        self.base_image = self.original_img.copy()
        self.canvas.reset_viewport(self.base_image)

        self.history.clear()
        self.unsaved_changes = False

        self.render_state()
        self.update_button_states()

    # ------------------------------------------------------------------
    # Files and application lifecycle
    # ------------------------------------------------------------------

    def change_image(self):
        """Open a new image and clear the current edit history."""
        image_name = filedialog.askopenfilename(
            initialdir=self.script_dir,
            title="Change Image",
        )

        if image_name:
            self.base_image = Image.open(image_name)
            self.original_img = self.base_image.copy()
            self.canvas.reset_viewport(self.base_image)

            self.history.clear()
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
