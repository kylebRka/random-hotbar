"""Regression coverage for switching themes with Tk 9 and older Tkinter."""
import unittest

try:
    import tkinter as tk
except ImportError:
    tk = None


@unittest.skipIf(tk is None, "This Python build does not include Tkinter")
class ThemeTests(unittest.TestCase):
    def test_switching_without_private_current_theme_variable(self):
        from random_hotbar.ui.app import HotbarApp
        from random_hotbar.ui.themes import PALETTES

        app = HotbarApp()
        errors = []
        app.report_callback_exception = lambda *error: errors.append(error)
        try:
            app.update()
            # Reproduce the user's Tk 9 state without relying on its occurrence
            # in a particular Python/Tk patch version.
            app.tk.call("unset", "-nocomplain", "::ttk::currentTheme")
            for name in ("Светлая", "Тёмная", "Системная", "Светлая", "Тёмная"):
                with self.subTest(theme=name):
                    app.theme.set(name)
                    app.update()
                    self.assertEqual(errors, [])
                    self.assertEqual(app.tk.call("ttk::style", "theme", "use"), "clam")
                    if name in PALETTES:
                        self.assertEqual(app.cget("bg"), PALETTES[name]["bg"])
                        self.assertEqual(app.style.lookup("TLabel", "foreground"), PALETTES[name]["fg"])
                    for panel in app.panels:
                        self.assertEqual(panel.content.cget("bg"), app.colors["card"])
                    self.assertEqual(app.start_button.colors, app.colors)
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()
