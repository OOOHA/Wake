import subprocess
import tkinter as tk
from tkinter import messagebox

class PreventSleepApp:
    def __init__(self, root):
        self.root = root
        self.caffeinate_process = None

        # Set up GUI
        self.root.title("Prevent Sleep (macOS)")
        self.root.geometry("300x150")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        label = tk.Label(root, text="Sleep prevention is inactive.", pady=10)
        label.pack()

        self.label = label
        self.start_button = tk.Button(root, text="Start Preventing Sleep", command=self.start_prevent_sleep)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(root, text="Stop Preventing Sleep", command=self.stop_prevent_sleep, state="disabled")
        self.stop_button.pack(pady=5)

    def start_prevent_sleep(self):
        if self.caffeinate_process is None:
            self.caffeinate_process = subprocess.Popen(["caffeinate"])
            self.label.config(text="Sleep prevention is active.")
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            messagebox.showinfo("Prevent Sleep", "Sleep prevention is now active!")

    def stop_prevent_sleep(self):
        if self.caffeinate_process:
            self.caffeinate_process.terminate()
            self.caffeinate_process = None
            self.label.config(text="Sleep prevention is inactive.")
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            messagebox.showinfo("Prevent Sleep", "Sleep prevention is now stopped!")

    def on_close(self):
        self.stop_prevent_sleep()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PreventSleepApp(root)
    root.mainloop()