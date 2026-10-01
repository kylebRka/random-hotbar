"""Liquid Glass inspired materials with readable light and dark palettes."""
import sys
from tkinter import font as tkfont

PALETTES = {
    "Light": {
        "bg": "#eaf0f8", "card": "#f7f9fd", "fg": "#172034",
        "muted": "#667286", "accent": "#007aff", "accent_hover": "#228bff",
        "on_accent": "#ffffff", "border": "#d8e0ed", "hover": "#e8f0fe",
        "field": "#e8eef7", "disabled": "#dfe6ef", "selected": "#ffffff",
        "shadow": "#d6dfed", "nav": "#dfe7f3",
        "nav_hover": "#edf2fa", "slot_border": "#d0dced",
    },
    "Dark": {
        "bg": "#171d2b", "card": "#272f40", "fg": "#f3f5fc",
        "muted": "#a5afc3", "accent": "#0a84ff", "accent_hover": "#409eff",
        "on_accent": "#ffffff", "border": "#4a556d", "hover": "#35425a",
        "field": "#343e52", "disabled": "#30394c", "selected": "#414d65",
        "shadow": "#101624", "nav": "#212a3c",
        "nav_hover": "#354059", "slot_border": "#4c5870",
    },
}


def interface_font(root):
    available = set(tkfont.families(root))
    preferred = ("Segoe UI Variable", "Segoe UI", "Arial") if sys.platform == "win32" else ("SF Pro Text", "Helvetica Neue", "Arial")
    return next((name for name in preferred if name in available), "TkDefaultFont")


def apply_theme(root, style, name, system_bg):
    if name == "System":
        name = "Dark" if sum(root.winfo_rgb(system_bg)) / 3 < 32768 else "Light"
    c = dict(PALETTES[name], font=interface_font(root))
    root.configure(bg=c["bg"])
    # Tk 9 no longer consistently exposes the private ttk::currentTheme
    # variable used by older Python versions of Style.theme_use().
    if root.tk.call("ttk::style", "theme", "use") != "clam":
        style.theme_use("clam")
    style.configure("TFrame", background=c["bg"])
    style.configure("TLabel", background=c["bg"], foreground=c["fg"], font=(c["font"], 12))
    style.configure("Title.TLabel", font=(c["font"], 28, "bold"))
    style.configure("Muted.TLabel", foreground=c["muted"], font=(c["font"], 11))
    style.configure("Eyebrow.TLabel", foreground=c["accent"], font=(c["font"], 10, "bold"))
    style.configure("Card.TLabel", background=c["card"])
    style.configure("CardMuted.TLabel", background=c["card"], foreground=c["muted"], font=(c["font"], 11))
    style.configure("CardTitle.TLabel", background=c["card"], font=(c["font"], 14, "bold"))
    return c
