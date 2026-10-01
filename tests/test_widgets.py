"""UI regressions: borders, rounded inputs and dropdown interaction."""
import unittest
from unittest.mock import Mock

try:
    import tkinter as tk
except ImportError:
    tk=None


@unittest.skipIf(tk is None,"This Python build does not include Tkinter")
class DrawingTests(unittest.TestCase):
    def test_outline_has_no_implicit_black_fill(self):
        from random_hotbar.ui.widgets import rounded_rect
        canvas=Mock()
        rounded_rect(canvas,0,0,100,40,12,outline="#ffffff")
        self.assertEqual(canvas.create_polygon.call_args.kwargs["fill"],"")


@unittest.skipIf(tk is None,"This Python build does not include Tkinter")
class FieldTests(unittest.TestCase):
    def setUp(self):
        from random_hotbar.ui.app import HotbarApp
        self.app=HotbarApp()
        self.errors=[]
        self.app.report_callback_exception=lambda *error:self.errors.append(error)
        self.app.update()

    def tearDown(self):
        for field in self.app.fields:
            field._close_popup()
        self.app.destroy()

    def test_language_switch_keeps_values_page_and_active_state(self):
        from random_hotbar.config import RunConfig
        self.assertEqual(self.app.language.get(), "en")
        self.app.slots.set("7")
        self.app.speed.set("Medium")
        self.app.theme.set("Dark")
        self.app._show_page("Settings")
        self.app.pending = True
        self.app._set_running(True)
        self.app._set_status("Running · last key: {key}", key="7")
        self.app._toggle_language()
        self.app.update()
        self.assertEqual(self.app.start_button.text, "Начать перемешивание")
        self.assertEqual(self.app.status.get(), "Работает · последняя клавиша: 7")
        self.assertEqual(self.app.speed.get(), "Medium")
        self.assertEqual(self.app.theme.get(), "Dark")
        self.assertEqual(self.app.slots.get(), "7")
        self.assertEqual(self.app.navigation.selected, "Settings")
        self.assertEqual(str(self.app.start_button.cget("state")), "disabled")
        self.assertEqual(RunConfig(speed=self.app.speed.get()).speed, "Medium")
        self.app._toggle_language()
        self.assertEqual(self.app.start_button.text, "Start shuffling")
        self.assertEqual(self.app.status.get(), "Running · last key: 7")
        self.assertTrue(self.app.pending)
        self.assertEqual(self.errors, [])

    def test_russian_dropdown_uses_canonical_values_and_errors(self):
        from random_hotbar.i18n import translate
        self.app._toggle_language()
        field=next(field for field in self.app.fields if field.variable is self.app.speed)
        field._open_popup()
        self.app.update()
        menu=field.popup.winfo_children()[0]
        labels=[menu.itemcget(item,"text") for item in menu.find_all() if menu.type(item)=="text"]
        self.assertIn("Быстро",labels)
        menu.event_generate("<Up>")
        menu.event_generate("<Return>")
        self.assertEqual(self.app.speed.get(),"Medium")
        self.assertEqual(translate("The number of slots must be between 2 and 9.","ru"),
                         "Количество клавиш должно быть от 2 до 9.")
        self.assertEqual(translate("unexpected {error}","ru"),"unexpected {error}")

    def test_numeric_bounds_and_disabled_field(self):
        field=next(field for field in self.app.fields if field.variable is self.app.slots)
        self.app.slots.set("9")
        field._step(1)
        self.assertEqual(self.app.slots.get(),"9")
        self.app.slots.set("2")
        field._step(-1)
        self.assertEqual(self.app.slots.get(),"2")
        field.configure(state="disabled")
        field._step(1)
        self.assertEqual(self.app.slots.get(),"2")
        field.configure(state="normal")
        field._step(1)
        self.assertEqual(self.app.slots.get(),"3")

    def test_dropdown_keyboard_selection_and_theme_change(self):
        field=next(field for field in self.app.fields if field.variable is self.app.speed)
        field._open_popup()
        self.app.update()
        menu=field.popup.winfo_children()[0]
        menu.event_generate("<Up>")
        menu.event_generate("<Return>")
        self.app.update()
        self.assertEqual(self.app.speed.get(),"Medium")
        self.assertIsNone(field.popup)
        field._open_popup()
        self.app.update()
        self.app.theme.set("Dark")
        self.app.update()
        self.assertIsNone(field.popup)
        self.assertEqual(field.colors,self.app.colors)
        self.assertEqual(self.errors,[])

    def test_round_priority_toggle_and_opaque_popup(self):
        control=self.app.bias_control
        control._toggle()
        self.assertTrue(self.app.bias.get())
        control.configure(state="disabled")
        control._toggle()
        self.assertTrue(self.app.bias.get())
        circles=[item for item in control.find_all() if control.type(item)=="oval"]
        self.assertEqual(len(circles),1)
        field=next(field for field in self.app.fields if field.variable is self.app.speed)
        field._open_popup()
        self.app.update()
        self.assertEqual(field.popup.cget("bg"),self.app.colors["bg"])
        menu=field.popup.winfo_children()[0]
        for item in menu.find_all():
            if menu.type(item)=="polygon":
                self.assertNotIn(menu.itemcget(item,"fill"),("black","#000000"))

    def test_dpi_scaling_handles_asymmetric_padding(self):
        self.app.ui_scale=1.5
        self.app._scale_spacing(self.app.page_host)
        self.app.update()
        panel=self.app.panels[0]
        self.assertEqual(int(panel.pack_info()["pady"][1]),18)
        self.assertEqual(self.errors,[])

    def test_small_window_keeps_stop_button_visible_without_scrollbar(self):
        self.app.geometry("660x620")
        self.app._show_page("Help")
        self.app.update()
        page=self.app.pages["Help"]
        self.assertTrue(page.overflow)
        self.assertFalse(any(child.winfo_class()=="TScrollbar" for child in page.winfo_children()))
        self.assertTrue(self.app.stop_button.winfo_ismapped())
        button_bottom=self.app.stop_button.winfo_rooty()+self.app.stop_button.winfo_height()
        self.assertLessEqual(button_bottom,self.app.winfo_rooty()+self.app.winfo_height())


if __name__=="__main__":
    unittest.main()
