# -*- coding: utf-8 -*-

"""
Created on Tue Aug 18 07:01:40 2020

@author: noerg
"""

import ctypes
import os
import winreg
import wmi
import yaml
import logging
from pathlib import Path


def get_logger(name=__name__, level=logging.INFO):
    """Returns a :class:`logging.Logger` object.
    Sets two handlers with different levels of severity to the created logger.

    :param name: Name of the logger. Defaults to ``__name__``
    :type name: str
    :param level: Logger default level of severity. Defaults to `logging.INFO`
    :type level: int
    :return: A `logging.Logger` object using the provided name and level of severity
    :rtype: :class:`logging.Logger`
    """
    logging.basicConfig(level=level)
    logger = logging.getLogger(name)
    c_handler = logging.FileHandler(Path(__file__).parent / "full.log")
    f_handler = logging.FileHandler(Path(__file__).parent / "app.log")
    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.ERROR)

    c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    return logger


logger = get_logger(__name__)


def load_settings():
    """
    Reads the contents of `settings.yaml` and returns them as a dictionary. If the file can't be found,
    or the contents are not the ones expected by the program, a new file with default values is created.

    :raises FileNotFoundError: Raised when the file `settings.yaml` is not found.
    The exception is handled by creating a new `settings.yaml` file with a default set of values
    :return: A dictionary with the contents of `settings.yaml` or default values.
    :rtype: dict
    """
    logger.info("Attempting to read settings file")
    try:
        with open(Path(__file__).parent / "settings.yaml") as file:
            settings = yaml.load(file, Loader=yaml.FullLoader)
            if not check_settings(settings):
                raise FileNotFoundError
            logger.info("Settings recovered successfully")
    except FileNotFoundError:
        with open(Path(__file__).parent / "settings.yaml", "w") as file:
            settings = {
                "dark_mode": {
                    "brightness": 0,
                    "os_theme": 0,
                    "wallpaper": "",
                    "start_hour": "07",
                    "start_minute": "00",
                    "enable_schedule": False
                },
                "light_mode": {
                    "brightness": 100,
                    "os_theme": 1,
                    "wallpaper": "",
                    "start_hour": "19",
                    "start_minute": "00",
                    "enable_schedule": False
                },
            }
            yaml.dump(settings, file)
            logger.info("New settings file with default values created in %s", Path(__file__).parent / "settings.yaml")
    return settings


def check_settings(settings):
    """
    Verify the integrity of `settings.yaml` and return False if there's any problem with the file.

    :param settings: A dictionary with the contents of `settings.yaml`
    :type settings: dict
    :raises AttributeError: If the number of keys in the dictionary are not the expected amount, return False
    :return: True or False
    :rtype: bool
    """
    top_keys = ['dark_mode', 'light_mode']
    low_keys = ['brightness', 'enable_schedule', 'os_theme', 'start_hour', 'start_minute', 'wallpaper']
    try:
        if list(settings.keys()) != top_keys:
            return False
        for i, mode in enumerate(settings):
            if list(settings[mode].keys()) != low_keys:
                return False
            if any(value is None for value in settings[mode].values()):
                return False
            if any(key not in low_keys for key in settings[mode].keys()):
                return False
            if type(settings[mode]['brightness']) != int or settings[mode]['brightness'] < 0 or settings[mode]['brightness'] > 100:
                return False
            if type(settings[mode]['enable_schedule']) != bool:
                return False
            if type(settings[mode]['os_theme']) != int or settings[mode]['os_theme'] != i:
                return False
        return True
    except AttributeError:
        logger.error("Settings file non-existing or corrupted.")
        return False


def light_mode_is_on():
    """
    Check the Windows registry and returns `1` if light mode is on

    :return: 1 if Windows light mode is on, 0 if not
    :rtype: bool
    """
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
                         access=winreg.KEY_READ | winreg.KEY_WOW64_32KEY)
    logger.info("Light mode is on: %s", bool(winreg.EnumValue(key, 2)[1]))
    return winreg.EnumValue(key, 2)[1]


def change_brightness(value):
    """
    Change Windows brightness level to ``value`` using WMI

    :param value: A number within the range 0-100
    :type value: int
    :return: None
    :rtype: None
    """
    c = wmi.WMI(namespace='wmi')
    methods = c.WmiMonitorBrightnessMethods()[0]
    methods.WmiSetBrightness(value, 0)
    logger.info("Brightness level set to %s", value)


def change_wallpaper(path_to_wallpaper):
    """
    Change Windows wallpaper to the image located in ``path_to_wallpaper``

    :param path_to_wallpaper: Path to the image file that will be set as wallpaper. A JPEG or PNG are expected
    :type path_to_wallpaper: str
    :return: None
    :rtype: None
    """
    ctypes.windll.user32.SystemParametersInfoW(20, 0, path_to_wallpaper, 0)
    logger.info("Wallpaper set to %s", path_to_wallpaper)


def change_apps_theme(value):
    """
    Change to dark mode or light mode for apps

    :param value: 0 for dark mode, 1 for light mode
    :type value: int
    :return: None
    :rtype: None
    """
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
                         0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, value)
    winreg.CloseKey(key)
    logger.info("Changed apps theme to %s", "dark mode" if value==0 else "light mode")


def change_system_theme(value):
    """
    Change to dark mode or light mode systemwide

    :param value: 0 for dark mode, 1 for light mode
    :type value: int
    :return: None
    :rtype: None
    """
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
                         0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, value)
    winreg.CloseKey(key)
    logger.info("Changed apps theme to %s", "dark mode" if value == 0 else "light mode")


