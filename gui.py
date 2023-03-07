import tkinter as tk
from tkinter import filedialog
from tkinter.messagebox import showinfo

import os, timeit

import model
import solver
import plot

class gui():
    def __init__(self, root, config):
        self.window_name = config["name"] + " " + config["version"]
        self.scale = config["scale"]
        self.print_head = config["print_head"]

        root.title(self.window_name)
        root.geometry("450x600")
        icon = tk.PhotoImage(file=os.path.dirname(os.path.realpath(__file__)) + "/media/icon.png")
        root.iconphoto(True, icon)

        frame = tk.Frame(root)

        self.dir_name_text = tk.StringVar()
        self.inp_name_text = tk.StringVar()

        self.dir_name_text.set("Working directory")
        self.inp_name_text.set("Input file")

        dir_button = tk.Button(frame, textvariable=self.dir_name_text, command=self.select_dir)
        inp_button = tk.Button(frame, textvariable=self.inp_name_text, command=self.select_inp)
        model_button = tk.Button(frame, text='Generate model', command=self.model_generate)
        solve_button = tk.Button(frame, text='Solve model', command=self.model_solve)
        plot_button = tk.Button(frame, text='Plot results', command=self.plot_results)
        quit_button = tk.Button(frame, text="Quit", command=root.destroy)
        self.log = tk.Text(frame, state='disabled', height="200", wrap='char')     

        frame.pack(fill="both", expand=True)
        dir_button.pack(fill="both", expand=True)
        inp_button.pack(fill="both", expand=True)
        model_button.pack(fill="both", expand=True)
        solve_button.pack(fill="both", expand=True)
        plot_button.pack(fill="both", expand=True)
        quit_button.pack(fill="both", expand=True)
        self.log.pack(fill="both", expand=True)

        self.writeToLog(config["disclaimer"])

    def writeToLog(self, msg):
        numlines = int(self.log.index('end - 1 line').split('.')[0])
        self.log['state'] = 'normal'
        if numlines==24:
            self.log.delete(1.0, 2.0)
        if self.log.index('end-1c')!='1.0':
            self.log.insert('end', '\n')
        self.log.insert('end', msg)
        self.log['state'] = 'disabled'
        

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
        
        self.dir_name_text.set("..." + self.dir_name[-25:])
        self.writeToLog("Working directory selected...")
        self.writeToLog(self.dir_name)


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
        self.writeToLog("Input file selected...")
        self.writeToLog(self.inp_name)


    def model_generate(self):
        self.writeToLog("Generating model " + self.inp_name + "...")
        try:
            input = model.load_input(self.dir_name + "/" + self.inp_name)
            self.model = model.call_gen_function(input)
            self.writeToLog("Nodes: " + str(self.model["node count"]))
            self.writeToLog("Elements: " + str(self.model["element count"]))
            self.writeToLog("DOF: " + str(self.model["dof"]))
            self.writeToLog("...complete")
        except Exception as e:
            self.writeToLog(str(e))


    def model_solve(self):    
        self.solver_start = timeit.default_timer()
        self.writeToLog("Solving model "  + self.inp_name + "...")
        self.call_solver()


    def call_solver(self):
        try:
            self.s = solver.solver(self.model, self.print_head)
            self.solver_end = timeit.default_timer()
            duration = self.solver_end - self.solver_start
            self.writeToLog("...complete [{:.3f}s]".format(duration))
        except Exception as e:
            self.writeToLog(str(e))


    def plot_results(self):    
        self.writeToLog("Ploting results "  + self.inp_name + ", close to continue...")
        try:
            plot.plot_results(self.model, self.s, self.scale, self.window_name)
            self.writeToLog("...closed")
        except Exception as e:
            self.writeToLog(str(e))


def run(config):
    root=tk.Tk()
    gui(root, config)
    root.mainloop()


if __name__=="__main__":
    root=tk.Tk()
    gui(
        root,
        {"version":"0.0.0",
        "disclaimer":""}
        )
    root.mainloop()