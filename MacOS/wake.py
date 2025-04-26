import sys
import os
import subprocess
import atexit
import locale
import json

import customtkinter as ctk

# -----------------------------------------------------------------------------
# macOS Sleep-prevention constants
# -----------------------------------------------------------------------------
APP_NAME = "PreventSleepApp"
# Make sure CFBundleIdentifier = LaunchAgent  Label 
APP_IDENTIFIER = "com.preventsleepapp.launcher"
LAUNCHAGENT_PATH = os.path.expanduser(
    f"~/Library/LaunchAgents/{APP_IDENTIFIER}.plist"
)

# -----------------------------------------------------------------------------
# prevent sleep
# -----------------------------------------------------------------------------
caffeinate_proc = None
def prevent_sleep():
    global caffeinate_proc
    try:
        caffeinate_proc = subprocess.Popen(["/usr/bin/caffeinate", "-dims"])
        atexit.register(lambda: caffeinate_proc.terminate())
    except Exception as e:
        print("Warning: cannot launch caffeinate:", e)
        caffeinate_proc = None

def allow_sleep():
    if caffeinate_proc:
        caffeinate_proc.terminate()

# -----------------------------------------------------------------------------
# LaunchAgent launch at startup
# -----------------------------------------------------------------------------
def add_to_startup():
    python_exec = sys.executable
    script_path = os.path.abspath(sys.argv[0])
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{APP_IDENTIFIER}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python_exec}</string>
    <string>{script_path}</string>
  </array>
  <key>RunAtLoad</key><true/>
