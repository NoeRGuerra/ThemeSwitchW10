from themeswitch import gui
import themeswitch.functions as functions
import tkinter as tk
from pathlib import Path
import argparse


def main():
    settings = functions.load_settings()
    functions.check_tasks(settings)
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--darkmode", action="store_const", const='dark_mode')
    ap.add_argument("-l", "--lightmode", action="store_const", const='light_mode')
    args = vars(ap.parse_args())
    if any(args.values()):
        mode = args['darkmode'] or args['lightmode']
        if type(mode) == str:
            values = settings[mode]
        else:
            values = settings['dark_mode'] if functions.light_mode_is_on() else settings['light_mode']
        functions.change_sys_theme(**values)
    else:
        root = tk.Tk()
        print(f'{Path(__file__).parent / "../icons/icon.ico"=}')
        root.iconbitmap(True, Path(__file__).parent / "../icons/icon.ico")
        root.title("Theme Switcher")
        gui.MainWindow(root)
        root.mainloop()


if __name__ == '__main__':
    main()