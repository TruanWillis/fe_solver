import tkinter as tk
import tkinter.ttk as ttk


mainWindow = tk.Tk()


def update_progress_bar():
    x = barVar.get()
    if x < 100:
        barVar.set(x + 0.5)
        mainWindow.after(50, update_progress_bar)
    else:
        print("Complete")


barVar = tk.DoubleVar()
barVar.set(0)
bar = ttk.Progressbar(
    mainWindow,
    length=200,
    style="black.Horizontal.TProgressbar",
    variable=barVar,
    mode="determinate",
)
bar.grid(row=1, column=0)
button = tk.Button(mainWindow, text="Click", command=update_progress_bar)
button.grid(row=0, column=0)

mainWindow.mainloop()