</dict>
</plist>"""
    os.makedirs(os.path.dirname(LAUNCHAGENT_PATH), exist_ok=True)
    with open(LAUNCHAGENT_PATH, "w", encoding="utf-8") as f:
        f.write(plist)
    subprocess.run(["launchctl", "load", LAUNCHAGENT_PATH], stderr=subprocess.DEVNULL)

def remove_from_startup():
    subprocess.run(["launchctl", "unload", LAUNCHAGENT_PATH], stderr=subprocess.DEVNULL)
    try:
        os.remove(LAUNCHAGENT_PATH)
    except FileNotFoundError:
        pass

def is_in_startup():
    return os.path.exists(LAUNCHAGENT_PATH)

# -----------------------------------------------------------------------------
# Persistent "start minimized" setting
# -----------------------------------------------------------------------------
def set_start_minimized(on: bool):
    subprocess.run([
        "defaults", "write",
        APP_IDENTIFIER, "StartMinimized",
        "-bool", "YES" if on else "NO"
    ], stderr=subprocess.DEVNULL)

def get_start_minimized() -> bool:
    p = subprocess.run([
        "defaults", "read",
        APP_IDENTIFIER, "StartMinimized"
    ], capture_output=True, text=True)
    return p.returncode == 0 and p.stdout.strip().lower() in ("1","yes","true")

# -----------------------------------------------------------------------------
# translations
# -----------------------------------------------------------------------------
if getattr(sys, "_MEIPASS", None):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(base_path, "translations.json"), "r", encoding="utf-8") as f:
    ALL_TX = json.load(f)

def get_system_lang():
    lang, _ = locale.getdefaultlocale()
    if not lang:
        return "en"
    code = lang.replace("-", "_")
    for avail in ALL_TX.keys():
        if code.lower().startswith(avail.lower()):
            return avail
    return "en"

def t(key: str) -> str:
    return ALL_TX.get(current_lang, ALL_TX["en"]).get(key, key)

# -----------------------------------------------------------------------------
# UI 
# -----------------------------------------------------------------------------
def change_language(new_lang: str):
    global current_lang
    current_lang = new_lang
    status_lbl.configure(text=t("status_active"))
    label_language.configure(text=t("settings_language"))
    label_theme.configure(text=t("settings_theme"))
    label_startup.configure(text=t("settings_startup"))
    label_minimize.configure(text=t("settings_start_minimized"))

    # update all labels
    lang_menu.configure(values=[ALL_TX[c][f"lang_{c}"] for c in ALL_TX])
    lang_menu.set(ALL_TX[current_lang][f"lang_{current_lang}"])

    theme_vals = [t("theme_Light"), t("theme_Dark"), t("theme_Auto")]
    theme_menu.configure(values=theme_vals)
    cm = ctk.get_appearance_mode()
    theme_menu.set(t(f"theme_{cm if cm in ('Light','Dark') else 'Auto'}"))

    startup_vals = [t("startup_on"), t("startup_off")]
    startup_menu.configure(values=startup_vals)
    startup_menu.set(t("startup_on") if is_in_startup() else t("startup_off"))

    min_vals = [t("minimize_on"), t("minimize_off")]
    minimize_menu.configure(values=min_vals)
    minimize_menu.set(t("minimize_on") if get_start_minimized() else t("minimize_off"))

def on_theme_change(sel: str):
    rev = {
        t("theme_Light"): "Light",
        t("theme_Dark"):  "Dark",
        t("theme_Auto"):  "System"
    }
    ctk.set_appearance_mode(rev.get(sel, "System"))

def on_startup_change(sel: str):
    if sel == t("startup_on"):
        add_to_startup()
    else:
        remove_from_startup()

def on_minimize_change(sel: str):
    if sel == t("minimize_on"):
        set_start_minimized(True)
    else:
        set_start_minimized(False)

def on_close(event=None):
    allow_sleep()
    root.destroy()
    sys.exit(0)

def toggle_settings():
    if settings_frame.winfo_viewable():
        settings_frame.grid_remove()
    else:
        settings_frame.grid()


if __name__ == "__main__":
    prevent_sleep()
    current_lang = get_system_lang()

    # Init CustomTkinter
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()

    # App icon
    ico = os.path.join(base_path, "app.ico")
    if os.path.exists(ico):
        try: root.iconbitmap(ico)
        except: pass  

    root.title("Prevent Sleep")
    root.geometry("400x200")
    root.resizable(True, True)

    
    if get_start_minimized():
        root.after(100, lambda: root.iconify())

    # Close button = Command Q
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.bind_all("<Command-q>", lambda e: on_close())
    root.bind_all("<Command-Q>", lambda e: on_close())
    try:
        root.createcommand('tk::mac::Quit', on_close)
    except:
        pass

    # Toolbar
    toolbar = ctk.CTkFrame(root, height=40)
    toolbar.pack(fill="x", side="top", padx=5, pady=5)
    ctk.CTkButton(
        toolbar, text="☰", width=30, height=30,
        fg_color="transparent", hover_color=None,
        command=toggle_settings
    ).pack(side="left")

    # Main body
    body = ctk.CTkFrame(root)
    body.pack(fill="both", expand=True, padx=5, pady=(0,5))
    body.columnconfigure(1, weight=1)
    body.rowconfigure(0, weight=1)

    # Settings frame
    settings_frame = ctk.CTkScrollableFrame(
        master=body, corner_radius=10, width=180
    )
    settings_frame.grid(row=0, column=0, sticky="ns", padx=(0,5))
    settings_frame.grid_remove()

    # Language settings
    label_language = ctk.CTkLabel(
        settings_frame, text=t("settings_language"), anchor="w"
    )
    label_language.pack(fill="x", padx=10, pady=(10,0))
    lang_vals = [ALL_TX[c][f"lang_{c}"] for c in ALL_TX]
    lang_menu = ctk.CTkOptionMenu(
        settings_frame, values=lang_vals,
        command=lambda v: change_language(
            list(ALL_TX.keys())[lang_vals.index(v)]
        ),
        width=150, dynamic_resizing=False
    )
    lang_menu.pack(fill="x", padx=10, pady=(0,10))
    lang_menu.set(ALL_TX[current_lang][f"lang_{current_lang}"])

    # Theme settings
    label_theme = ctk.CTkLabel(
        settings_frame, text=t("settings_theme"), anchor="w"
    )
    label_theme.pack(fill="x", padx=10)
    theme_menu = ctk.CTkSegmentedButton(
        settings_frame,
        values=[t("theme_Light"), t("theme_Dark"), t("theme_Auto")],
        command=on_theme_change
    )
    theme_menu.pack(fill="x", padx=10, pady=(0,10))
    cm = ctk.get_appearance_mode()
    theme_menu.set(t(f"theme_{cm if cm in ('Light','Dark') else 'Auto'}"))

    # Startup settings
    label_startup = ctk.CTkLabel(
        settings_frame, text=t("settings_startup"), anchor="w"
    )
    label_startup.pack(fill="x", padx=10)
    startup_menu = ctk.CTkSegmentedButton(
        settings_frame,
        values=[t("startup_on"), t("startup_off")],
        command=on_startup_change
    )
    startup_menu.pack(fill="x", padx=10, pady=(0,10))
    startup_menu.set(t("startup_on") if is_in_startup() else t("startup_off"))

    # Start Minimized settings
    label_minimize = ctk.CTkLabel(
        settings_frame, text=t("settings_start_minimized"), anchor="w"
    )
    label_minimize.pack(fill="x", padx=10)
    minimize_menu = ctk.CTkSegmentedButton(
        settings_frame,
        values=[t("minimize_on"), t("minimize_off")],
        command=on_minimize_change
    )
    minimize_menu.pack(fill="x", padx=10, pady=(0,10))
    minimize_menu.set(t("minimize_on") if get_start_minimized() else t("minimize_off"))

    # status label
    content = ctk.CTkFrame(master=body, fg_color="transparent")
    content.grid(row=0, column=1, sticky="nsew")
    status_lbl = ctk.CTkLabel(
        content, text=t("status_active"),
        font=ctk.CTkFont(size=16), justify="center"
    )
    status_lbl.place(relx=0.5, rely=0.5, anchor="center")

    root.mainloop()
