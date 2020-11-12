from themeswitch import gui
import themeswitch.functions as functions
import tkinter as tk
from pathlib import Path
import argparse
from pystray import Menu, MenuItem
import pystray
import time
from PIL import Image

logger = functions.get_logger(__name__)
logger.info("Starting program.")


def setup(icon):
    """
    Make the system tray icon visible and notifies the user

    :param icon: Icon object that is displayed on the System Tray
    :type icon: :class:`pystray.Icon`
    :return: None
    :rtype: None
    """
    logger.info("Program moved to System Tray.")
    icon.visible = True
    icon.notify("Theme switch has moved to the system tray.")
    time.sleep(3)
    icon.remove_notification()


def reopen_program(root, icon):
    """
    Redraw the gui window and hide System Tray icon.

    :param root: Main GUI Window
    :type root: :class:`tk.Tk`
    :param icon: Icon object that is displayed on the System Tray
    :type icon: :class:`pystray.Icon`
    :return: None
    :rtype: None
    """
    logger.info("Program opened from System Tray.")
    icon.visible = False
    icon.stop()
    root.deiconify()


def exit_tray(root, icon):
    """
    Close the program completely. Destroy the Main GUI window and stop the program from running on the System Tray

    :param root: Main GUI Window
    :type root: :class:`tk.Tk`
    :param icon: Icon object that is displayed on the System Tray
    :type icon: :class:`pystray.Icon`
    :return: None
    :rtype: None
    """
    logger.info("Closing program.")
    icon.visible = False
    icon.stop()
    root.destroy()


def change_mode_tray(settings):
    """
    Change to Dark or Light mode (Whichever is inactive) from the System Tray

    :param settings: A dictionary with the contents of `settings.yaml`
    :type settings: dict
    :return: None
    :rtype: None
    """
    mode = 'dark_mode' if functions.light_mode_is_on() else 'light_mode'
    logger.info("Changed to %s", mode)
    values = settings[mode]
    functions.change_sys_theme(values['brightness'], values['wallpaper'], values['os_theme'])


def main():
    """
    Load settings and check the status of scheduled tasks. Parse and run with the arguments invoked when running the
    program if any. If no arguments where invoked, open the GUI and move the program to System Tray when closed.

    :return: None
    :rtype: None
    """

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
        functions.change_sys_theme(values['brightness'], values['wallpaper'], values['os_theme'])
    else:
        def on_closing():
            icon = pystray.Icon("ThemeSwitch")
            icon.icon = Image.open(Path(__file__).parent / "../icons/icon.ico")
            icon.title = "Theme Switch"
            icon.menu = Menu(
                MenuItem('Open', lambda: reopen_program(root, icon), default=True),
                MenuItem('Change mode', lambda: change_mode_tray(settings)),
                MenuItem('Quit', lambda: exit_tray(root, icon))
            )
            root.withdraw()
            icon.run(setup)
        root = tk.Tk()
        root.iconbitmap(True, Path(__file__).parent / "../icons/icon.ico")
        root.title("Theme Switcher")
        gui.MainWindow(root)
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()


if __name__ == '__main__':
    main()