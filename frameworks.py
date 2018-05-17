# Copyright (c) 2018 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

""" Frameworks for using in Tkinter application"""

import tkinter as tk
# installed libraries
# local files
import psoc_spectrometer
import pyplot_embed


class LightButtons(tk.Frame):
    def __init__(self, parent: tk.Frame, light: psoc_spectrometer.LightSource, button_pady=5):
        # make a frame to hold the light source related widgets
        tk.Frame.__init__(self, parent)
        self.light = light
        tk.Label(self, text="{0} power (mA):".format(light.name)).pack(side='top', pady=button_pady)

        lighting_options = light.power_options

        tk.OptionMenu(self, light.power_var, *light.power_options,
                      command=light.change_power_level).pack(side='top', pady=button_pady)

        self.button = tk.Button(self, text="Turn {0} On".format(light.name),
                                relief=tk.RAISED, command=self.toggle)
        self.button.pack(side='top', pady=button_pady)

        # make a check box for if the light source should be flashed
        self.use_flash_local = tk.BooleanVar()
        tk.Checkbutton(self,
                       text="Use flash",
                       variable=self.use_flash_local,
                       command=self.flash_toggle).pack(side='top', pady=button_pady)
        # # make a check box for if the LED should be flashed
        # self.use_led_flash = tk.IntVar()
        # self.flash_led_button = tk.Checkbutton(lighting_frame, text="Use flash", variable=self.use_led_flash)
        # self.flash_led_button.pack(side="top", pady=BUTTON_PADY)

    def toggle(self):
        self.light.toggle()
        if self.light.on:
            self.button.config(text="Turn {0} off".format(self.light.name), relief=tk.SUNKEN)
        else:
            self.button.config(text="Turn {0} on".format(self.light.name), relief=tk.RAISED)

    def flash_toggle(self):
        print("toggle flash")
        self.light.use_flash = self.use_flash_local.get()
        print("use {0} flash {1} ".format(self.light.name, self.light.use_flash))
        self.light.set_flash(self.light.use_flash)
