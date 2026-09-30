"""Application entry point with a useful message for missing Tkinter."""


def main():
    try:
        from .ui.app import HotbarApp
    except ModuleNotFoundError as error:
        if error.name not in ("tkinter", "_tkinter"):
            raise
        raise SystemExit(
            "В этой сборке Python отсутствует Tkinter. Используйте Python с Tcl/Tk.\n"
            "Проверка: python3 -m tkinter. Инструкции: README.md."
        ) from None
    HotbarApp().mainloop()


if __name__ == "__main__":
    main()
