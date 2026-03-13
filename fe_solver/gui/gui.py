import queue
import sys
import threading
import timeit
import traceback
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

from fe_solver.core import model
from fe_solver.core import solver
from fe_solver.gui import plot


ASSETS = Path(__file__).parent.parent / "assets"


class StdoutRedirector:
    """
    Redirects stdout writes to the GUI log window.
    """
    
    def __init__(self, log_queue):
        self.log_queue = log_queue
    
    def write(self, message):
        if message.strip():
            self.log_queue.put(message.strip())
    
    def flush(self):
        pass


class FESolverApp:
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
        
        self.root = root
        self.log_queue = queue.Queue()

        self.root.title(self.window_name)
        self.root.geometry("450x600")
        icon = tk.PhotoImage(
            file=ASSETS / "icons" / "icon.png"
        )
        self.root.iconphoto(True, icon)

        frame = tk.Frame(root)

        self.dir_name_text = tk.StringVar()
        self.inp_name_text = tk.StringVar()

        self.dir_name_text.set("Working directory")
        self.inp_name_text.set("Input file")

        dir_button = tk.Button(
            frame, textvariable=self.dir_name_text, command=self.select_dir
        )
        self.inp_button = tk.Button(
            frame, textvariable=self.inp_name_text, command=self.select_inp, state="disabled"
        )
        self.model_button = tk.Button(
            frame, text="Generate model", command=self.model_generate, state="disabled"
        )
        self.solve_button = tk.Button(frame, text="Solve model", command=self.model_solve, state="disabled")
        self.plot_button = tk.Button(frame, text="Plot results", command=self.plot_results, state="disabled")
        quit_button = tk.Button(frame, text="Quit", command=root.destroy)

        log_frame = tk.Frame(frame)
        self.log = tk.Text(log_frame, state="disabled", wrap="word")
        scrollbar = tk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)
        log_frame.pack(fill="both", expand=True)

        frame.pack(fill="both", expand=True)
        dir_button.pack(fill="both", expand=True)
        self.inp_button.pack(fill="both", expand=True)
        self.model_button.pack(fill="both", expand=True)
        self.solve_button.pack(fill="both", expand=True)
        self.plot_button.pack(fill="both", expand=True)
        quit_button.pack(fill="both", expand=True)
        self.log.pack(fill="both", expand=True)

        self.writeToLog(f"{app_config['disclaimer']}\n")

    def writeToLog(self, msg):
        """
        Writes text to gui log.

        Args:
            msg (string): Text to display.
        """

        self.log["state"] = "normal"
        if self.log.index("end-1c") != "1.0":
            self.log.insert("end", "\n")
        self.log.insert("end", msg)
        self.log["state"] = "disabled"
        self.log.see("end")

    def select_dir(self):
        """
        Button function to select working directory.
        """

        dir_name = filedialog.askdirectory(title="Select working directory")
        self.dir_name = Path(dir_name)

        if len(str(self.dir_name)) > 25:
            display_path = f"...{str(self.dir_name)[-25:]}" 
        else:
            display_path = str(self.dir_name)

        self.dir_name_text.set(display_path)
        self.writeToLog("Working directory selected...")
        self.writeToLog(f"{self.dir_name}\n")
        self.inp_button.config(state="normal")

    def select_inp(self):
        """
        Button function to select inp file.
        """

        filetypes = (
            ("inp file", "*.inp"),
            ("text files", "*.txt"),
            ("all files", "*.*"),
        )

        inp_name = filedialog.askopenfilename(
            title="Select input file", initialdir=self.dir_name, filetypes=filetypes
        )

        self.inp_path = Path(inp_name)
        self.inp_name_text.set(self.inp_path.name)
        self.writeToLog("Input file selected...")
        self.writeToLog(f"{self.inp_path.name}\n")
        self.model_button.config(state="normal")
        self.solve_button.config(state="disabled")
        self.plot_button.config(state="disabled")

    def model_generate(self):
        """
        Button function to generate model from selected inp file.
        """

        model_start = timeit.default_timer()
        self.writeToLog(f"Generating model {self.inp_path.name}...")
        try:
            inp_lines = model.load_input(self.inp_path)
            self.model = model.call_gen_function(inp_lines)
            self.writeToLog(f"Nodes: {self.model['node count']}")
            self.writeToLog(f"Elements: {self.model['element count']}")
            self.writeToLog(f"DOF: {self.model['dof']}")
            model_end = timeit.default_timer()
            duration = model_end - model_start
            self.writeToLog(f"...complete [{duration:.3f}s]\n")
            self.solve_button.config(state="normal")
            self.plot_button.config(state="disabled")
        except Exception as e:
            e_filename, e_line, e_function = traceback_info(e)
            self.writeToLog(f"\nError generating model: {str(e)}")
            self.writeToLog(f"File: {e_filename}")
            self.writeToLog(f"Line: {e_line}")
            self.writeToLog(f"Function: {e_function}")

    def model_solve(self):
        """
        Button function to solve model.
        """

        self.solve_button.config(state="disabled")
        self.plot_button.config(state="disabled")

        self.solver_start = timeit.default_timer()
        self.solver_running = True
        self.writeToLog(f"Solving model {self.inp_path.name}...")
        
        self.root.after(100, self.poll_log_queue)

        thread = threading.Thread(target=self.call_solver, daemon=True)
        thread.start()

    def call_solver(self):
        """
        Calls solver function.
        """

        if self.fe_solver:
            self.writeToLog("Direct solver: fe_solver")
        else:
            self.writeToLog("Direct solver: numpy")
        
        original_stdout = sys.stdout
        sys.stdout = StdoutRedirector(self.log_queue)

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
            self.log_queue.put(f"...complete [{duration:.3f}s]\n")
            self.plot_button.config(state="normal")
        except Exception as e:
            e_filename, e_line, e_function = traceback_info(e)
            self.log_queue.put(f"\nError solving model: {str(e)}")
            self.log_queue.put(f"File: {e_filename}")
            self.log_queue.put(f"Line: {e_line}")
            self.log_queue.put(f"Line: {e_function}")
        finally:
            sys.stdout = original_stdout
            self.solver_running = False
            self.root.after(0, lambda: self.plot_button.config(state="normal"))
            self.root.after(0, lambda: self.solve_button.config(state="normal"))

    def plot_results(self):
        """
        Button function to plot solver results.
        """

        self.writeToLog(f"Plotting results {self.inp_path.name}...")
        try:
            self.writeToLog(f"Max displacement: {float(self.s.displacements.abs().max()):.4e}")
            self.writeToLog(f"Max von Mises stress: {float(self.s.stress_mises.max()):.4e}")
            self.writeToLog("...close to continue...")
            plot.plot_results(
                self.model, self.s, self.scale, self.window_name, self.save_matrix
            )
            self.writeToLog(f"...closed\n")
        except Exception as e:
            e_filename, e_line, e_function = traceback_info(e)
            self.writeToLog(f"\nError ploting result: {str(e)}")
            self.writeToLog(f"File: {e_filename}")
            self.writeToLog(f"Line: {e_line}")
            self.writeToLog(f"Line: {e_function}")

    def poll_log_queue(self):
        """
        Checks the log queue for new messages and writes them to the log.
        Reschedules itself every 100ms while the solver is running.
        """
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.writeToLog(message)
        except queue.Empty:
            pass

        if self.solver_running:
            self.root.after(100, self.poll_log_queue)


def traceback_info(e):
    tb = e.__traceback__
    frame = traceback.extract_tb(tb)[-1]
    file_path = Path(frame.filename)
    return file_path.name, frame.lineno, frame.name


def run(app_config, user_config):
    """
    Runs gui.

    Args:
        app_config (dict): fe_solver configurable values.
        config (dict): User configurable values.
    """

    root = tk.Tk()
    FESolverApp(root, app_config, user_config)
    root.mainloop()


if __name__ == "__main__":
    """
    __main__ used for development purposes.
    """

    root = tk.Tk()
    gui(root, {"name": "Test", "version": "0.0.0", "disclaimer": ""})
    root.mainloop()
