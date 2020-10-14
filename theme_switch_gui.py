# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 07:24:36 2020

@author: noerg
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk
from theme_switch import light_mode_is_on, change_sys_theme, load_settings, create_task, change_task_state
import yaml
import webbrowser
import os

"""
TODO:
    - What happens if the wallpaper string in settings.yaml is empty?
"""


class Base:
    def __init__(self, parent):
        self.parent = parent
        self.parent.resizable(False, False)
        self.load_theme()

    def set_position(self, w, h):
        """
        Puts the window in the center of the screen.
        
        :param w: width of the window
        :param h: height of the window
        """
        ws = self.parent.winfo_screenwidth()  # Screen width
        hs = self.parent.winfo_screenheight()  # Screen height
        x = (ws / 2) - (w / 2)  # Program x axis
        y = (hs / 2) - (h / 2)  # Program y axis
        self.parent.geometry('{0}x{1}+{2}+{3}'.format(w, h, int(x), int(y)))

    def load_theme(self):
        # Code based on https://stackoverflow.com/a/62934393
        self.parent.tk.eval("""
set base_theme_dir awthemes-9.3.2/

package ifneeded awthemes 9.3.2 \
    [list source [file join $base_theme_dir awthemes.tcl]]
package ifneeded colorutils 4.8 \
    [list source [file join $base_theme_dir colorutils.tcl]]
package ifneeded awdark 7.7 \
    [list source [file join $base_theme_dir awdark.tcl]]
package ifneeded awlight 7.6 \
    [list source [file join $base_theme_dir awlight.tcl]]
                            """)
        self.parent.tk.call("package", "require", "awdark")
        self.parent.tk.call("package", "require", "awlight")


class MainWindow(Base):
    def __init__(self, parent):
        Base.__init__(self, parent)
        self.parent = parent
        self.style = ttk.Style()

        self.img = ImageTk.PhotoImage
        self.canvas = tk.Canvas(self.parent)
        self.action_btn = ttk.Button(self.parent)

        self.initialize_interface()
        Base.set_position(self, 200, 180)
        self.get_active_mode()

    def initialize_interface(self):
        menubar = tk.Menu(self.parent)

        settings_menu = tk.Menu(self.parent, menubar, tearoff=0)
        settings_menu.add_command(label="Settings", command=self.open_settings_window)
        menubar.add_cascade(label="Edit", menu=settings_menu)

        about_menu = tk.Menu(self.parent, menubar, tearoff=0)
        about_menu.add_command(label="About this program",
                               command=self.open_about_window)
        menubar.add_cascade(label="About",
                            menu=about_menu)

        self.canvas.config(width=200,
                           height=150, )
        self.canvas.pack()

        self.action_btn.config(command=self.change_system_mode)
        self.action_btn.pack(fill=tk.BOTH)

        self.parent.config(menu=menubar)

    def get_active_mode(self):
        if light_mode_is_on():
            self.apply_light_theme()
        else:
            self.apply_dark_theme()

    def change_system_mode(self):
        if light_mode_is_on():
            mode = 'dark_mode'
            self.apply_dark_theme()
        else:
            mode = 'light_mode'
            self.apply_light_theme()
        change_sys_theme(**load_settings()[mode])

    def apply_dark_theme(self):
        self.style.theme_use("awdark")
        self.style.configure('TButton',
                             relief=tk.FLAT)
        self.img = ImageTk.PhotoImage(file="moon.png")
        img_on_canvas = self.canvas.create_image(100, 75)
        self.canvas.configure(background='black', highlightbackground='black')
        self.canvas.itemconfig(img_on_canvas, image=self.img)
        self.action_btn.config(text="Dark mode on")

    def apply_light_theme(self):
        self.style.theme_use("awlight")
        self.style.configure('TButton',
                             relief=tk.FLAT)
        self.img = ImageTk.PhotoImage(file="sun.png")
        img_on_canvas = self.canvas.create_image(100, 75)
        self.canvas.configure(background='white', highlightbackground='white')
        self.canvas.itemconfig(img_on_canvas, image=self.img)
        self.action_btn.config(text="Light mode on")

    def open_about_window(self):
        new_window = tk.Toplevel(self.parent)
        new_window.title("About")
        About(new_window)

    def open_settings_window(self):
        new_window = tk.Toplevel(self.parent)
        new_window.title("Settings")
        Settings(new_window)


