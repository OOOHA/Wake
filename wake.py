import ctypes
import tkinter as tk
from tkinter import messagebox

# Constants for Windows Sleep prevention
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

def prevent_sleep():
    """Prevents Windows from sleeping."""
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)

def on_close():
    """Allows Windows to sleep when the script is closed."""
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    root.destroy()

if __name__ == "__main__":
    prevent_sleep()

    # Create a simple GUI
    root = tk.Tk()
    root.title("Prevent Sleep")
    root.geometry("300x100")
    root.protocol("WM_DELETE_WINDOW", on_close)

    label = tk.Label(root, text="Sleep prevention is active.\nClose this window to stop.", padx=10, pady=20)
    label.pack()

    root.mainloop()