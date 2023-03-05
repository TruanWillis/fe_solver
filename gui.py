'''
from tkinter import *
import numpy as np
import matplotlib.pyplot as plt

root = Tk()
root.geometry("800x800")
root.title("openFEM 0.0.1")

def plot_mises():
    test = np.random.normal(100, 1000, 10)
    plt.hist(test, 5)
    plt.show()


my_button = Button(root, text="FEA is cool", command=plot_mises)
my_button.pack()
my_button.mainloop()

'''


'''
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter.messagebox import showinfo

root = Tk()
root.title("openFEM 0.0.1")
root.geometry("100x300")

#frm = ttk.Frame(root, padding=10)
#frm.grid()

def select_folder():
    dirname = filedialog.askdirectory(
        title="Specify working directory"
    )

    showinfo(
        title="Selected directory",
        message=dirname
    )    

    return dirname


def select_file(dirname):
    filetypes = (
        ("inp file", "*.inp"),
        ("text files", "*.txt"),
        ("all files", "*.*")
    )

    filename = filedialog.askopenfilename(
        title='Open a file',
        initialdir=dirname,
        filetypes=filetypes
        )

    showinfo(
        title='Selected File',
        message=filename
        )


#ttk.Label(frm, text="Working directory").grid(column=0, row=0)
#wk_dir = ttk.Button(frm, text="Select", command=select_folder).grid(column=1, row=0)

#ttk.Label(frm, text="inp file").grid(column=0, row=1)
#inp_file = ttk.Button(frm, text="Select", command=select_file(wk_dir)).grid(column=1, row=1)

#ttk.Button(frm, text="Quit", command=root.destroy).grid(row=4)


wk_dir = ttk.Button(
    root,
    text='Working directory',
    command=select_folder
    )

inp_file = ttk.Button(
    root,
    text='inp_file',
    command=select_file(wk_dir)
    )

quit = ttk.Button(
    root, 
    text="Quit", 
    command=root.destroy)

wk_dir.pack(expand=True)
inp_file.pack(expand=True)


# run the application
root.mainloop()

#filename = filedialog.askopenfilename()
#dirname = filedialog.askdirectory
#root.mainloop()





'''
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter.messagebox import showinfo

import os

import load_inp
import solver
import plot

#import Tkinter as tk

class gui():
    def __init__(self, root):
        root.title("openFEM 0.0.1")
        root.geometry("400x300")
        frame = ttk.Frame(root, padding=(15))

        self.dir_name_text = StringVar()
        self.inp_name_text = StringVar()

        self.dir_name_text.set("Working directory")
        self.inp_name_text.set("Input file")

        dir_button = ttk.Button(frame, textvariable=self.dir_name_text, command=self.select_dir)
        inp_button = ttk.Button(frame, textvariable=self.inp_name_text, command=self.select_inp)
        model_button = ttk.Button(frame, text='Generate model', command=self.model_load)
        solve_button = ttk.Button(frame, text='Solve model', command=self.model_solve)
        quit_button = ttk.Button(frame, text="Quit", command=root.destroy)

        frame.pack(fill=BOTH, expand=True)
        dir_button.pack(fill=BOTH, expand=True)
        inp_button.pack(fill=BOTH, expand=True)
        model_button.pack(fill=BOTH, expand=True)
        solve_button.pack(fill=BOTH, expand=True)
        quit_button.pack(fill=BOTH, expand=True)


    def select_dir(self):
        self.dir_name = filedialog.askdirectory(
            title="Select working directory"
        )

        '''
        showinfo(
            title="Selected directory",
            message=self.dir_name
        )    
        '''
        
        self.dir_name_text.set("..." + self.dir_name[-20:])

    def select_inp(self):
        filetypes = (
            ("inp file", "*.inp"),
            ("text files", "*.txt"),
            ("all files", "*.*")
        )

        self.inp_name = filedialog.askopenfilename(
            title='Select input file',
            initialdir=self.dir_name,
            filetypes=filetypes
            )
        
        self.inp_name = os.path.basename(self.inp_name)

        '''
        showinfo(
            title='Selected File',
            message=self.inp_name
            )
        '''
            
        self.inp_name_text.set(self.inp_name)

    def model_load(self):
        inp = load_inp.load_inp(self.dir_name + "/" + self.inp_name)
        self.model = load_inp.call_gen_function(inp)

    def model_solve(self):    
        s = solver.solver(self.model)
        s.define_element_stiffness()
        s.define_global_stiffness()
        s.define_boundary()
        s.define_load()
        s.reduce_matrix()
        s.compute_dispalcements()
        s.compute_normal_stress()
        s.compute_principal_stress()
        s.compute_mises_stress()
        plot.plot_results(self.model, s, 2)


