"""
Image-processing functions.

This module contains image operations that do not need direct access
to the Tkinter interface.
"""

from PIL import Image, ImageFilter


def get_resample_filter():
    """Return a Pillow resize filter compatible with multiple Pillow versions."""
    try:
        return Image.Resampling.LANCZOS
    except AttributeError:
        return Image.LANCZOS


def apply_modifier(image, modifier):
    """
    Apply one recorded editing action to an image.

    Modifiers are dictionaries such as:
        {"action": "rotate"}
        {"action": "crop", "value": (x1, y1, x2, y2)}
        {"action": "slider", "type": "brightness", "value": 1.5}
    """
    action = modifier["action"]
    value = modifier.get("value")

    if action == "rotate":
        return image.rotate(90, expand=True)

    if action == "flip":
        return image.transpose(Image.FLIP_LEFT_RIGHT)

    if action == "blur":
        return image.filter(ImageFilter.BLUR)

    if action == "emboss":
        return image.filter(ImageFilter.EMBOSS)

    if action == "edgeEnhance":
        return image.filter(ImageFilter.EDGE_ENHANCE)

    if action == "crop":
        return image.crop(value)

    if action == "resize":
        return image.resize(value, get_resample_filter())

    return image
