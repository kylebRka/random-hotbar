"""Display helpers for the published macOS version."""


def prepare_display():
    """macOS handles Retina scaling through Tk."""


def display_scale(root):
    return 1.0


def px(widget, value):
    return round(value * getattr(widget.winfo_toplevel(), "ui_scale", 1.0))