def main():
    root=Tk()
    gui(root)
    root.mainloop()

if __name__=="__main__":
    main()




'''

import tkinter as tk
import matplotlib

matplotlib.use('TkAgg')

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)
'''
'''

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title('Tkinter Matplotlib Demo')

        self.geometry("800x800")

        # prepare data
        data = {
            'Python': 11.27,
            'C': 11.16,
            'Java': 10.46,
            'C++': 7.5,
            'C#': 5.26
        }

        languages = data.keys()
        popularity = data.values()

        # create a figure
        figure = Figure(figsize=(3, 4), dpi=100)

        # create FigureCanvasTkAgg object
        figure_canvas = FigureCanvasTkAgg(figure, self)

        # create the toolbar
        NavigationToolbar2Tk(figure_canvas, self)

        # create axes
        axes = figure.add_subplot()

        # create the barchart
        axes.bar(languages, popularity)
        axes.set_title('Top 5 Programming Languages')
        axes.set_ylabel('Popularity')

        figure_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)


if __name__ == '__main__':
    app = App()
    app.mainloop()
'''
'''
import tkinter

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import numpy as np


root = tkinter.Tk()
root.wm_title("Embedding in Tk")

fig = Figure(figsize=(5, 4), dpi=100)
t = np.arange(0, 3, .01)
ax = fig.add_subplot()
line, = ax.plot(t, 2 * np.sin(2 * np.pi * t))
ax.set_xlabel("time [s]")
ax.set_ylabel("f(t)")

canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
canvas.draw()

# pack_toolbar=False will make it easier to use a layout manager later on.
toolbar = NavigationToolbar2Tk(canvas, root, pack_toolbar=False)
toolbar.update()

canvas.mpl_connect(
    "key_press_event", lambda event: print(f"you pressed {event.key}"))
canvas.mpl_connect("key_press_event", key_press_handler)

button_quit = tkinter.Button(master=root, text="Quit", command=root.destroy)


def update_frequency(new_val):
    # retrieve frequency
    f = float(new_val)

    # update data
    y = 2 * np.sin(2 * np.pi * f * t)
    line.set_data(t, y)

    # required to update canvas and attached toolbar!
    canvas.draw()


slider_update = tkinter.Scale(root, from_=1, to=5, orient=tkinter.HORIZONTAL,
                              command=update_frequency, label="Frequency [Hz]")

# Packing order is important. Widgets are processed sequentially and if there
# is no space left, because the window is too small, they are not displayed.
# The canvas is rather flexible in its size, so we pack it last which makes
# sure the UI controls are displayed as long as possible.
button_quit.pack(side=tkinter.BOTTOM)
slider_update.pack(side=tkinter.BOTTOM)
toolbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)

tkinter.mainloop()

'''

'''
from tkinter import * 
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
NavigationToolbar2Tk)
  
# plot function is created for 
# plotting the graph in 
# tkinter window
def plot():
  
    # the figure that will contain the plot
    fig = Figure(figsize = (5, 5),
                 dpi = 100)
  
    # list of squares
    y = [i**2 for i in range(101)]
  
    # adding the subplot
    plot1 = fig.add_subplot(111)
  
    # plotting the graph
    plot1.plot(y)
  
    # creating the Tkinter canvas
    # containing the Matplotlib figure
    canvas = FigureCanvasTkAgg(fig,
                               master = window)  
    canvas.draw()
  
    # placing the canvas on the Tkinter window
    canvas.get_tk_widget().pack()
  
    # creating the Matplotlib toolbar
    toolbar = NavigationToolbar2Tk(canvas,
                                   window)
    toolbar.update()
  
    # placing the toolbar on the Tkinter window
    canvas.get_tk_widget().pack()
  
# the main Tkinter window
window = Tk()
  
# setting the title 
window.title('Plotting in Tkinter')
  
# dimensions of the main window
window.geometry("500x500")
  
# button that displays the plot
plot_button = Button(master = window, 
                     command = plot,
                     height = 2, 
                     width = 10,
                     text = "Plot")
  
# place the button 
# in main window
plot_button.pack()
  
# run the gui
window.mainloop()

'''