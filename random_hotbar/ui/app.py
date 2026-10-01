"""Application window. Only the main thread reads or updates Tk widgets."""
import queue
import time
import tkinter as tk
from tkinter import messagebox, ttk

from .. import __version__
from ..backends import create_backend
from ..config import RunConfig, SPEEDS
from ..runner import HotbarRunner
from .themes import apply_theme
from .widgets import ActionButton, RoundedPanel, ScrollablePage, RoundedNavigation, RoundCheckbutton, rounded_surface
from .platform import display_scale, prepare_display, px
from .fields import RoundedField


class HotbarApp(tk.Tk):
    def __init__(self):
        prepare_display()
        super().__init__()
        self.title(f"Random Hotbar · {__version__}")
        self.ui_scale = display_scale(self)
        width = min(px(self,700), self.winfo_screenwidth()-px(self,48))
        height = min(px(self,820), self.winfo_screenheight()-px(self,100))
        self.geometry(f"{width}x{height}")
        self.minsize(min(px(self,660),width), min(px(self,620),height))
        self.system_bg = self.cget("bg")
        self.style = ttk.Style(self)
        self.runner = HotbarRunner()
        self.pending = False
        self.deadline = 0.0
        self.theme = tk.StringVar(value="Light")
        self.slots = tk.StringVar(value="9")
        self.speed = tk.StringVar(value="Fast")
        self.bias = tk.BooleanVar(value=False)
        self.priority = tk.StringVar(value="1")
        self.chance = tk.StringVar(value="40")
        self.delay = tk.StringVar(value="3")
        self.status = tk.StringVar(value="Ready to build")
        self.controls = []
        self.panels = []
        self.fields = []
        self.colors = None
        self.last_key = None
        self._ui_active = None
        self._build_ui()
        self.theme.trace_add("write", self._theme_changed)
        for variable in (self.slots, self.bias, self.priority):
            variable.trace_add("write", self._draw_hotbar)
        self._theme_changed()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._poll_id = self.after(80, self._poll)

    def _build_ui(self):
        outer = ttk.Frame(self, padding=(px(self,28), px(self,22)))
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0,weight=1)
        outer.rowconfigure(2,weight=1)
        heading = ttk.Frame(outer)
        heading.grid(row=0,column=0,sticky="ew")
        ttk.Label(heading, text="FOR YOUR NEXT BUILD", style="Eyebrow.TLabel").pack(anchor="w")
        ttk.Label(heading, text="Random Hotbar", style="Title.TLabel").pack(anchor="w", pady=(4, 0))
        ttk.Label(heading, text="A little randomness. Richer textures.", style="Muted.TLabel").pack(anchor="w", pady=(2, 0))

        self.pages = {}
        names=("Randomizer","Settings","Help")
        self.navigation=RoundedNavigation(outer,names,self._show_page)
        self.navigation.grid(row=1,column=0,sticky="ew",pady=(px(self,18),px(self,16)))
        self.page_host = ttk.Frame(outer)
        self.page_host.grid(row=2,column=0,sticky="nsew")
        for name in names:
            self.pages[name]=ScrollablePage(self.page_host)
        play, settings, help_page = (page.content for page in self.pages.values())

        preview = self._panel(play, 156)
        ttk.Label(preview, text="HOTBAR", style="CardMuted.TLabel").pack(anchor="w")
        self.hotbar = tk.Canvas(preview, height=px(self,58), highlightthickness=0, bd=0)
        self.hotbar.pack(fill="x", pady=(9, 5))
        self.hotbar.bind("<Configure>", self._draw_hotbar)
        ttk.Label(preview, text="The highlighted slot is the last key pressed", style="CardMuted.TLabel").pack(anchor="w")

        parameters = self._panel(play, 240)
        ttk.Label(parameters, text="Your building rhythm", style="CardTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self._field(parameters, 1, "Number of slots", self.slots, 2, 9)
        self._field(parameters, 2, "Switching speed", self.speed, values=tuple(SPEEDS))
        self._field(parameters, 3, "Start delay, seconds", self.delay, 0, 30)

        priority = self._panel(play, 64, padding=18)
        priority.master.pack_configure(pady=0)
        priority.columnconfigure(0, weight=1)
        bias = RoundCheckbutton(priority,text="Priority key",variable=self.bias)
        self.bias_control=bias
        bias.grid(row=0, column=0, sticky="w")
        self.controls.append((bias, "normal"))
        self.priority_summary = ttk.Label(priority, style="CardMuted.TLabel")
        self.priority_summary.grid(row=0, column=1, sticky="e")
        self.chance.trace_add("write", self._draw_hotbar)

        actions = ttk.Frame(outer)
        actions.grid(row=3,column=0,sticky="ew",pady=(px(self,12),0))
        self.start_button = ActionButton(actions, "Start shuffling", self._start, primary=True, width=380)
        self.start_button.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.stop_button = ActionButton(actions, "Stop", self._stop, width=170)
        self.stop_button.pack(side="right")
        self.stop_button.configure(state="disabled")

        preferences = self._panel(settings, 260)
        ttk.Label(preferences, text="Make it your own", style="CardTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))
        self._field(preferences, 1, "Priority key", self.priority, values=tuple("123456789"))
        self._field(preferences, 2, "Selection chance, %", self.chance, 0, 100)
        self._field(preferences, 3, "Appearance", self.theme, values=("Dark", "Light", "System"), lock=False)
        explanation = self._panel(settings, 154)
        ttk.Label(explanation, text="How priority works", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 10))
        ttk.Label(explanation, text="At 40%, the priority key gets 40% of all presses.\nThe other keys share the remaining 60% equally.\nChoose a key within your slot range and enable priority\non the Randomizer tab.", style="CardMuted.TLabel", justify="left").pack(anchor="w")
        ttk.Label(settings, text="Settings last until you close the app.", style="Muted.TLabel").pack(anchor="w", pady=8)

        guide = self._panel(help_page, 310)
        ttk.Label(guide, text="From blocks to beautiful textures", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 16))
        for number, title, detail in (
            ("01", "Build a palette", "Place your blocks in the first hotbar slots."),
            ("02", "Find your rhythm", "Choose your slot count, speed, and priority."),
            ("03", "Start building", "Press Start and switch to the game during the countdown."),
            ("04", "Stop when you are done", "Return to the app and press Stop."),
        ):
            row = tk.Frame(guide)
            row.pack(fill="x", pady=(0, 12))
            self.help_rows = getattr(self, "help_rows", []) + [row]
            ttk.Label(row, text=number, style="CardTitle.TLabel", width=4).pack(side="left", anchor="n")
            text = tk.Frame(row)
            text.pack(side="left", fill="x", expand=True)
            self.help_rows.append(text)
            ttk.Label(text, text=title, style="Card.TLabel").pack(anchor="w")
            ttk.Label(text, text=detail, style="CardMuted.TLabel").pack(anchor="w")
        notes = self._panel(help_page, 156)
        ttk.Label(notes, text="Good to know", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 10))
        ttk.Label(notes, text="Keys go to the active window. There is no global\nstop shortcut; closing the app stops the loop.\n\nUses keys 1–9 on the top row of your keyboard.",
                  style="CardMuted.TLabel", justify="left").pack(anchor="w")

        footer = ttk.Frame(outer)
        footer.grid(row=4,column=0,sticky="ew",pady=(px(self,14),0))
        self.status_dot = tk.Canvas(footer, width=px(self,12), height=px(self,12), highlightthickness=0)
        self.status_dot.pack(side="left", padx=(0, 8))
        ttk.Label(footer, textvariable=self.status, style="Muted.TLabel").pack(side="left")
        ttk.Label(footer, text=f"v{__version__}", style="Muted.TLabel").pack(side="right")
        self._show_page("Randomizer")
        self._scale_spacing(self.page_host)

    def _panel(self, parent, height, padding=18):
        panel = RoundedPanel(parent, height, padding)
        panel.pack(fill="x", pady=(0, 12))
        self.panels.append(panel)
        return panel.content

    def _show_page(self, name):
        for key, page in self.pages.items():
            page.pack_forget()

        self.pages[name].pack(fill="both", expand=True)
        self.navigation.selected=name
        self.navigation.redraw()

    def _scale_spacing(self, widget):
        # Fonts are DPI-scaled by Tk; scale the explicit layout distances too.
        if self.ui_scale != 1:
            manager=widget.winfo_manager()
            if manager in ("pack","grid"):
                info=widget.pack_info() if manager=="pack" else widget.grid_info()
                options={}
                for name in ("padx","pady"):
                    raw=info.get(name,0)
                    values=raw if isinstance(raw,(tuple,list)) else self.tk.splitlist(str(raw))
                    options[name]=tuple(px(self,int(float(value))) for value in values)
                if manager=="pack":
                    widget.pack_configure(**options)
                else:
                    widget.grid_configure(**options)
        for child in widget.winfo_children():
            self._scale_spacing(child)

    def _field(self, parent, row, label, variable, lower=None, upper=None, values=None, lock=True):
        parent.columnconfigure(0, weight=1)
        ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=6, padx=(0, 12))
        widget=RoundedField(parent,variable,lower,upper,values)
        self.fields.append(widget)
        state="readonly" if values is not None else "normal"
        widget.grid(row=row, column=1, sticky="e", pady=6)
        if lock:
            self.controls.append((widget, state))

    def _theme_changed(self, *_):
        self.colors = apply_theme(self, self.style, self.theme.get(), self.system_bg)
        for panel in self.panels:
            panel.set_palette(self.colors)
        for field in self.fields:
            field.set_palette(self.colors)
        self.bias_control.set_palette(self.colors)
        self.navigation.set_palette(self.colors)
        for page in self.pages.values():
            page.set_palette(self.colors)
        for row in self.help_rows:
            row.configure(bg=self.colors["card"])
        for button in (self.start_button, self.stop_button):
            button.set_palette(self.colors)
        self._draw_hotbar()
        self._draw_status()

    def _draw_hotbar(self, *_):
        if not self.colors:
            return
        c = self.colors
        self.hotbar.configure(bg=c["card"])
        self.hotbar.delete("all")
        try:
            count = max(2, min(9, int(self.slots.get())))
        except ValueError:
            count = 9
        width = self.hotbar.winfo_width()
        gap = px(self,8)
        size = min(px(self,48), (width - 8 * gap) / 9)
        left = (width - (9 * size + 8 * gap)) / 2
        if size > 0:
            for i, key in enumerate("123456789"):
                x = left + i * (size + gap)
                active = i < count
                selected = active and self.last_key == key
                priority = active and self.bias.get() and self.priority.get() == key
                slot_colors=dict(c,border=c["accent"] if priority else c["slot_border"])
                rounded_surface(self.hotbar,(x,px(self,4),x+size,px(self,4)+size),slot_colors,
                              radius=px(self,14),fill=c["accent"] if selected else c["field"] if active else c["card"])
                self.hotbar.create_text(x + size / 2, px(self,4) + size / 2, text=key,
                                        fill=c["on_accent"] if selected else c["fg"] if active else c["muted"],
                                        font=(c["font"], 14, "bold"))
        self.priority_summary.configure(text=f"{self.priority.get()}  ·  {self.chance.get()}%" if self.bias.get() else "Off")

    def _draw_status(self):
        if not self.colors:
            return
        self.status_dot.configure(bg=self.colors["bg"])
        self.status_dot.delete("all")
        self.status_dot.create_oval(px(self,2), px(self,2), px(self,10), px(self,10), outline="", fill=self.colors["accent"] if self.pending else self.colors["muted"])

    def _set_running(self, active):
        if self._ui_active == active:
            return
        self._ui_active = active
        for widget, state in self.controls:
            widget.configure(state="disabled" if active else state)
        self.start_button.configure(state="disabled" if active else "normal")
        self.stop_button.configure(state="normal" if active else "disabled")
        self._draw_status()

    def _start(self):
        if self.pending or self.runner.running:
            return
        try:
            config = RunConfig(
                slots=int(self.slots.get()), speed=self.speed.get(), bias=self.bias.get(),
                priority_key=self.priority.get(), priority_chance=int(self.chance.get()),
                start_delay=int(self.delay.get()),
            )
            backend = create_backend()
        except (ValueError, RuntimeError) as error:
            messagebox.showerror("Could not start", str(error), parent=self)
            return
        if self.runner.start(config, backend):
            self.pending = True
            self.last_key = None
            self._draw_hotbar()
            self.deadline = time.monotonic() + config.start_delay
            self.status.set("Switch to Minecraft…")
            self._set_running(True)

    def _stop(self):
        self.runner.stop()
        if self.pending:
            self.status.set("Stopping…")
            self.stop_button.configure(state="disabled")

    def _poll(self):
        try:
            while True:
                event, value = self.runner.events.get_nowait()
                if event == "started":
                    self.deadline = 0
                    self.status.set("Running · switch to the game")
                elif event == "key":
                    self.last_key = value
                    self._draw_hotbar()
                    self.status.set(f"Running · last key: {value}")
                elif event == "error":
                    messagebox.showerror("Could not send key", value, parent=self)
                elif event == "stopped":
                    # Wait for the old worker to exit before enabling another run.
                    self.pending = False
                    self.deadline = 0
                    self.status.set("Stopped")
        except queue.Empty:
            pass
        if not self.pending and not self.runner.running:
            self._set_running(False)
        elif self.deadline and str(self.stop_button.cget("state")) != "disabled":
            seconds = max(0, int(self.deadline - time.monotonic()) + 1)
            self.status.set(f"Starting in {seconds}s · switch to the game")
        self._poll_id = self.after(80, self._poll)

    def destroy(self):
        if getattr(self,"_poll_id",None) is not None:
            self.after_cancel(self._poll_id)
            self._poll_id=None
        super().destroy()

    def _close(self):
        self.runner.stop()
        # Let a held key be released before destroying the process/window.
        self.withdraw()
        self._finish_close()

    def _finish_close(self):
        if self.runner.running:
            self.after(20, self._finish_close)
        else:
            self.destroy()
