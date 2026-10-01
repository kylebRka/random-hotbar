"""Application entry point with a useful message for missing Tkinter."""


def main():
    try:
        from .ui.app import HotbarApp
    except ModuleNotFoundError as error:
        if error.name not in ("tkinter", "_tkinter"):
            raise
        raise SystemExit(
            "This Python build does not include Tkinter. Use Python with Tcl/Tk.\n"
            "Check: python3 -m tkinter. See README.md for setup instructions."
        ) from None
    HotbarApp().mainloop()


if __name__ == "__main__":
    main()
