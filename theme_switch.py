# -*- coding: utf-8 -*-

"""
Created on Tue Aug 18 07:01:40 2020

@author: noerg
"""

import argparse
import ctypes
import os
import winreg
import wmi
import yaml


def load_settings():
    try:
        with open("settings.yaml") as file:
            settings = yaml.load(file, Loader=yaml.FullLoader)
            settings = check_settings(settings)
            if not settings:
                raise FileNotFoundError
    except FileNotFoundError:
        with open("settings.yaml", "w") as file:
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
    return settings


def check_settings(settings):
    top_keys = ['dark_mode', 'light_mode']
    low_keys = ['brightness', 'enable_schedule', 'os_theme', 'start_hour', 'start_minute', 'wallpaper']
    if list(settings.keys()) != top_keys:
        return False
    for i, mode in enumerate(settings):
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
    return settings

def light_mode_is_on():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
                         access=winreg.KEY_READ | winreg.KEY_WOW64_32KEY)
    return winreg.EnumValue(key, 2)[1]


def change_brightness(value):
    c = wmi.WMI(namespace='wmi')
    methods = c.WmiMonitorBrightnessMethods()[0]
    methods.WmiSetBrightness(value, 0)


def change_wallpaper(path_to_wallpaper):
    ctypes.windll.user32.SystemParametersInfoW(20, 0, path_to_wallpaper, 0)


def change_apps_theme(value):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
                         0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, value)
    winreg.CloseKey(key)


def change_system_theme(value):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
                         0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, value)
    winreg.CloseKey(key)


def create_task(start_dark_mode=None, start_light_mode=None):
    if start_dark_mode:
        os.popen(r'SCHTASKS /CREATE /SC DAILY /TN "Theme Switch\Change to Dark Mode" /TR ' +
                 r'"python %userprofile%\Documents\test.py -d" /ST {0} /F'.format(start_dark_mode))
    if start_light_mode:
        os.popen(r'SCHTASKS /CREATE /SC DAILY /TN "Theme Switch\Change to Light Mode" /TR ' +
                 r'"python %userprofile%\Documents\test.py -l" /ST {0} /F'.format(start_light_mode))


def change_task_state(i, state):
    if i == 0:
        os.popen(r'SCHTASKS /CHANGE /TN "Theme Switch\Change to Dark Mode" /{0}'.format(state))
    elif i == 1:
        os.popen(r'SCHTASKS /CHANGE /TN "Theme Switch\Change to Light Mode" /{0}'.format(state))


def task_exists(task_name):
    if os.popen('schtasks /query /TN "Theme Switch\{0}" >NUL 2>&1 || echo error'.format(
            task_name)).read().strip() == "error":
        return False
    return True


def change_sys_theme(brightness, wallpaper, os_theme, **kwargs):
    change_brightness(brightness)
    change_wallpaper(wallpaper)
    change_apps_theme(os_theme)
    change_system_theme(os_theme)


def check_tasks(settings):
    tasknames = ("Change to Dark mode", "Change to Light mode")
    modes = ("dark_mode", "light_mode")
    for i, task_mode in enumerate(zip(tasknames, modes)):
        if not task_exists(task_mode[0]):
            start_time = f"{settings[task_mode[1]]['start_hour']}:{settings[task_mode[1]]['start_minute']}"
            values = [None, None]
            values[i] = f"{settings[task_mode[1]]['start_hour']}:{settings[task_mode[1]]['start_minute']}"
            create_task(*values)
        else:
            query = os.popen(r'schtasks /query /TN "Theme Switch\{0}" /fo CSV /nh'.format(task_mode[0]))
            output = query.readline().strip().replace('"', '')
            output = output.split(',')
            state = True if output[-1] == "Ready" else False
            time = output[-2].strip().split(" ")
            start_time = f"{settings[task_mode[1]]['start_hour']}:{settings[task_mode[1]]['start_minute']}"
            if len(time) > 1 and time[1][:-3] != start_time:
                start_time = time[:-3]
                settings[task_mode[1]]['start_hour'] = start_time.split(":")[0]
                settings[task_mode[1]]['start_minute'] = start_time.split(":")[1]
            if state != settings[task_mode[1]]['enable_schedule']:
                settings[task_mode[1]]['enable_schedule'] = state
            with open('settings.yaml', 'w') as file:
                yaml.dump(settings, file)


def main():
    settings = load_settings()
    check_tasks(settings)
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--darkmode", action="store_const", const='dark_mode')
    ap.add_argument("-l", "--lightmode", action="store_const", const='light_mode')
    args = vars(ap.parse_args())
    mode = args['darkmode'] or args['lightmode']

    if type(mode) == str:
        values = settings[mode]
    else:
        values = settings['dark_mode'] if light_mode_is_on() else settings['light_mode']
    change_sys_theme(**values)

    return


if __name__ == "__main__":
    main()
