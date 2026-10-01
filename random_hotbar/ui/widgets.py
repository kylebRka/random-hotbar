"""Rounded surfaces and keyboard-operable canvas buttons, without extra dependencies."""
import math
import tkinter as tk
from tkinter import ttk
from .platform import px


def rounded_rect(canvas, x1, y1, x2, y2, radius=16, **kwargs):
    """One continuous contour avoids seams between separately drawn corners."""
    if x2 <= x1 or y2 <= y1:
        return
    r = min(radius,(x2-x1)/2,(y2-y1)/2)
    points=[]
    for cx,cy,start in ((x1+r,y1+r,180),(x2-r,y1+r,270),
                        (x2-r,y2-r,0),(x1+r,y2-r,90)):
        for step in range(13):
            angle=math.radians(start+step*90/12)
            points.extend((cx+r*math.cos(angle),cy+r*math.sin(angle)))
    kwargs.setdefault("fill", "")
    kwargs.setdefault("outline", "")
    return canvas.create_polygon(points,smooth=False,**kwargs)


def rounded_surface(canvas, box, colors, radius=22, fill=None, tag="surface"):
    """A matte, continuous surface without highlight strips or gradient bands."""
    x1,y1,x2,y2=box
    if x2<=x1 or y2<=y1:
        return
    rounded_rect(canvas,x1,y1+2,x2,y2+2,radius,fill=colors["shadow"],tags=tag)
    rounded_rect(canvas,x1,y1,x2,y2,radius,fill=fill or colors["card"],
                 outline=colors["border"],tags=tag)


class RoundedPanel(tk.Canvas):
    def __init__(self, master, height, padding=22):
        super().__init__(master, height=px(master,height), highlightthickness=0, bd=0)
        self.padding = px(master,padding)
        self.colors = None
        self.content = tk.Frame(self, bd=0)
        self.window = self.create_window(self.padding, self.padding, window=self.content, anchor="nw")
        self.bind("<Configure>", self._resize)

    def set_palette(self, colors):
        self.colors = colors
        self.configure(bg=colors["bg"])
        self.content.configure(bg=colors["card"])
        self._resize()

    def _resize(self, event=None):
        if not self.colors:
            return
        width, height = self.winfo_width(), self.winfo_height()
        self.delete("surface")
        rounded_surface(self, (3, 2, width - 3, height - 5), self.colors,
                      radius=px(self,24), tag="surface")
        self.tag_lower("surface")
        self.itemconfigure(self.window, width=max(1, width - self.padding * 2),
                           height=max(1, height - self.padding * 2))


class ActionButton(tk.Canvas):
    def __init__(self, master, text, command, primary=False, width=200, height=52, compact=False):
        super().__init__(master, width=px(master,width), height=px(master,height), bd=0, highlightthickness=0,
                         takefocus=True, cursor="hand2")
        self.text, self.command, self.primary = text, command, primary
        self.colors = None
        self.compact = compact
        self.selected = False
        self.hover = False
        self.bind("<Configure>", lambda _: self.redraw())
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Button-1>", lambda _: self.focus_set())
        self.bind("<ButtonRelease-1>", self._invoke)
        self.bind("<Return>", self._invoke)
        self.bind("<space>", self._invoke)
        self.bind("<FocusIn>", lambda _: self.redraw())
        self.bind("<FocusOut>", lambda _: self.redraw())

    def configure(self, cnf=None, **kwargs):
        result = super().configure(cnf, **kwargs)
        if hasattr(self, "colors"):
            self.redraw()
        return result

    config = configure

    def set_palette(self, colors):
        self.colors = colors
        self.configure(bg=colors["nav"] if self.compact else colors["bg"])

    def _enter(self, _):
        self.hover = True
        self.redraw()

    def _leave(self, _):
        self.hover = False
        self.redraw()

    def _invoke(self, event):
        if str(self.cget("state")) == "disabled":
            return
        if event.type == tk.EventType.ButtonRelease and not (
            0 <= event.x < self.winfo_width() and 0 <= event.y < self.winfo_height()
        ):
            return
        self.command()
        return "break"

    def redraw(self):
        if not self.colors:
            return
        c = self.colors
        disabled = str(self.cget("state")) == "disabled"
        fill = c["accent_hover" if self.hover else "accent"] if self.primary else c["hover" if self.hover else "card"]
        fg = c["on_accent"] if self.primary else c["fg"]
        if disabled:
            fill, fg = c["disabled"], c["muted"]
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        if self.compact:
            fill = c["card"] if self.selected else c["nav_hover"] if self.hover else c["nav"]
            fg = c["fg"] if self.selected else c["muted"]
            if self.selected or self.hover:
                rounded_surface(self,(2,2,width-2,height-3),c,radius=height/2-3,fill=fill)
        else:
            rounded_surface(self,(2,2,width-2,height-4),c,radius=height/2-3,fill=fill)
        if self.focus_get() is self and not disabled:
            rounded_rect(self,2,2,width-2,height-4,height/2-3,outline=c["fg"] if self.primary else c["accent"],width=2)
        self.create_text(width/2,height/2-1,text=self.text,fill=fg,
                         font=(c["font"],11 if self.compact else 13,"bold" if self.primary or self.selected else "normal"))


