from tkinter import *
from tkinter import ttk, filedialog
from PIL import ImageTk, Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw
import os

current_mode = None
bbox = [0, 0, 0, 0]
active_handle = None
handle_size = 12
img_canvas_x = 0
img_canvas_y = 0
scale_factor = 1.0
checkerboard_bg = None

def generate_checkerboard():
    """Generates a full 600x600 checkerboard canvas background."""
    base = Image.new('RGB', (40, 40), color='#ffffff')
    draw = ImageDraw.Draw(base)
    draw.rectangle([20, 0, 39, 19], fill='#cccccc')
    draw.rectangle([0, 20, 19, 39], fill='#cccccc')
    
    cb = Image.new('RGB', (600, 600))
    for y in range(0, 600, 40):
        for x in range(0, 600, 40):
            cb.paste(base, (x, y))
    return ImageTk.PhotoImage(cb)

def displayimage(img_to_display):
    global dispimage, img_canvas_x, img_canvas_y, scale_factor, checkerboard_bg
    
    # 1. Generate full 600x600 checkerboard background once
    if checkerboard_bg is None:
        checkerboard_bg = generate_checkerboard()

    ow, oh = img_to_display.size
    
    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        resample = Image.LANCZOS
        
    if ow > 600 or oh > 600:
        disp_img = ImageOps.contain(img_to_display, (600, 600), resample)
    else:
        disp_img = img_to_display.copy()
        
    dispimage = ImageTk.PhotoImage(disp_img)
    dw, dh = disp_img.size
    
    scale_factor = dw / ow if ow > 0 else 1
    
    img_canvas_x = 300 - dw / 2
    img_canvas_y = 300 - dh / 2

    panel.delete("all")
    
    # 2. Draw full canvas checkerboard first, then overlay the image in the center
    panel.create_image(300, 300, image=checkerboard_bg, anchor=CENTER)
    panel.create_image(300, 300, image=dispimage, anchor=CENTER)
    panel.image = dispimage 
    
    if current_mode in ['crop', 'resize']:
        draw_handles()

def draw_handles():
    panel.delete("overlay")
    x1, y1, x2, y2 = bbox
    
    # Bounding Box
    color = 'cyan' if current_mode == 'resize' else 'magenta'
    panel.create_rectangle(x1, y1, x2, y2, outline=color, width=2, dash=(4,4), tags="overlay")
    
    # Corner Nodes
    s = handle_size / 2
    panel.create_rectangle(x1-s, y1-s, x1+s, y1+s, fill=color, tags="overlay")
    panel.create_rectangle(x2-s, y1-s, x2+s, y1+s, fill=color, tags="overlay")
    panel.create_rectangle(x1-s, y2-s, x1+s, y2+s, fill=color, tags="overlay")
    panel.create_rectangle(x2-s, y2-s, x2+s, y2+s, fill=color, tags="overlay")
    
    # Instruction Text
    action_text = "Resize" if current_mode == 'resize' else "Crop"
    txt_id = panel.create_text(panel.winfo_reqwidth() // 2, 20, text=f"Drag corners to {action_text}. Press ENTER to apply.",
                               fill="black", font=("poppins", 12, "bold"), tags="overlay")
    # Text background for readability
    txt_bbox = panel.bbox(txt_id)
    panel.create_rectangle(txt_bbox[0]-5, txt_bbox[1]-2, txt_bbox[2]+5, txt_bbox[3]+2, 
                           fill="white", tags="overlay", outline="")
    panel.tag_raise(txt_id)

def activate_crop():
    global current_mode, bbox
    current_mode = 'crop'
    if not hasattr(panel, 'image'): return
    dw = dispimage.width()
    dh = dispimage.height()
    pad_x, pad_y = dw * 0.1, dh * 0.1
    bbox = [img_canvas_x + pad_x, img_canvas_y + pad_y, 
            img_canvas_x + dw - pad_x, img_canvas_y + dh - pad_y]
    panel.config(cursor="crosshair")
    displayimage(outputImage)

def activate_resize():
    global current_mode, bbox
    current_mode = 'resize'
    if not hasattr(panel, 'image'): return
    
    # Start the handles at the full 600x600 canvas limits
    bbox = [0, 0, 600, 600]
    panel.config(cursor="crosshair")
    displayimage(outputImage)

def start_drag(event):
    global active_handle
    if current_mode not in ['crop', 'resize']: return
    
    x, y = event.x, event.y
    x1, y1, x2, y2 = bbox
    s = handle_size
    
    if abs(x - x1) <= s and abs(y - y1) <= s: active_handle = 'TL'
    elif abs(x - x2) <= s and abs(y - y1) <= s: active_handle = 'TR'
    elif abs(x - x1) <= s and abs(y - y2) <= s: active_handle = 'BL'
    elif abs(x - x2) <= s and abs(y - y2) <= s: active_handle = 'BR'
    else:
        active_handle = 'NEW'
        bbox[0] = bbox[2] = x
        bbox[1] = bbox[3] = y

