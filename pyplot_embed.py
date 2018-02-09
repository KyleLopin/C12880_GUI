# Copyright (c) 2017-2018 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

""" Embedded matplotlib plot in a tkinter frame """

#standard libraries
import logging
import tkinter as tk

# installed libraries
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib import pyplot as plt
# local files
import data_class

__author__ = 'Kyle Vitautas Lopin'

COUNT_SCALE = [10, 20, 50, 100, 200, 500, 1000, 5000, 10000, 50000, 100000]
LOWEST_WAVELENGTH = 340
HIGHEST_WAVELENGTH = 850
NUM_PIXELS = 288
WAVELENGTH_INCREMENT = (HIGHEST_WAVELENGTH - LOWEST_WAVELENGTH) / NUM_PIXELS
WAVELENGTHS = [LOWEST_WAVELENGTH + x*WAVELENGTH_INCREMENT for x in range(NUM_PIXELS)]
print(WAVELENGTHS)
print(len(WAVELENGTHS))

class SpectroPlotter(tk.Frame):
    def __init__(self, parent, _size=(6, 3)):
        tk.Frame.__init__(self, master=parent)
        self.data = data_class.SpectrometerData(WAVELENGTHS)
        self.scale_index = 3

        # routine to make and embed the matplotlib graph
        self.figure_bed = plt.figure(figsize=_size)
        self.axis = self.figure_bed.add_subplot(111)

        # self.figure_bed.set_facecolor('white')
        self.canvas = FigureCanvasTkAgg(self.figure_bed, self)
        self.canvas._tkcanvas.config(highlightthickness=0)

        toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        toolbar.update()

        self.canvas._tkcanvas.pack(side='top', fill=tk.BOTH, expand=True)
        self.canvas.draw()

        self.axis.set_xlim([400, 700])
        self.axis.set_xlabel("wavelength (nm)")

        self.axis.set_ylim([0, COUNT_SCALE[self.scale_index]])
        # self.axis.set_ylabel(r'$\mu$W/cm$^2$')
        self.axis.set_ylabel('counts')
        self.lines = None

    def update_data(self, new_count_data=None):
        logging.debug("updating data")
        if new_count_data:
            self.data.update_data(new_count_data)
        else:
            self.data.set_data_type()
        display_data = self.data.current_data

        while max(display_data) > COUNT_SCALE[self.scale_index]:
            self.scale_index += 1
            self.axis.set_ylim([0, COUNT_SCALE[self.scale_index]])
        while (self.scale_index >= 1) and (max(display_data) < COUNT_SCALE[self.scale_index-1]):
            self.scale_index -= 1
            self.axis.set_ylim([0, COUNT_SCALE[self.scale_index]])
        if self.lines:
            self.lines.set_ydata(display_data)
        else:
            self.lines, = self.axis.plot(WAVELENGTHS, display_data)
        self.canvas.draw()


