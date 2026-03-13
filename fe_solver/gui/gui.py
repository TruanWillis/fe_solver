import os
import sys
import timeit
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

from fe_solver.core import model
from fe_solver.core import solver
from fe_solver.gui import plot

# from tkinter.messagebox import showinfo

ASSETS = Path(__file__).parent.parent / "assets"


class StdoutRedirector:
    """
    Redirects stdout writes to the GUI log window.
    """
    
    def __init__(self, write_func):
        self.write_func = write_func
    
    def write(self, message):
        if message.strip():
            self.write_func(message.strip())
    
    def flush(self):
        pass


class gui:
    def __init__(self, root, app_config, user_config):
        """
        Initiates gui class object.

        Args:
            root (object): TKinter tk class object.
            app_config (dict): fe_solver configurable values.
            user_config (dict): User configurable values.
        """

        self.window_name = app_config["name"] + " " + app_config["version"]
        self.scale = user_config["scale"]
        self.print_head = user_config["print_head"]
        self.save_matrix = user_config["save_matrix"]
        self.fe_solver = user_config["fe_solver"]

        root.title(self.window_name)
        root.geometry("450x600")
        icon = tk.PhotoImage(
            file=ASSETS / "icons" / "icon.png"
        )
        root.iconphoto(True, icon)

        frame = tk.Frame(root)

        self.dir_name_text = tk.StringVar()
        self.inp_name_text = tk.StringVar()

        self.dir_name_text.set("Working directory")
        self.inp_name_text.set("Input file")

        dir_button = tk.Button(
            frame, textvariable=self.dir_name_text, command=self.select_dir
        )
        inp_button = tk.Button(
            frame, textvariable=self.inp_name_text, command=self.select_inp
        )
        model_button = tk.Button(
            frame, text="Generate model", command=self.model_generate
        )
        solve_button = tk.Button(frame, text="Solve model", command=self.model_solve)
        plot_button = tk.Button(frame, text="Plot results", command=self.plot_results)
        quit_button = tk.Button(frame, text="Quit", command=root.destroy)
        self.log = tk.Text(frame, state="disabled", height="200", wrap="char")

        frame.pack(fill="both", expand=True)
        dir_button.pack(fill="both", expand=True)
        inp_button.pack(fill="both", expand=True)
        model_button.pack(fill="both", expand=True)
        solve_button.pack(fill="both", expand=True)
        plot_button.pack(fill="both", expand=True)
        quit_button.pack(fill="both", expand=True)
        self.log.pack(fill="both", expand=True)

        self.writeToLog(app_config["disclaimer"] + "\n")

    def writeToLog(self, msg):
        """
        Writes text to gui log.

        Args:
            msg (string): Text to display.
        """

        numlines = int(self.log.index("end - 1 line").split(".")[0])
        self.log["state"] = "normal"
        if numlines == 24:
            self.log.delete(1.0, 2.0)
        if self.log.index("end-1c") != "1.0":
            self.log.insert("end", "\n")
        self.log.insert("end", msg)
        self.log["state"] = "disabled"

    def select_dir(self):
        """
        Button function to select working directory.
        """

        dir_name = filedialog.askdirectory(title="Select working directory")
        self.dir_name = Path(dir_name)

        """
        showinfo(
            title="Selected directory",
            message=self.dir_name
        )
        """
        if len(str(self.dir_name)) > 25:
            display_path = f"...{str(self.dir_name)[-25:]}" 
        else:
            display_path = str(self.dir_name)

        self.dir_name_text.set(display_path)
        self.writeToLog("Working directory selected...")
        self.writeToLog(f"{self.dir_name}\n")

    def select_inp(self):
        """
        Button function to select inp file.
        """

        filetypes = (
            ("inp file", "*.inp"),
            ("text files", "*.txt"),
            ("all files", "*.*"),
        )

        self.inp_name = filedialog.askopenfilename(
            title="Select input file", initialdir=self.dir_name, filetypes=filetypes
        )

        self.inp_name = os.path.basename(self.inp_name)

        """
        showinfo(
            title='Selected File',
            message=self.inp_name
            )
        """

        self.inp_name_text.set(self.inp_name)
        self.writeToLog("Input file selected...")
        self.writeToLog(self.inp_name + "\n")

    def model_generate(self):
        """
        Button function to generate model from selected inp file.
        """

        model_start = timeit.default_timer()
        self.writeToLog("Generating model " + self.inp_name + "...")
        try:
            input = model.load_input(self.dir_name / self.inp_name)
            self.model = model.call_gen_function(input)
            self.writeToLog("Nodes: " + str(self.model["node count"]))
            self.writeToLog("Elements: " + str(self.model["element count"]))
            self.writeToLog("DOF: " + str(self.model["dof"]))
            model_end = timeit.default_timer()
            duration = model_end - model_start
            self.writeToLog("...complete [{:.3f}s]".format(duration) + "\n")
        except Exception as e:
            self.writeToLog(str(e))

    def model_solve(self):
        """
        Button function to solve model.
        """

        # TODO: Fix button so is can print live statements during solver

        self.solver_start = timeit.default_timer()
        self.writeToLog("Solving model " + self.inp_name + "...")
        self.call_solver()

    def call_solver(self):
        """
        Calls solver function.
        """

        if self.fe_solver:
            self.writeToLog("Direct solver: fe_solver")
        else:
            self.writeToLog("Direct solver: numpy")
        
        original_stdout = sys.stdout
        sys.stdout = StdoutRedirector(self.writeToLog)

        try:
            self.s = solver.solver(
                self.model,
                self.fe_solver,
                self.print_head,
                self.save_matrix,
                self.dir_name,
            )
            self.solver_end = timeit.default_timer()
            duration = self.solver_end - self.solver_start
            self.writeToLog("...complete [{:.3f}s]".format(duration) + "\n")
        except Exception as e:
            self.writeToLog(str(e))
        finally:
            sys.stdout = original_stdout

    def plot_results(self):
        """
        Button function to plot solver results.
        """

        self.writeToLog("Plotting results " + self.inp_name + ", close to continue...")
        try:
            plot.plot_results(
                self.model, self.s, self.scale, self.window_name, self.save_matrix
            )
            self.writeToLog("...closed" + "\n")
        except Exception as e:
            self.writeToLog(str(e))


def run(app_config, user_config):
    """
    Runs gui.

    Args:
        app_config (dict): fe_solver configurable values.
        config (dict): User configurable values.
    """

    root = tk.Tk()
    gui(root, app_config, user_config)
    root.mainloop()


if __name__ == "__main__":
    """
    __main__ used for development purposes.
    """

    root = tk.Tk()
    gui(root, {"name": "Test", "version": "0.0.0", "disclaimer": ""})
    root.mainloop()
