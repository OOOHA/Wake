import sys
import os
import ctypes
import locale
import winreg
import json

import customtkinter as ctk

# --- Windows Sleep-prevention constants ---
ES_CONTINUOUS       = 0x80000000
ES_SYSTEM_REQUIRED  = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002
APP_NAME = "PreventSleepApp"

def prevent_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )

def allow_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)

def add_to_startup():
    exe = sys.executable
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE
    )
    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe)
    winreg.CloseKey(key)

def remove_from_startup():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
    except FileNotFoundError:
        pass

def is_in_startup():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run"
        )
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False

# --- Persistent "start minimized" setting in registry ---
def set_start_minimized(on: bool):
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\{APP_NAME}")
    winreg.SetValueEx(key, "StartMinimized", 0, winreg.REG_DWORD, 1 if on else 0)
    winreg.CloseKey(key)

def get_start_minimized() -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, f"Software\\{APP_NAME}")
        val, _ = winreg.QueryValueEx(key, "StartMinimized")
        winreg.CloseKey(key)
        return bool(val)
    except FileNotFoundError:
        return False

def get_system_lang():
    lang, _ = locale.getdefaultlocale()
    if not lang:
        return "en"
    code = lang.replace("-", "_")
    for avail in ALL_TX.keys():
        if code.lower().startswith(avail.lower()):
            return avail
    return "en"

# — Load translations.json (and icon) from PyInstaller bundle or source dir —
if getattr(sys, "_MEIPASS", None):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(base_path, "translations.json"), "r", encoding="utf-8") as f:
    ALL_TX = json.load(f)

def t(key: str) -> str:
    return ALL_TX.get(current_lang, ALL_TX["en"]).get(key, key)

def disable_maximize(hwnd):
    GWL_STYLE      = -16
    WS_MAXIMIZEBOX = 0x00010000
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
    style &= ~WS_MAXIMIZEBOX
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style)

def change_language(new_lang: str):
    global current_lang
    current_lang = new_lang
    status_lbl.configure(text=t("status_active"))

    # static labels
    label_language.configure(text=t("settings_language"))
    label_theme.configure(text=t("settings_theme"))
    label_startup.configure(text=t("settings_startup"))
    label_minimize.configure(text=t("settings_start_minimized"))

    # language menu
    lv = [ALL_TX[c][f"lang_{c}"] for c in ALL_TX]
    lang_menu.configure(values=lv)
    lang_menu.set(ALL_TX[current_lang][f"lang_{current_lang}"])

    # theme selector
    theme_vals = [t("theme_Light"), t("theme_Dark"), t("theme_Auto")]
    theme_menu.configure(values=theme_vals)
    cm = ctk.get_appearance_mode()
    theme_menu.set(t(f"theme_{cm if cm in ('Light','Dark') else 'Auto'}"))

    # startup selector
    startup_vals = [t("startup_on"), t("startup_off")]
    startup_menu.configure(values=startup_vals)
    startup_menu.set(t("startup_on") if is_in_startup() else t("startup_off"))

    # minimize selector
    min_vals = [t("minimize_on"), t("minimize_off")]
    minimize_menu.configure(values=min_vals)
    minimize_menu.set(t("minimize_on") if get_start_minimized() else t("minimize_off"))

def on_theme_change(selection: str):
    rev = {
        t("theme_Light"): "Light",
        t("theme_Dark"):  "Dark",
        t("theme_Auto"):  "System"
    }
    ctk.set_appearance_mode(rev.get(selection, "System"))

def on_startup_change(selection: str):
    if selection == t("startup_on"):
        add_to_startup()
    else:
        remove_from_startup()

def on_minimize_change(selection: str):
    if selection == t("minimize_on"):
        set_start_minimized(True)
        root.after(0, root.iconify)
    else:
        set_start_minimized(False)

def on_close():
    allow_sleep()
    root.destroy()

def toggle_settings():
    if settings_frame.winfo_viewable():
        settings_frame.grid_remove()
    else:
        settings_frame.grid()