def create_task(start_dark_mode=None, start_light_mode=None):
    """
    Create a daily task in Windows Task Scheduler for switching to dark or light mode

    :param start_dark_mode: Time for the `'Change to Dark Mode'` task to be scheduled in a 24 hours format `HH:MM`
    For example, `"19:00"`
    :type start_dark_mode: str
    :param start_light_mode: Time for the `'Change to Light Mode'` task to be scheduled in a 24 hours format `HH:MM`
    For example, `"07:00"`
    :type start_light_mode: str
    :return: None
    :rtype: None
    """
    if start_dark_mode:
        os.popen(r'SCHTASKS /CREATE /SC DAILY /TN "Theme Switch\Change to Dark Mode" /TR ' +
        r'"{0} -d" /ST {1} /F'.format(Path(__file__).parent / "..\TSwitch.exe", start_dark_mode))
        logger.info("Task scheduled: 'Change to Dark Mode' at %s", start_dark_mode)

    if start_light_mode:
        os.popen(r'SCHTASKS /CREATE /SC DAILY /TN "Theme Switch\Change to Light Mode" /TR ' +
                 r'"{0} -l" /ST {1} /F'.format(Path(__file__).parent / "..\TSwitch.exe", start_light_mode))
        logger.info("Task scheduled: 'Change to Light Mode' at %s", start_light_mode)


def change_task_state(i, state):
    """
    Enable or disable a Windows Task Scheduler task

    :param i: ``0`` to change dark mode task state, ``1`` for light mode
    :type i: int
    :param state: `ENABLE` or `DISABLE`
    :type state: str
    :return: None
    :rtype: None
    """
    if i == 0:
        os.popen(r'SCHTASKS /CHANGE /TN "Theme Switch\Change to Dark Mode" /{0}'.format(state))
        logger.info("Task changed: 'Change to Dark Mode' set to %s", state)
    elif i == 1:
        os.popen(r'SCHTASKS /CHANGE /TN "Theme Switch\Change to Light Mode" /{0}'.format(state))
        logger.info("Task changed: 'Change to Light Mode' set to %s", state)


def task_exists(task_name):
    """
    Check if a task named ``task_name`` exists in Windows Task Scheduler

    :param task_name: Name of the task to check. Can be either `Change to Dark Mode` or `Change to Light Mode`
    :type task_name: str
    :return: False if task doesn't exists. True if it does
    :rtype: bool
    """
    return not os.popen('schtasks /query /TN "Theme Switch\{0}" >NUL 2>&1 || echo error'.format(
            task_name)).read().strip() == "error"


def change_sys_theme(brightness, wallpaper, os_theme, **kwargs):
    """
    Set brightness, wallpaper, system theme and apps theme to given values.
    For example:
    >> change_sys_theme(80, "path/to/wallpaper.jpg", 1)

    Values can be passed as a dictionary

    :param brightness: Brightness level. A number within the range 0-100
    :type brightness: int
    :param wallpaper: Path to the image file that will be set as wallpaper. A JPEG or PNG are expected
    :type wallpaper: str
    :param os_theme: 0 for dark mode, 1 for light mode
    :type os_theme: int
    :return: None
    :rtype: None
    """
    change_brightness(brightness)
    change_wallpaper(wallpaper)
    change_apps_theme(os_theme)
    change_system_theme(os_theme)


def check_tasks(settings):
    """
    Check if the status of the scheduled tasks is the same in Task Scheduler and in the setting files.
    If the tasks do not exists or have a different configuration than in the settings file, they will be updated to
    correct their status and properties.

    :param settings: Dict containing the settings from settings.yaml
    :type settings: dict
    :return: None
    :rtype: None
    """
    tasknames = ("Change to Dark mode", "Change to Light mode")
    modes = ("dark_mode", "light_mode")
    for i, task_mode in enumerate(zip(tasknames, modes)):
        task_start_time = f"{settings[task_mode[1]]['start_hour']}:{settings[task_mode[1]]['start_minute']}" # Get the task start time from settings
        if not task_exists(task_mode[0]) and settings[task_mode[1]]['enable_schedule']:
            # Create a new task if it doesn't exist in task scheduler
            start_time = [None, None]
            start_time[i] = task_start_time
            create_task(*start_time)
            logger.warning("Task %s did not exist in Task Scheduler although it was not deleted by this program."
                           " The task has been created again.", task_mode[0])
        else:
            # If the task does exist, check if its status and properties are the same ones as in the settings file
            query = os.popen(r'schtasks /query /TN "Theme Switch\{0}" /fo CSV /nh'.format(task_mode[0]))
            output = query.readline().strip().replace('"', '')
            output = output.split(',')
            task_enabled = output[-1] == "Ready"
            time = output[-2].strip().split(" ")  # Current next run time for the task
            correct_state = settings[task_mode[1]]['enable_schedule']
            if task_enabled == correct_state and time[-1][:-3] == task_start_time:
                continue
            elif time[-1] != "N/A" and time[1][:-3] != task_start_time:
                start_time = [None, None]
                start_time[i] = task_start_time
                create_task(*start_time)
                logger.warning("Task %s next run time has been corrected to %s", task_mode[0], start_time[i])
                check_tasks(settings)
            if task_enabled != correct_state:
                state = "ENABLE" if correct_state else "DISABLE"
                change_task_state(i, state)
                logger.warning("Task %s status has been corrected to %s", task_mode[0], state)
                check_tasks(settings)
    # Call check_tasks again because:
    #     - The function can't check if a task is disabled and if its next run time is correct at the same time
    #     - If the tasks do not exists, they are created and are enable no matter what the settings file config is
