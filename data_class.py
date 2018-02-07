# Copyright (c) 2017-2018 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

""" Data class to hold color sensor / spectrometer data """

# standard libraries
import array
import datetime
import logging
import os
import tkinter as tk
from tkinter import filedialog
# local files


__author__ = 'Kyle V. Lopin'


class SpectrometerData(object):
    def __init__(self, wavelengths):
        self.current_data = None
        self.wavelengths = wavelengths

    def update_data(self, data):
        self.current_data = data

    def save_data(self):
        SaveTopLevel(self.wavelengths, self.current_data)


class SaveTopLevel(tk.Toplevel):
    def __init__(self, wavelength_data, light_data):
        tk.Toplevel.__init__(self, master=None)
        self.geometry('400x300')
        self.title("Save data")
        self.data_string = tk.StringVar()

        _data_string = "Wavelength, counts\n"
        for i, _data in enumerate(wavelength_data):
            _data_string += "{0}, {1:4.2f}\n".format(_data, light_data[i])

        text_box = tk.Text(self, width=20, height=8)
        text_box.insert(tk.END, _data_string)
        text_box.pack()


if __name__ == '__main__':
    data = SpectrometerData([450, 500, 550, 570, 600, 650])
    app = SaveTopLevel([450, 500, 550, 570, 600, 650], [1, 2, 3, 4, 5, 6])
    app.title("Spectrograph")
    app.geometry("900x650")
    app.mainloop()