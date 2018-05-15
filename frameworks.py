# Copyright (c) 2018 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

""" Frameworks for using in Tkinter application"""

import tkinter as tk
# installed libraries
# local files
import psoc_spectrometer
import pyplot_embed


class TkButtons(tk.Frame):
    def __init__(self, parent: tk.Frame, name: str, button_pady=5):
        tk.Frame.__init__(self, parent)

        tk.Label(self, text="{0} power (mA):".format(name)).pack(side='top', pady=button_pady)

