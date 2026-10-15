"""Sliders and buttons: the right-hand control panel and the top toolbar."""

from tkinter import Scale, Button, HORIZONTAL, NORMAL, DISABLED


class ControlPanel:
    """
    Builds every slider and button.

    `editor` supplies the callbacks the widgets trigger (rotate, save,
    on_slider_move, ...), so this class only deals with widgets.
    """

    def __init__(self, controls_frame, toolbar, editor):
        self.controls_frame = controls_frame
        self.toolbar = toolbar
        self.editor = editor

        self._create_sliders()
        self._create_edit_buttons()
        self._create_toolbar_buttons()

    # ------------------------------------------------------------------
    # Sliders
    # ------------------------------------------------------------------

    def _create_sliders(self):
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

    def create_slider(self, label, row, slider_type):
        """Create one adjustment slider with its mouse event handlers."""
        editor = self.editor

        slider = Scale(
            self.controls_frame,
            label=label,
            from_=0,
            to=2,
            orient=HORIZONTAL,
            length=120,
            resolution=0.1,
            command=editor.on_slider_move,
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
            lambda event: editor.on_slider_press(
                slider_type,
                slider,
            ),
        )
        slider.bind(
            "<ButtonRelease-1>",
            lambda event: editor.on_slider_release(
                slider_type,
                slider,
            ),
        )
        return slider

    def set_slider_values(self, values):
        """Set all four sliders from a dict keyed by slider type."""
        self.brightness_slider.set(values["brightness"])
        self.contrast_slider.set(values["contrast"])
        self.sharpness_slider.set(values["sharpness"])
        self.color_slider.set(values["color"])

    def get_slider_values(self):
        """Return the current (brightness, contrast, sharpness, color)."""
        return (
            self.brightness_slider.get(),
            self.contrast_slider.get(),
            self.sharpness_slider.get(),
            self.color_slider.get(),
        )

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------

    def _create_edit_buttons(self):
        editor = self.editor

        self.btn_rotate = self.create_control_button(
            "Rotate",
            editor.rotate,
            4,
            0,
        )
        self.btn_change_image = self.create_control_button(
            "Change Image",
            editor.change_image,
            4,
            1,
            activebackground="ORANGE",
        )
        self.btn_flip = self.create_control_button(
            "Flip",
            editor.flip,
            5,
            0,
        )
        self.btn_resize = self.create_control_button(
            "Resize",
            editor.selection.activate_resize,
            5,
            1,
        )
        self.btn_crop = self.create_control_button(
            "Crop",
            editor.selection.activate_crop,
            6,
            0,
        )
        self.btn_blur = self.create_control_button(
            "Blur",
            editor.blur,
            6,
            1,
        )
        self.btn_emboss = self.create_control_button(
            "Emboss",
            editor.emboss,
            7,
            0,
        )
        self.btn_edge_enhance = self.create_control_button(
            "EdgeEnhance",
            editor.edge_enhance,
            7,
            1,
        )

        self.btn_save = Button(
            self.controls_frame,
            text="Save",
            width=16,
            command=editor.save,
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

    def _create_toolbar_buttons(self):
        editor = self.editor

        self.reset_button = self.create_toolbar_button(
            "Reset",
            editor.reset,
            0,
        )
        self.btn_close = self.create_toolbar_button(
            "Close",
            editor.close,
            1,
        )
        self.btn_undo = self.create_toolbar_button(
            "Undo",
            editor.undo,
            2,
        )
        self.btn_redo = self.create_toolbar_button(
            "Redo",
            editor.redo,
            3,
        )

    def create_toolbar_button(self, text, command, column):
        """Create one of the buttons in the top toolbar."""
        button = Button(
            self.toolbar,
            text=text,
            command=command,
            bg="black",
            activebackground="ORANGE",
        )
        button.configure(
            font=("poppins", 10, "bold"),
            foreground="white",
        )
        button.grid(row=0, column=column, padx=3)
        return button

    def update_undo_redo_state(self, can_undo, can_redo):
        """Enable or disable Undo and Redo."""
        self.btn_undo.configure(state=NORMAL if can_undo else DISABLED)
        self.btn_redo.configure(state=NORMAL if can_redo else DISABLED)
