from setuptools import setup

setup(
    name='Theme Switch',
    version='1.0.0',
    packages=[''],
    url='https://github.com/Nxz02/ThemeSwitchW10',
    license='GNU General Public License v3 (GPLv3)',
    author='Noé R. Guerra',
    author_email='noe.r.guerra@outlook.com',
    description='Simple program to switch between Windows 10 light and dark themes with some customization options.',
    entry_points={"console_scripts": ["themeswitch=themeswitch.__main__:main"]},
)
