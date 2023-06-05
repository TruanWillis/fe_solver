from tkinter import *
from tkinter import ttk

import os

# /home/truan/workspace/github.com/koodibaas/fe_solver/media/icon.png

root = Tk()

root.option_add('*tearOff', FALSE)

#gui = ttk.Frame(root, width=200, height=100)
gui = ttk.Frame(root)
toolbar_frame = ttk.Frame(gui, borderwidth=5, relief="ridge")
canvas_frame = ttk.Frame(gui, borderwidth=5, relief="ridge")
tree_frame = ttk.Frame(gui, borderwidth=5, relief="ridge")
dialog_frame = ttk.Frame(gui, borderwidth=5, relief="ridge")
text_frame = ttk.Frame(gui, borderwidth=5, relief="ridge")

icon = PhotoImage(file=os.path.dirname(os.path.realpath(__file__)) + "/media/icon.png")
icon = icon.subsample(10, 10)
toolbar_btn_zoom_in = Button(toolbar_frame, height=30, width=30, image=icon)
zoom_i = Button(toolbar_frame, height=30, width=30, image=icon)
zoom_o = Button(toolbar_frame, height=30, width=30, image=icon)


h = ttk.Scrollbar(canvas_frame, orient=HORIZONTAL)
v = ttk.Scrollbar(canvas_frame, orient=VERTICAL)

canvas = Canvas(canvas_frame, bg="white", scrollregion=(-400, -400, 400, 400), yscrollcommand=v.set, xscrollcommand=h.set)
#tree_lbl = ttk.Label(tree_frame, text="Design Tree")
tree_lbl = Listbox(tree_frame)
tree_scroll_v = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=tree_lbl.yview)
tree_scroll_h = ttk.Scrollbar(tree_frame, orient=HORIZONTAL, command=tree_lbl.xview)
dialog_lbl = ttk.Label(dialog_frame, text="Dialog Box")
text_box = Text(text_frame, height=8, state='disabled', wrap='word')
text_scroll_v = ttk.Scrollbar(text_frame, orient=VERTICAL, command=text_box.yview)

text_box['state'] = 'normal'
for i in range(20):
    t = "This is some tex to show how the text box works. "
    text_box.insert('end', t)
text_box['state'] = 'disabled'


gui.grid(column=0, row=0, sticky=(N, S, E, W))

toolbar_frame.grid(column=0, row=0, columnspan=2, sticky=(N, S, E, W))
toolbar_btn_zoom_in.grid(column=0, row=0)
zoom_i.grid(column=1, row=0)
zoom_o.grid(column=2, row=0)

canvas_frame.grid(column=1, row=1, rowspan=2, sticky=(N, S, E, W))
canvas.grid(column=0, row=0, sticky=(N, S, E, W))
h.grid(column=0, row=1, sticky=(W,E))
v.grid(column=1, row=0, sticky=(N,S))

tree_frame.grid(column=0, row=1, sticky=(N, S, E, W))
tree_lbl.grid(column=0, row=0, sticky=(N, S, E, W))
tree_scroll_v.grid(column=1, row=0, sticky=(N, S, E, W))
tree_scroll_h.grid(column=0, row=1, sticky=(N, S, E, W))

dialog_frame.grid(column=0, row=2, sticky=(N, S, E, W))
dialog_lbl.grid(column=0, row=0)

text_frame.grid(column=0, row=3, columnspan=2, sticky=(N, S, E, W))
text_box.grid(column=0, row=0, sticky=(N, S, E, W))
text_scroll_v.grid(column=1, row=0, sticky=(N, S, E, W))

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

gui.columnconfigure(0, weight=1)
gui.columnconfigure(1, weight=3)

gui.rowconfigure(1, weight=3)
gui.rowconfigure(2, weight=3)

canvas_frame.columnconfigure(0, weight=1)
canvas_frame.rowconfigure(0, weight=1)

tree_frame.columnconfigure(0, weight=1)
tree_frame.rowconfigure(0, weight=1)

dialog_frame.columnconfigure(0, weight=1)
dialog_frame.rowconfigure(0, weight=1)

text_frame.columnconfigure(0, weight=1)
text_frame.rowconfigure(0, weight=1)


for i in range(1,101):
    tree_lbl.insert('end', 'Line %d of 100' % i)


canvas.create_rectangle(50, 50, 200, 200, fill="blue")
canvas.create_line(0,0,100,100)

#canvas.bind("<MouseWheel>", do_zoom)
canvas.bind('<ButtonPress-1>', lambda event: canvas.scan_mark(event.x, event.y))
canvas.bind("<B1-Motion>", lambda event: canvas.scan_dragto(event.x, event.y, gain=1))

def do_zoom(event):
    x = canvas.canvasx(event.x)
    y = canvas.canvasy(event.y)
    factor = 1.001 ** event.delta
    canvas.scale(ALL, x, y, factor, factor)

    scale = 1    
    delta = 0.1
    
def zoom_in():
    canvas.scale(ALL, 250, 250, scale + delta, scale + delta)

def zoom_out():
    canvas.scale(ALL, 250, 250, scale - delta, scale - delta)


root.mainloop()