def drag(event):
    if not current_mode or not active_handle: return
    dw = dispimage.width()
    dh = dispimage.height()
    
    if current_mode == 'resize':
        # Allow dragging across the full 600x600 canvas area to enlarge/upsize
        min_x, max_x = 0, 600
        min_y, max_y = 0, 600
    else:
        # Keep crop handles bounded to the actual image display bounds
        min_x, max_x = img_canvas_x, img_canvas_x + dw
        min_y, max_y = img_canvas_y, img_canvas_y + dh
    
    x = max(min_x, min(max_x, event.x))
    y = max(min_y, min(max_y, event.y))
    
    if active_handle == 'TL': bbox[0], bbox[1] = x, y
    elif active_handle == 'TR': bbox[2], bbox[1] = x, y
    elif active_handle == 'BL': bbox[0], bbox[3] = x, y
    elif active_handle == 'BR': bbox[2], bbox[3] = x, y
    elif active_handle == 'NEW': bbox[2], bbox[3] = x, y
        
    draw_handles()

def end_drag(event):
    global active_handle
    active_handle = None

def apply_action(event=None):
    global current_mode, img, outputImage
    if current_mode not in ['crop', 'resize']: return
    
    x1, x2 = sorted([bbox[0], bbox[2]])
    y1, y2 = sorted([bbox[1], bbox[3]])
    
    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        resample = Image.LANCZOS
        
    if current_mode == 'crop':
        # Translate canvas coordinates to original image pixels
        ox1 = (x1 - img_canvas_x) / scale_factor
        oy1 = (y1 - img_canvas_y) / scale_factor
        ox2 = (x2 - img_canvas_x) / scale_factor
        oy2 = (y2 - img_canvas_y) / scale_factor
        
        ow, oh = img.size
        ox1, oy1 = max(0, int(ox1)), max(0, int(oy1))
        ox2, oy2 = min(ow, int(ox2)), min(oh, int(oy2))
        
        if ox2 - ox1 > 5 and oy2 - oy1 > 5:
            img = img.crop((ox1, oy1, ox2, oy2))
            
    elif current_mode == 'resize':
        # Convert selected canvas bounding box dimensions into real image pixel dimensions
        target_w = max(10, int((x2 - x1) / scale_factor))
        target_h = max(10, int((y2 - y1) / scale_factor))
        img = img.resize((target_w, target_h), resample)
        
    current_mode = None
    panel.config(cursor="")
    apply_sliders()

def apply_sliders(*args):
    global outputImage
    temp_img = img.copy()
    
    b_val = brightnessSlider.get()
    if b_val != 1.0: temp_img = ImageEnhance.Brightness(temp_img).enhance(b_val)
        
    c_val = contrastSlider.get()
    if c_val != 1.0: temp_img = ImageEnhance.Contrast(temp_img).enhance(c_val)
        
    s_val = sharpnessSlider.get()
    if s_val != 1.0: temp_img = ImageEnhance.Sharpness(temp_img).enhance(s_val)
        
    col_val = colorSlider.get()
    if col_val != 1.0: temp_img = ImageEnhance.Color(temp_img).enhance(col_val)
        
    outputImage = temp_img
    displayimage(outputImage)

def rotate():
    global img
    img = img.rotate(90, expand=True)
    apply_sliders()

def flip():
    global img
    img = img.transpose((Image.FLIP_LEFT_RIGHT))
    apply_sliders()

def blurr():
    global img
    img = img.filter(ImageFilter.BLUR)
    apply_sliders()

def emboss():
    global img
    img = img.filter(ImageFilter.EMBOSS)
    apply_sliders()

def edgeEnhance():
    global img
    img = img.filter(ImageFilter.EDGE_ENHANCE)
    apply_sliders()

def reset():
    global img, original_img, current_mode
    current_mode = None
    panel.config(cursor="")
    img = original_img.copy()
    
    brightnessSlider.set(1)
    contrastSlider.set(1)
    sharpnessSlider.set(1)
    colorSlider.set(1)
    apply_sliders()

def ChangeImg():
    global img, original_img
    imgname = filedialog.askopenfilename(title="Change Image")
    if imgname:
        img = Image.open(imgname)
        original_img = img.copy()
        
        brightnessSlider.set(1)
        contrastSlider.set(1)
        sharpnessSlider.set(1)
        colorSlider.set(1)
        apply_sliders()

def save():
    global outputImage
    save_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png"), ("All Files", "*.*")])
    if save_path:
        img_to_save = outputImage
        if save_path.lower().endswith((".jpg", ".jpeg")) and img_to_save.mode in ("RGBA", "P"):
            img_to_save = img_to_save.convert("RGB")
        img_to_save.save(save_path)