class ScrollablePage(ttk.Frame):
    """Keep page content usable on Windows laptops and at larger display scales."""
    def __init__(self,master):
        super().__init__(master)
        self.canvas=tk.Canvas(self,highlightthickness=0,bd=0)
        self.overflow=False
        self.canvas.pack(side="left",fill="both",expand=True)
        self.content=ttk.Frame(self.canvas)
        self.window=self.canvas.create_window(0,0,window=self.content,anchor="nw")
        self.canvas.bind("<Configure>",self._layout)
        self.canvas.bind("<Next>",lambda _:self.canvas.yview_scroll(1,"pages"))
        self.canvas.bind("<Prior>",lambda _:self.canvas.yview_scroll(-1,"pages"))
        self.content.bind("<Configure>",self._layout)
        self.winfo_toplevel().bind("<MouseWheel>",self._wheel,add="+")

    def _layout(self,event=None):
        width=self.canvas.winfo_width()
        if int(float(self.canvas.itemcget(self.window,"width") or 0)) != width:
            self.canvas.itemconfigure(self.window,width=width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.overflow=self.content.winfo_reqheight()>self.canvas.winfo_height()+1
        if not self.overflow:
            self.canvas.yview_moveto(0)

    def _wheel(self,event):
        if not self.winfo_ismapped() or not self.overflow:
            return
        widget=event.widget
        while widget is not None and widget is not self:
            widget=getattr(widget,"master",None)
        if widget is self:
            delta=event.delta
            amount=-int(delta/120) if abs(delta)>=120 else (-1 if delta>0 else 1)
            self.canvas.yview_scroll(amount,"units")
            return "break"

    def set_palette(self,colors):
        self.canvas.configure(bg=colors["bg"])


class RoundedNavigation(tk.Canvas):
    """A single rounded capsule, with arrow-key navigation and no opaque seams."""
    def __init__(self,master,names,command,label=None):
        super().__init__(master,height=px(master,52),highlightthickness=0,bd=0,
                         takefocus=True,cursor="hand2")
        self.label=label or (lambda name: name)
        self.names=tuple(names)
        self.command=command
        self.selected=self.names[0]
        self.colors=None
        self.hover=None
        self.bind("<Configure>",lambda _:self.redraw())
        self.bind("<Motion>",self._hover)
        self.bind("<Leave>",self._leave)
        self.bind("<ButtonRelease-1>",self._click)
        self.bind("<Left>",lambda _:self._step(-1))
        self.bind("<Right>",lambda _:self._step(1))
        self.bind("<FocusIn>",lambda _:self.redraw())
        self.bind("<FocusOut>",lambda _:self.redraw())

    def _hover(self,event):
        index=min(len(self.names)-1,max(0,int(event.x/max(1,self.winfo_width())*len(self.names))))
        if index!=self.hover:
            self.hover=index
            self.redraw()

    def _leave(self,event):
        self.hover=None
        self.redraw()

    def _click(self,event):
        if not (0<=event.x<self.winfo_width() and 0<=event.y<self.winfo_height()):
            return
        self.focus_set()
        self.command(self.names[min(len(self.names)-1,int(event.x/self.winfo_width()*len(self.names)))])

    def _step(self,amount):
        self.command(self.names[(self.names.index(self.selected)+amount)%len(self.names)])
        return "break"

    def set_palette(self,colors):
        self.colors=colors
        self.configure(bg=colors["bg"])
        self.redraw()

    def redraw(self):
        if not self.colors:
            return
        c=self.colors
        width,height=self.winfo_width(),self.winfo_height()
        self.delete("all")
        rounded_surface(self,(2,2,width-2,height-4),c,radius=height/2-3,fill=c["nav"])
        inset=px(self,5)
        part=(width-2*inset)/len(self.names)
        for i,name in enumerate(self.names):
            selected=name==self.selected
            x=inset+i*part
            if selected or i==self.hover:
                rounded_surface(self,(x,inset,x+part,height-inset-2),c,
                              radius=height/2-inset-2,fill=c["card"] if selected else c["nav_hover"])
            if selected and self.focus_get() is self:
                rounded_rect(self,x,inset,x+part,height-inset-2,height/2-inset-2,
                             fill="",outline=c["accent"],width=1)
            self.create_text(x+part/2,height/2-1,text=self.label(name),fill=c["fg"] if selected else c["muted"],
                             font=(c["font"],12,"bold" if selected else "normal"))


class RoundCheckbutton(tk.Canvas):
    """Circular checkbox, with keyboard focus and the same state API as buttons."""
    def __init__(self,master,text,variable):
        super().__init__(master,width=px(master,320),height=px(master,28),
                         highlightthickness=0,bd=0,takefocus=True,cursor="hand2")
        self.text=text
        self.variable=variable
        self.colors=None
        self.variable.trace_add("write",lambda *_:self.redraw())
        self.bind("<ButtonRelease-1>",self._toggle)
        self.bind("<space>",self._toggle)
        self.bind("<Return>",self._toggle)
        self.bind("<Configure>",lambda _:self.redraw())
        self.bind("<FocusIn>",lambda _:self.redraw())
        self.bind("<FocusOut>",lambda _:self.redraw())

    def configure(self,cnf=None,**kwargs):
        if "state" in kwargs:
            kwargs["takefocus"]=kwargs["state"]!="disabled"
        result=super().configure(cnf,**kwargs)
        if hasattr(self,"colors"):
            self.redraw()
        return result

    config=configure

    def _toggle(self,event=None):
        if str(self.cget("state"))!="disabled":
            self.focus_set()
            self.variable.set(not self.variable.get())
        return "break"

    def set_palette(self,colors):
        self.colors=colors
        self.configure(bg=colors["card"])

    def redraw(self):
        if not self.colors:
            return
        c=self.colors
        disabled=str(self.cget("state"))=="disabled"
        selected=self.variable.get()
        self.delete("all")
        size=px(self,20)
        top=(self.winfo_height()-size)/2
        fill=c["disabled"] if disabled else c["accent"] if selected else c["field"]
        self.create_oval(px(self,2),top,px(self,2)+size,top+size,fill=fill,
                         outline=c["accent"] if self.focus_get() is self else c["slot_border"],width=1)
        if selected:
            self.create_line(px(self,7),top+size*.52,px(self,11),top+size*.7,
                             px(self,17),top+size*.34,fill=c["muted"] if disabled else c["on_accent"],
                             width=px(self,2),capstyle="round",joinstyle="round")
        self.create_text(px(self,32),self.winfo_height()/2,text=self.text,anchor="w",
                         fill=c["muted"] if disabled else c["fg"],font=(c["font"],12))