if __name__ == "__main__":
    prevent_sleep()
    current_lang = get_system_lang()

    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    # load icon if present
    icon_path = os.path.join(base_path, "app.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    root.title("Prevent Sleep")
    root.geometry("400x200")
    root.resizable(True, True)

    # disable maximize button
    hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
    disable_maximize(hwnd)

    # start minimized if set
    if get_start_minimized():
        root.after(0, root.iconify)

    # top toolbar with hamburger
    toolbar = ctk.CTkFrame(root, height=40)
    toolbar.pack(fill="x", side="top", padx=5, pady=5)
    menu_btn = ctk.CTkButton(
        toolbar, text="☰", width=30, height=30,
        fg_color="transparent", hover_color=None,
        command=toggle_settings
    )
    menu_btn.pack(side="left")

    # body layout
    body = ctk.CTkFrame(root)
    body.pack(fill="both", expand=True, padx=5, pady=(0,5))
    body.columnconfigure(1, weight=1)
    body.rowconfigure(0, weight=1)

    # settings pane (hidden by default)
    settings_frame = ctk.CTkScrollableFrame(master=body, corner_radius=10, width=180)
    settings_frame.grid(row=0, column=0, sticky="ns", padx=(0,5))
    settings_frame.grid_remove()

    # Language
    label_language = ctk.CTkLabel(settings_frame, text=t("settings_language"), anchor="w")
    label_language.pack(fill="x", padx=10, pady=(10,0))
    lang_vals = [ALL_TX[c][f"lang_{c}"] for c in ALL_TX]
    lang_menu = ctk.CTkOptionMenu(
        settings_frame, values=lang_vals,
        command=lambda v: change_language(list(ALL_TX.keys())[lang_vals.index(v)]),
        width=150, dynamic_resizing=False
    )
    lang_menu.pack(fill="x", padx=10, pady=(0,10))
    lang_menu.set(ALL_TX[current_lang][f"lang_{current_lang}"])

    # Theme
    label_theme = ctk.CTkLabel(settings_frame, text=t("settings_theme"), anchor="w")
    label_theme.pack(fill="x", padx=10)
    theme_menu = ctk.CTkSegmentedButton(
        settings_frame,
        values=[t("theme_Light"), t("theme_Dark"), t("theme_Auto")],
        command=on_theme_change
    )
    theme_menu.pack(fill="x", padx=10, pady=(0,10))
    cm = ctk.get_appearance_mode()
    theme_menu.set(t(f"theme_{cm if cm in ('Light','Dark') else 'Auto'}"))

    # Startup
    label_startup = ctk.CTkLabel(settings_frame, text=t("settings_startup"), anchor="w")
    label_startup.pack(fill="x", padx=10)
    startup_menu = ctk.CTkSegmentedButton(
        settings_frame,
        values=[t("startup_on"), t("startup_off")],
        command=on_startup_change
    )
    startup_menu.pack(fill="x", padx=10, pady=(0,10))
    startup_menu.set(t("startup_on") if is_in_startup() else t("startup_off"))

    # Start Minimized
    label_minimize = ctk.CTkLabel(settings_frame, text=t("settings_start_minimized"), anchor="w")
    label_minimize.pack(fill="x", padx=10)
    minimize_menu = ctk.CTkSegmentedButton(
        settings_frame,
        values=[t("minimize_on"), t("minimize_off")],
        command=on_minimize_change
    )
    minimize_menu.pack(fill="x", padx=10, pady=(0,10))
    minimize_menu.set(t("minimize_on") if get_start_minimized() else t("minimize_off"))

    # content area
    content = ctk.CTkFrame(master=body, fg_color="transparent")
    content.grid(row=0, column=1, sticky="nsew")
    status_lbl = ctk.CTkLabel(
        content, text=t("status_active"),
        font=ctk.CTkFont(size=16), justify="center"
    )
    status_lbl.place(relx=0.5, rely=0.5, anchor="center")

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
