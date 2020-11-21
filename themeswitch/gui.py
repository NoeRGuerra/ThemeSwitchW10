# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 07:24:36 2020

@author: noerg
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilename
from tkinter.scrolledtext import ScrolledText, Scrollbar
from PIL import Image, ImageTk
from themeswitch import functions
import yaml
import webbrowser
import os
import pyperclip
from pathlib import Path


class Base:
    def __init__(self, parent):
        self.parent = parent
        self.parent.resizable(False, False)
        self.load_theme()

    def set_position(self, w, h):
        """
        Start the window in the center of the screen.
        
        :param w: Width of the window in pixels
        :type w: int
        :param h: Height of the window in pixels
        :type h: int
        :return: None
        :rtype: None
        """
        ws = self.parent.winfo_screenwidth()  # Screen width
        hs = self.parent.winfo_screenheight()  # Screen height
        x = (ws / 2) - (w / 2)  # Program x axis
        y = (hs / 2) - (h / 2)  # Program y axis
        self.parent.geometry('{0}x{1}+{2}+{3}'.format(w, h, int(x), int(y)))

    def load_theme(self):
        """
        Load dark and light themes and allow the program to access them

        :return: None
        :rtype: None
        """
        # Code based on https://stackoverflow.com/a/62934393
        base_theme_dir = Path(__file__).parent / "awthemes-9.3.2/"
        self.parent.tk.eval(f"""
set base_theme_dir "{base_theme_dir.as_posix()}"

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

        Base.set_position(self, 200, 180)
        self.initialize_interface()
        self.get_active_mode()
        self.check_wallpaper()

    def initialize_interface(self):
        menubar = tk.Menu(self.parent)

        settings_menu = tk.Menu(self.parent, menubar, tearoff=0)
        settings_menu.add_command(label="Dark mode", command=self.open_dark_mode_settings)
        settings_menu.add_command(label="Light mode", command=self.open_light_mode_settings)
        menubar.add_cascade(label="Settings", menu=settings_menu)

        about_menu = tk.Menu(self.parent, menubar, tearoff=0)
        about_menu.add_command(label="About this program",
                               command=self.open_about_window)
        about_menu.add_command(label="Open program log",
                               command=self.open_log_window)
        menubar.add_cascade(label="About",
                            menu=about_menu)

        self.canvas.config(width=200,
                           height=150,)
        self.canvas.pack()

        self.action_btn.config(command=self.change_system_mode)
        self.action_btn.pack(fill=tk.BOTH)

        self.parent.config(menu=menubar)

    def get_active_mode(self):
        if functions.light_mode_is_on():
            self.apply_light_theme()
        else:
            self.apply_dark_theme()

    def change_system_mode(self):
        if functions.light_mode_is_on():
            mode = 'dark_mode'
            self.apply_dark_theme()
        else:
            mode = 'light_mode'
            self.apply_light_theme()
        functions.change_sys_theme(**functions.load_settings()[mode])

    def apply_dark_theme(self):
        self.style.theme_use("awdark")
        self.style.configure('TButton',
                             relief=tk.FLAT)
        self.img = ImageTk.PhotoImage(file=Path(__file__).parent / "../icons/moon.png")
        img_on_canvas = self.canvas.create_image(100, 75)
        self.canvas.configure(background='black', highlightbackground='black')
        self.canvas.itemconfig(img_on_canvas, image=self.img)
        self.action_btn.config(text="Dark mode on")

    def apply_light_theme(self):
        self.style.theme_use("awlight")
        self.style.configure('TButton',
                             relief=tk.FLAT)
        self.img = ImageTk.PhotoImage(file=Path(__file__).parent / "../icons/sun.png")
        img_on_canvas = self.canvas.create_image(100, 75)
        self.canvas.configure(background='white', highlightbackground='white')
        self.canvas.itemconfig(img_on_canvas, image=self.img)
        self.action_btn.config(text="Light mode on")

    def check_wallpaper(self):
        # Maybe there should be a way to turn this on or off?
        with open(Path(__file__).parent / "settings.yaml") as file:
            settings = yaml.load(file, Loader=yaml.FullLoader)
            dark_wp_path = settings['dark_mode']['wallpaper'] or ''
            light_wp_path = settings['light_mode']['wallpaper'] or ''
            if dark_wp_path == '' and light_wp_path == '':
                messagebox.showwarning("No wallpaper set", "Please select a wallpaper for your dark and light mode settings.")
                self.open_dark_mode_settings()
            elif dark_wp_path == '':
                messagebox.showwarning("No wallpaper set", "Please select a wallpaper for your dark mode settings.")
                self.open_dark_mode_settings()
            elif light_wp_path == '':
                messagebox.showwarning("No wallpaper set", "Please select a wallpaper for your light mode settings.")
                self.open_light_mode_settings()
            else:
                return

    def open_about_window(self):
        new_window = tk.Toplevel(self.parent)
        new_window.title("About")
        About(new_window)

    def open_log_window(self):
        new_window = tk.Toplevel(self.parent)
        new_window.title("Log")
        Log(new_window)

    def open_dark_mode_settings(self):
        new_window = tk.Toplevel(self.parent)
        new_window.title("Settings")
        Settings(new_window, 'dark_mode')

    def open_light_mode_settings(self):
        new_window = tk.Toplevel(self.parent)
        new_window.title("Settings")
        Settings(new_window, 'light_mode')

class Settings(Base):
    def __init__(self, parent, tab):
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
        tab_control.select(self.tabs[tab])
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

    def check_wallpaper_size(self, image):
        if image.size[0] < self.parent.winfo_screenwidth() and image.size[1] < self.parent.winfo_screenheight():
            messagebox.showwarning("Warning: Image resolution too low.",
                                   "The resolution of the selected image is too low. For better results, select an "
                                   f"image with a resolution higher than {self.parent.winfo_screenwidth()}x{self.parent.winfo_screenheight()}",
                                   parent=self.parent)
        elif image.size[0] < self.parent.winfo_screenwidth():
            messagebox.showwarning("Warning: Image width too low",
                                   "The width of the selected image is too low. "
                                   "To avoid black bars or a blurry wallpaper, select an image with a higher resolution.",
                                   parent=self.parent)
        elif image.size[1] < self.parent.winfo_screenheight():
            messagebox.showwarning("Warning: Image height too low.",
                                   "The height of the selected image is too low. "
                                   "To avoid black bars or a blurry wallpaper, select an image with a higher resolution.",
                                   parent=self.parent)
        return

    def preview_img_on_canvas(self, img_path, i):
        if img_path == "":
            self.preview_canvas[i].create_text(64, 32,
                                               text='No wallpaper set. \nClick here to select.',
                                               tag='placeholder_text')
        else:
            try:
                self.preview_canvas[i].delete('placeholder_text')
                img = Image.open(img_path)
                self.check_wallpaper_size(img)
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
        with open(Path(__file__).parent / "settings.yaml", "r+") as file:
            settings = yaml.load(file, Loader=yaml.FullLoader)
        with open(Path(__file__).parent / "settings.yaml", "w") as file:
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
            with open(Path(__file__).parent / "settings.yaml") as file:
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
            functions.load_settings()
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
                functions.change_task_state(c, "ENABLE")
                functions.create_task(**settings)
            else:
                functions.change_task_state(c, "DISABLE")

        messagebox.showinfo("Settings saved",
                            "Settings have been successfully updated and will be applied next time you switch modes.",
                            parent=self.parent)


class About(Base):
    def __init__(self, parent):
        Base.__init__(self, parent)
        self.parent = parent
        self.frame = ttk.Frame(self.parent)
        self.frame.pack()
        Base.set_position(self, 274, 75)

        ttk.Label(self.frame, text="Theme switch 1.0.0", font=("Helvetica", 10, "bold")).grid(row=0, column=0)
        ttk.Label(self.frame, text="Programmed by Noé Guerra").grid(row=1, column=0)
        ttk.Label(self.frame, text="Project page and source code available at:").grid(row=4, column=0)
        link = ttk.Label(self.frame,
                         text="https://github.com/NoeRGuerra/ThemeSwitchW10",
                         foreground="SteelBlue3",
                         cursor="hand2", )
        link.grid(row=5, column=0)
        link.bind("<Button-1>", lambda event: webbrowser.open_new(event.widget.cget("text")))

class Log(Base):
    def __init__(self, parent):
        Base.__init__(self, parent)
        self.parent = parent
        self.frame = ttk.Frame(self.parent)
        self.frame.pack()
        Base.set_position(self, 266, 270)

        bar = Scrollbar(self.frame, orient=tk.HORIZONTAL)
        self.log_box = ScrolledText(self.frame, width=35, height=15, wrap='none', font=("Calibri", 10))
        self.log_box.bind("<Key>", lambda e: "break")

        bar.config(command=self.log_box.xview)
        self.log_box.config(xscrollcommand=bar.set)

        self.log_box.grid(row=0, columnspan=2)
        bar.grid(row=1, column=0, sticky='nsew', columnspan=2)

        if functions.light_mode_is_on():
            self.log_box.config(background='gray88', foreground="gray8")
        else:
            self.log_box.config(background='gray15', foreground="gray95")
        ttk.Button(self.frame, text="Click here to copy", command=self.copy_log_clipboard).grid(row=2, column=0, columnspan=3, sticky="WE")
        self.read_log()

    def read_log(self):
        with open(Path(__file__).parent / "full.log") as file:
            self.text = file.readlines()
            self.log_box.insert(tk.INSERT, ''.join(self.text))

    def copy_log_clipboard(self):
        pyperclip.copy(''.join(self.text))