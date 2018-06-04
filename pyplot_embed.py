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

C12880_SERIAL = "17D00042"
pixel = range(1, 289)
print(pixel)
A_0 = 3.056675765e+2
B_1 = 2.718285424
B_2 = -1.550742501e-3
B_3 = -3.975858137e-6
B_4 = -5.463349212e-9
B_5 = -2.634533143e-11

COUNT_SCALE = [10, 20, 50, 100, 200, 500, 1000, 5000, 10000, 50000, 100000]
LOWEST_WAVELENGTH = 340
HIGHEST_WAVELENGTH = 850
NUM_PIXELS = 288
WAVELENGTH_INCREMENT = (HIGHEST_WAVELENGTH - LOWEST_WAVELENGTH) / NUM_PIXELS
WAVELENGTHS = [LOWEST_WAVELENGTH + x*WAVELENGTH_INCREMENT for x in range(NUM_PIXELS)]
print(WAVELENGTHS)
print([x for x in range(1, 289)])
WAVELENGTHS = [A_0+B_1*x+B_2*x**2+B_3*x**3+B_4*x**4+B_5*x**5 for x in range(1, 289)]
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

        self.axis.set_xlim([300, 850])
        self.axis.set_xlabel("wavelength (nm)")

        self.axis.set_ylim([-200, COUNT_SCALE[self.scale_index]])
        # self.axis.set_ylabel(r'$\mu$W/cm$^2$')
        self.axis.set_ylabel('counts')
        self.lines = None

    def update_data(self, new_count_data=None, num_data_reads: int = 1):
        logging.debug("updating data")
        if new_count_data:
            logging.debug("updating data 2")
            print(num_data_reads)
            print(new_count_data)
            self.data.update_data(new_count_data, num_data_reads)
            print("////////////////////////////////////////")
            logging.debug("[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[")
            print(self.data.current_data)
        else:
            self.data.set_data_type()
        display_data = self.data.current_data
        print("============= ", max(display_data))
        while max(display_data) > COUNT_SCALE[self.scale_index]:
            self.scale_index += 1
            self.axis.set_ylim([-100, COUNT_SCALE[self.scale_index]])
        while (self.scale_index >= 1) and (max(display_data) < COUNT_SCALE[self.scale_index-1]):
            self.scale_index -= 1
            self.axis.set_ylim([-100, COUNT_SCALE[self.scale_index]])
        if self.lines:
            self.lines.set_ydata(display_data)
        else:
            self.lines, = self.axis.plot(WAVELENGTHS, display_data)
        self.canvas.draw()


