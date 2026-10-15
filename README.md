# Quality_Photo_Editor
Uniji Software Quality Course program that is an incomplete app editor that is used as training material for semester 4B of SE class


## Project structure

```
main.py                  entry point (python main.py)
image_editor.py          ImageEditor: owns the images and wires everything together
image_operations.py      pure Pillow functions (modifiers, slider adjustments)
editor/
  window.py              MainWindow: Tk root, icon, main frames
  status_bar.py          StatusBar: size/zoom, cursor and hint labels
  control_panel.py       ControlPanel: sliders, edit buttons, toolbar buttons
  canvas_view.py         ImageCanvas: drawing, rulers, zoom, pan, cursor tracking
  viewport.py            Viewport: zoom/pan state
  selection_tool.py      SelectionTool: crop/resize box
  edit_history.py        EditHistory: undo/redo list
```
