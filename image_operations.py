"""
Image-processing functions.

This module contains image operations that do not need direct access
to the Tkinter interface.
"""

from PIL import Image, ImageEnhance, ImageFilter


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


def apply_adjustments(image, brightness, contrast, sharpness, color):
    """Apply the four slider adjustments (1.0 means unchanged) to a copy."""
    temp_image = image.copy()

    if brightness != 1.0:
        temp_image = ImageEnhance.Brightness(temp_image).enhance(brightness)

    if contrast != 1.0:
        temp_image = ImageEnhance.Contrast(temp_image).enhance(contrast)

    if sharpness != 1.0:
        temp_image = ImageEnhance.Sharpness(temp_image).enhance(sharpness)

    if color != 1.0:
        temp_image = ImageEnhance.Color(temp_image).enhance(color)

    return temp_image