class Settings(Base):
    def __init__(self, parent):
        Base.__init__(self, parent)
        self.parent = parent

        self.wallpaper_path = tk.StringVar(), tk.StringVar()
        self.brightness_scale = tk.IntVar(), tk.IntVar()
        self.start_hour = tk.StringVar(), tk.StringVar()
        self.start_minute = tk.StringVar(), tk.StringVar()
        self.enable_scheduler = tk.BooleanVar(), tk.BooleanVar()

        tab_control = ttk.Notebook(self.parent)
        self.tabs = {'dark_mode': ttk.Frame(tab_control),
                     'light_mode': ttk.Frame(tab_control)}

        self.preview_canvas = [tk.Canvas(self.tabs['dark_mode']), tk.Canvas(self.tabs['light_mode'])]
        self.spin_state = ["disabled", "disabled"]
        self.spin_hour = [ttk.Spinbox(self.tabs['dark_mode']), ttk.Spinbox(self.tabs['light_mode'])]
        self.spin_minute = [ttk.Spinbox(self.tabs['dark_mode']), ttk.Spinbox(self.tabs['light_mode'])]
        self.wallpaper_tk_thumbnail = [ImageTk.PhotoImage, ImageTk.PhotoImage]

        self.initialize_interface(tab_control)
        Base.set_position(self, 275, 270)

    def initialize_interface(self, tab_control):
        self.read_settings()

        tab_control.add(self.tabs['dark_mode'], text='Dark mode')
        tab_control.add(self.tabs['light_mode'], text='Light mode')
        tab_control.pack(expand=1, fill=tk.BOTH)

        self.create_settings_interface()

    def create_settings_interface(self):
        for i, tab in enumerate(self.tabs):
            ttk.Label(self.tabs[tab],
                      text="Wallpaper",
                      font=("Trebuchet MS", 10),
                      anchor=tk.E).grid(row=0, column=0, sticky="e", padx=5)
            self.preview_canvas[i].config(highlightthickness=0,
                                          width=128, height=64)
            self.preview_canvas[i].bind("<Button-1>",
                                        lambda event, i=i: self.get_wallpaper_path(i))
            self.preview_canvas[i].grid(row=0,
                                        column=1,
                                        columnspan=3,
                                        pady=10)
            self.preview_img_on_canvas(self.wallpaper_path[i].get(), i)

            ttk.Label(self.tabs[tab],
                      text="Brightness",
                      font=("Trebuchet MS", 10)).grid(row=1, column=0, sticky="e", padx=5, pady=5)
            ttk.Scale(self.tabs[tab],
                      from_=0, to=100,
                      orient=tk.HORIZONTAL,
                      variable=self.brightness_scale[i],
                      command=self.whole_values_only).grid(row=1, column=1, columnspan=2, sticky="ew")
            ttk.Spinbox(self.tabs[tab],
                        textvariable=self.brightness_scale[i],
                        from_=0, to=100,
                        increment=1,
                        wrap=True,
                        width=3,
                        state='readonly',
                        format="%02.0f",).grid(row=1, column=3, sticky='e', padx=(10,0))

            ttk.Label(self.tabs[tab],
                      text="Run everyday at:",
                      font=("Trebuchet MS", 10),
                      anchor=tk.E).grid(row=2, column=0, sticky="e", padx=5, pady=2)
            self.spin_hour[i].config(textvariable=self.start_hour[i],
                                     from_=0, to=23,
                                     increment=1, wrap=True,
                                     width=2,
                                     format="%02.0f",
                                     state=self.spin_state[i])
            self.spin_hour[i].grid(row=2, column=1, sticky="e", padx=(0, 2), pady=15)
            self.spin_minute[i].config(textvariable=self.start_minute[i],
                                       from_=0, to=59,
                                       increment=1, wrap=True,
                                       width=2,
                                       format="%02.0f",
                                       state=self.spin_state[i])
            self.spin_minute[i].grid(row=2, column=2, sticky="w")
            ttk.Checkbutton(self.tabs[tab],
                            text="Enable task scheduling",
                            variable=self.enable_scheduler[i],
                            command=lambda i=i: self.update_spin(i)).grid(row=3, column=0, columnspan=5)

            ttk.Button(self.tabs[tab],
                       text="Apply",
                       command=self.apply_changes).grid(row=5, column=0, columnspan=5, pady=5)

    def get_wallpaper_path(self, i):
        path = askopenfilename(parent=self.parent, initialdir=os.path.expanduser(r"~\Pictures"),
                               filetypes=(("JPEG Files", "*.jpg *.jpeg"), ("PNG Files", "*.png")))
        if path:
            self.wallpaper_path[i].set(path)
            self.preview_img_on_canvas(path, i)

    def preview_img_on_canvas(self, img_path, i):
        # If the img_path is invalid (There's an error while displaying the img), return a warning and substitute with "No image selected"
        if img_path == "":
            self.preview_canvas[i].create_text(64, 32,
                                               text='No img selected',
                                               tag='placeholder_text')
        else:
            try:
                self.preview_canvas[i].delete('placeholder_text')
                img = Image.open(img_path)
                img.thumbnail((128, 96))
                preview_img = self.preview_canvas[i].create_image(64, 32)
                self.wallpaper_tk_thumbnail[i] = ImageTk.PhotoImage(img)

                self.preview_canvas[i].itemconfig(preview_img,
                                                  image=self.wallpaper_tk_thumbnail[i])
            except OSError:
                messagebox.showerror("Error", "Wallpaper path is invalid.", parent=self.parent)
                self.preview_img_on_canvas("", i)

    def whole_values_only(self, e):
        for i in [0, 1]:
            value = self.brightness_scale[i].get()
            self.brightness_scale[i].set(round(value))

    def save_settings(self):
        with open("settings.yaml", "r+") as file:
            settings = yaml.load(file, Loader=yaml.FullLoader)
        with open("settings.yaml", "w") as file:
            for i, mode in enumerate(['dark_mode', 'light_mode']):
                settings[mode]['brightness'] = self.brightness_scale[i].get()
                if self.wallpaper_path[i].get():
                    settings[mode]['wallpaper'] = self.wallpaper_path[i].get()
                settings[mode]['start_hour'] = self.start_hour[i].get()
                settings[mode]['os_theme'] = i
                settings[mode]['start_minute'] = self.start_minute[i].get()
                settings[mode]['enable_schedule'] = self.enable_scheduler[i].get()
            yaml.dump(settings, file)

    def read_settings(self):
        try:
            with open("settings.yaml") as file:
                settings = yaml.load(file, Loader=yaml.FullLoader)
                for i, mode in enumerate(['dark_mode', 'light_mode']):
                    self.brightness_scale[i].set(settings[mode]['brightness'] or 0)
                    self.wallpaper_path[i].set(settings[mode]['wallpaper'] or "")
                    self.start_hour[i].set(settings[mode]['start_hour'] or '09')
                    self.start_minute[i].set(settings[mode]['start_minute'] or '30')
                    self.enable_scheduler[i].set(settings[mode]['enable_schedule'] or False)
                    if not settings[mode]['enable_schedule']:
                        self.spin_state[i] = tk.DISABLED
                    else:
                        self.spin_state[i] = 'readonly'
        except FileNotFoundError:
            load_settings()
            self.read_settings()

    def update_spin(self, i):
        checked = self.enable_scheduler[i].get()
        self.spin_hour[i].config(state='readonly' if checked else tk.DISABLED)
        self.spin_minute[i].config(state='readonly' if checked else tk.DISABLED)

    def apply_changes(self):
        self.save_settings()
        for c, k in enumerate(["start_dark_mode", "start_light_mode"]):
            settings = {"start_dark_mode": None, "start_light_mode": None}
            settings[k] = f"{self.start_hour[c].get()}:{self.start_minute[c].get()}"
            if self.enable_scheduler[c].get():
                change_task_state(c, "ENABLE")
                create_task(**settings)
            else:
                change_task_state(c, "DISABLE")

        messagebox.showinfo("Settings saved",
                            "Settings have been successfully updated and will be applied next time you switch modes.",
                            parent=self.parent)


class About(Base):
    def __init__(self, parent):
        Base.__init__(self, parent)
        self.parent = parent
        self.frame = ttk.Frame(self.parent)
        self.frame.pack()
        Base.set_position(self, 242, 75)

        ttk.Label(self.frame, text="Theme switch 1.0.0", font=("Helvetica", 10, "bold")).grid(row=0, column=0)
        ttk.Label(self.frame, text="Programmed by Noé Guerra").grid(row=1, column=0)
        ttk.Label(self.frame, text="Project page and source code available at:").grid(row=4, column=0)
        link = ttk.Label(self.frame,
                         text="https://github.com/Nxz02/ThemeSwitchW10",
                         foreground="SteelBlue3",
                         cursor="hand2", )
        link.grid(row=5, column=0)
        link.bind("<Button-1>", lambda event: webbrowser.open_new(event.widget.cget("text")))


def main():
    root = tk.Tk()
    root.iconbitmap(True, "icon.ico")
    root.title("Theme Switcher")
    MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