def close():
    mains.destroy()

mains = Tk()
space = (" ") * 215
screen_width = mains.winfo_screenwidth()
screen_height = mains.winfo_screenheight()

mains.geometry(f"{screen_width}x{screen_height}")
mains.title(f"{space}Image Editor")
mains.configure(bg='#323946')

try:
    img = Image.open("logo.png")
except FileNotFoundError:
    img = Image.new('RGB', (600, 600), color='#323946')

original_img = img.copy()
outputImage = img.copy()

panel = Canvas(mains, width=600, height=600, bg='#323946', highlightthickness=0)
panel.grid(row=0, column=0, rowspan=12, padx=50, pady=50)

panel.bind("<ButtonPress-1>", start_drag)
panel.bind("<B1-Motion>", drag)
panel.bind("<ButtonRelease-1>", end_drag)

# Bind the Enter key to apply edits
mains.bind("<Return>", apply_action)  

displayimage(img)

brightnessSlider = Scale(mains, label="Brightness", from_=0, to=2, orient=HORIZONTAL, length=200,
                         resolution=0.1, command=apply_sliders, bg="#1f242d")
brightnessSlider.set(1)
brightnessSlider.configure(font=('poppins',11,'bold'),foreground='white')
brightnessSlider.place(x=1070,y=15)

contrastSlider = Scale(mains, label="Contrast", from_=0, to=2, orient=HORIZONTAL, length=200,
                       command=apply_sliders, resolution=0.1, bg="#1f242d")
contrastSlider.set(1)
contrastSlider.configure(font=('poppins',11,'bold'),foreground='white')
contrastSlider.place(x=1070,y=90)

sharpnessSlider = Scale(mains, label="Sharpness", from_=0, to=2, orient=HORIZONTAL, length=200,
                        command=apply_sliders, resolution=0.1, bg="#1f242d")
sharpnessSlider.set(1)
sharpnessSlider.configure(font=('poppins',11,'bold'),foreground='white')
sharpnessSlider.place(x=1070,y=165)

colorSlider = Scale(mains, label="Colors", from_=0, to=2, orient=HORIZONTAL, length=200,
                    command=apply_sliders, resolution=0.1, bg="#1f242d")
colorSlider.set(1)
colorSlider.configure(font=('poppins',11,'bold'),foreground='white')
colorSlider.place(x=1070,y=240)

btnRotate = Button(mains, text='Rotate', width=25, command=rotate, bg="#1f242d")
btnRotate.configure(font=('poppins',11,'bold'),foreground='white')
btnRotate.place(x=805,y=110)

reset_button = Button(mains,text="Reset",command=reset,bg="black",activebackground="ORANGE")
reset_button.configure(font=('poppins',10,'bold'),foreground='white')
reset_button.place(x=380,y=15)

btnChaImg = Button(mains, text='Change Image', width=25,command=ChangeImg,bg="#1f242d",activebackground="ORANGE")
btnChaImg.configure(font=('poppins',11,'bold'),foreground='white')
btnChaImg.place(x=805,y=35)

btnFlip = Button(mains, text='Flip', width=25, command=flip, bg="#1f242d")
btnFlip.configure(font=('poppins',11,'bold'),foreground='white')
btnFlip.place(x=805,y=180)

btnResize = Button(mains, text='Resize', width=25, command=activate_resize, bg="#1f242d")
btnResize.configure(font=('poppins',11,'bold'),foreground='white')
btnResize.place(x=805,y=255)

btnCrop = Button(mains, text='Crop', width=25, command=activate_crop, bg="#1f242d")
btnCrop.configure(font=('poppins',11,'bold'),foreground='white')
btnCrop.place(x=805,y=340)

btnBlur = Button(mains, text='Blur', width=25, command=blurr, bg="#1f242d")
btnBlur.configure(font=('poppins',11,'bold'),foreground='white')
btnBlur.place(x=805,y=425)

btnEmboss = Button(mains, text='Emboss', width=25, command=emboss, bg="#1f242d")
btnEmboss.configure(font=('poppins',11,'bold'),foreground='white')
btnEmboss.place(x=805,y=510)

btnEdgeEnhance = Button(mains, text='EdgeEnhance', width=25, command=edgeEnhance, bg="#1f242d")
btnEdgeEnhance.configure(font=('poppins',11,'bold'),foreground='white')
btnEdgeEnhance.place(x=805,y=595)

btnSave = Button(mains, text='Save', width=25, command=save, bg="black")
btnSave.configure(font=('poppins',11,'bold'),foreground='white')
btnSave.place(x=805,y=675)

btnClose = Button(mains, text='Close', command=close, bg="black",activebackground="ORANGE")
btnClose.configure(font=('poppins',10,'bold'),foreground='white')
btnClose.place(x=430,y=15)

mains.mainloop()