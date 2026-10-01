"""Rounded numeric inputs and dropdowns with keyboard control."""
import tkinter as tk
from .platform import px
from .widgets import rounded_rect


class RoundedField(tk.Canvas):
    def __init__(self, master, variable, lower=None, upper=None, values=None, label=None):
        super().__init__(master, width=px(master,160), height=px(master,40),
                         highlightthickness=0, bd=0, takefocus=bool(values))
        self.label = label or (lambda value: value)
        self.variable = variable
        self.lower, self.upper = lower, upper
        self.values = tuple(values) if values is not None else None
        self.colors = None
        self.enabled = True
        self.hover = False
        self.popup = None
        self._outside_binding = None
        self.entry = None
        if self.values is None:
            self.entry = tk.Entry(self, textvariable=variable, bd=0, highlightthickness=0,
                                  relief="flat", justify="left", exportselection=False)
            self.entry.place(x=px(self,14), rely=.5, anchor="w", width=px(self,76), height=px(self,26))
            self.entry.bind("<Up>", lambda _: self._step(1))
            self.entry.bind("<Down>", lambda _: self._step(-1))
            self.entry.bind("<FocusIn>", lambda _: self.redraw())
            self.entry.bind("<FocusOut>", lambda _: self.redraw())
        else:
            for key in ("<space>", "<Return>", "<Down>"):
                self.bind(key, self._open_popup)
        self.bind("<ButtonRelease-1>", self._click)
        self.bind("<Configure>", lambda _: self.redraw())
        self.bind("<FocusIn>", lambda _: self.redraw())
        self.bind("<FocusOut>", lambda _: self.redraw())
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.variable.trace_add("write", lambda *_: self.redraw())

    def configure(self, cnf=None, **kwargs):
        # Keep the Canvas active so disabled text has controlled styling.
        state = kwargs.pop("state", None)
        if state is not None:
            self.enabled = state != "disabled"
            super().configure(takefocus=self.enabled and self.values is not None)
            if self.entry is not None:
                self.entry.configure(state="normal" if self.enabled else "disabled")
            if not self.enabled:
                self._close_popup()
        result = super().configure(cnf, **kwargs)
        if hasattr(self, "colors"):
            self.redraw()
        return result

    config = configure

    def set_palette(self, colors):
        self._close_popup()
        self.colors = colors
        self.configure(bg=colors["card"])
        if self.entry is not None:
            self.entry.configure(bg=colors["field"], fg=colors["fg"],
                                 disabledbackground=colors["disabled"], disabledforeground=colors["muted"],
                                 insertbackground=colors["fg"], selectbackground=colors["accent"],
                                 selectforeground=colors["on_accent"], font=(colors["font"],12))
        self.redraw()

    def _enter(self, _):
        self.hover = True
        self.redraw()

    def _leave(self, _):
        self.hover = False
        self.redraw()

    def _step(self, direction):
        if not self.enabled:
            return "break"
        try:
            current = int(self.variable.get())
        except ValueError:
            current = self.lower
        self.variable.set(str(max(self.lower,min(self.upper,current+direction))))
        return "break"

    def _click(self, event):
        if not self.enabled:
            return
        if self.values is not None:
            self.focus_set()
            self._open_popup()
        elif event.x > self.winfo_width()-px(self,58):
            self.entry.focus_set()
            self._step(1 if event.x > self.winfo_width()-px(self,30) else -1)
        else:
            self.entry.focus_set()

    def redraw(self):
        if not self.colors:
            return
        c = self.colors
        self.delete("all")
        width,height=self.winfo_width(),self.winfo_height()
        focused=self.focus_get() is self or (self.entry is not None and self.focus_get() is self.entry)
        fill=c["field"] if self.enabled else c["disabled"]
        border=c["accent"] if focused and self.enabled else c["slot_border"] if self.hover else fill
        rounded_rect(self,1,1,width-1,height-1,px(self,12),fill=fill,outline=border,width=1)
        foreground=c["fg"] if self.enabled else c["muted"]
        if self.values is not None:
            self.create_text(px(self,14),height/2,text=self.label(self.variable.get()),anchor="w",fill=foreground,
                             font=(c["font"],12))
            x,y=width-px(self,18),height/2
            self.create_line(x-px(self,4),y-px(self,2),x,y+px(self,2),x+px(self,4),y-px(self,2),
                             fill=c["muted"],width=px(self,2),capstyle="round",joinstyle="round")
        else:
            for offset,symbol in ((44,"−"),(18,"+")):
                x=width-px(self,offset)
                self.create_text(x,height/2,text=symbol,fill=foreground,font=(c["font"],13))
            self.create_line(width-px(self,58),px(self,10),width-px(self,58),height-px(self,10),fill=c["slot_border"])
            if self.entry is not None:
                self.entry.configure(bg=fill)
                self.entry.place_configure(width=max(1,width-px(self,80)))

    def _open_popup(self, event=None):
        if not self.enabled or self.values is None or not self.colors:
            return "break"
        if self.popup is not None:
            self._close_popup()
            return "break"
        c=self.colors
        popup=tk.Toplevel(self)
        self.popup=popup
        popup.withdraw()
        popup.overrideredirect(True)
        popup.transient(self.winfo_toplevel())
        # Tk 9 on macOS can render transparent popup backgrounds as black.
        # Use a normal opaque themed window on both platforms.
        popup_background=c["bg"]
        popup.configure(bg=popup_background)
        row_height=px(self,36)
        margin=px(self,7)
        width=max(self.winfo_width(),px(self,160))
        height=len(self.values)*row_height+margin*2
        x=min(self.winfo_rootx(),self.winfo_screenwidth()-width-px(self,8))
        y=self.winfo_rooty()+self.winfo_height()+px(self,6)
        if y+height>self.winfo_screenheight()-px(self,20):
            y=self.winfo_rooty()-height-px(self,6)
        popup.geometry(f"{width}x{height}+{max(0,x)}+{max(0,y)}")
        menu=tk.Canvas(popup,highlightthickness=0,bd=0,bg=popup_background,takefocus=True)
        menu.pack(fill="both",expand=True)
        selected=self.values.index(self.variable.get()) if self.variable.get() in self.values else 0
        self._popup_index=selected

        def draw():
            menu.delete("all")
            rounded_rect(menu,1,1,width-1,height-1,px(self,14),fill=c["card"],outline=c["slot_border"])
            for i,value in enumerate(self.values):
                top=margin+i*row_height
                if i==self._popup_index:
                    rounded_rect(menu,margin,top,width-margin,top+row_height,px(self,9),fill=c["hover"])
                menu.create_text(px(self,16),top+row_height/2,anchor="w",text=self.label(value),
                                 fill=c["fg"],font=(c["font"],12))
                if value==self.variable.get():
                    menu.create_text(width-px(self,18),top+row_height/2,text="✓",fill=c["accent"],font=(c["font"],12))

        def move(amount):
            self._popup_index=(self._popup_index+amount)%len(self.values)
            draw()
            return "break"

        def choose(event=None):
            value=self.values[self._popup_index]
            self._close_popup()
            self.focus_set()
            self.variable.set(value)
            return "break"

        def hover(event):
            index=int((event.y-margin)/row_height)
            if 0<=index<len(self.values) and index!=self._popup_index:
                self._popup_index=index
                draw()

        def click(event):
            if margin<=event.y<height-margin:
                hover(event)
                choose()

        def outside(event):
            if self.popup is not None and not (x<=event.x_root<x+width and y<=event.y_root<y+height):
                self._close_popup()

        menu.bind("<Motion>",hover)
        menu.bind("<ButtonRelease-1>",click)
        menu.bind("<Up>",lambda _:move(-1))
        menu.bind("<Down>",lambda _:move(1))
        menu.bind("<Return>",choose)
        menu.bind("<space>",choose)
        menu.bind("<Escape>",lambda _:self._dismiss_popup())
        menu.bind("<Tab>",lambda _:self._dismiss_popup(advance=True))
        popup.bind("<FocusOut>",lambda _:self.after_idle(self._close_if_unfocused))
        self._outside_binding=self.winfo_toplevel().bind("<ButtonPress-1>",outside,add="+")
        popup.deiconify()
        popup.lift()
        menu.focus_set()
        draw()
        return "break"

    def _dismiss_popup(self, advance=False):
        self._close_popup()
        self.focus_set()
        if advance:
            self.tk_focusNext().focus_set()
        return "break"

    def _close_if_unfocused(self):
        if self.popup is not None and self.focus_get() not in (self.popup,*self.popup.winfo_children()):
            self._close_popup()

    def _close_popup(self):
        if self._outside_binding is not None:
            self.winfo_toplevel().unbind("<ButtonPress-1>",self._outside_binding)
            self._outside_binding=None
        if self.popup is not None:
            popup,self.popup=self.popup,None
            popup.destroy()
        self.redraw()
