# Copyright (c) 2017-2018 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

""" Data class to hold color sensor / spectrometer data """

# standard libraries
import array
import datetime
import logging
import os
from tkinter import messagebox
import tkinter as tk
from tkinter import filedialog
# local files


__author__ = 'Kyle V. Lopin'


class SpectrometerData(object):
    def __init__(self, wavelengths):
        self.current_data = None
        self.background_count = None
        self.use_background = False
        self.wavelengths = wavelengths
        self.num_reads = 1

    def update_data(self, data, num_data_reads):
        print("1222222222222222222223333333333333333333")
        print(data)
        print(num_data_reads)
        self.num_reads = num_data_reads
        if self.use_background:
            logging.debug("using background data")
            self.current_data = [(x - self.background_count) / num_data_reads for x in data]
        else:
            logging.debug("not using background data")
            self.current_data = [x / num_data_reads for x in data]
        logging.debug("test2")
        print("/44444444444444444444444444")
        print("current data: ", self.current_data)

    def save_data(self):
        SaveTopLevel(self.wavelengths, self.current_data, self.num_reads)


class SaveTopLevel(tk.Toplevel):
    def __init__(self, wavelength_data, light_data, num_reads):
        tk.Toplevel.__init__(self, master=None)
        self.geometry('400x300')
        self.title("Save data")
        self.data_string = tk.StringVar()

        self.data_string = "Wavelength, counts\n"
        for i, _data in enumerate(wavelength_data):

            if num_reads == 1:
                self.data_string += "{0:.2f}, {1:d}\n".format(_data, int(light_data[i]))
            else:
                self.data_string += "{0:.2f}, {0:.2f}\n".format(_data, light_data[i])

        text_frame = tk.Frame(self)
        text_frame.pack(side='top')
        text_box = tk.Text(text_frame, width=40, height=8)
        text_box.insert(tk.END, self.data_string)
        text_box.pack(side='left')

        scrollbar = tk.Scrollbar(text_frame, command=text_box.yview)
        scrollbar.pack(side='left', fill=tk.Y, expand=True)
        text_box['yscrollcommand'] = scrollbar.set

        tk.Label(self, text="Comments:").pack(side='top', pady=6)

        self.comment = tk.Text(self, width=40, height=3)
        self.comment.pack(side='top', pady=6)

        button_frame = tk.Frame(self)
        button_frame.pack(side='top', pady=6)
        tk.Button(button_frame, text="Save Data", command=self.save_data).pack(side='left', padx=10)
        tk.Button(button_frame, text="Close", command=self.destroy).pack(side='left', padx=10)

    def save_data(self):
        logging.debug("saving data")
        self.attributes('-topmost', 'false')
        _file = None
        try:
            _file = open_file('saveas')  # open the file
            logging.debug("saving data: 4; file: {0}".format(_file))
        except Exception as error:
            messagebox.showerror(title="Error", message=error)
        self.attributes('-topmost', 'true')

        if _file:
            if self.comment.get(1.0, tk.END):
                logging.debug("saving data: 5")
                self.data_string += self.comment.get(1.0, tk.END)
                logging.debug("saving data: 6; string: {0}".format(self.data_string))
            try:

                _file.write(self.data_string)
                logging.debug("saving data: 7")
                _file.close()
                self.destroy()

            except Exception as error:

                messagebox.showerror(title="Error", message=error)
                self.lift()

        else:
            self.destroy()


def open_file(_type):
    """
    Make a method to return an open file or a file name depending on the type asked for
    :param _type:
    :return:
    """
    """ Make the options for the save file dialog box for the user """
    file_opt = options = {}
    options['defaultextension'] = ".csv"
    # options['filetypes'] = [('All files', '*.*'), ("Comma separate values", "*.csv")]
    options['filetypes'] = [("Comma separate values", "*.csv")]
    logging.debug("saving data: 1")
    if _type == 'saveas':
        """ Ask the user what name to save the file as """
        logging.debug("saving data: 2")
        _file = filedialog.asksaveasfile(mode='a', confirmoverwrite=False, **file_opt)
    elif _type == 'open':
        _filename = filedialog.askopenfilename(**file_opt)
        return _filename
    logging.debug("saving data: 3")
    return _file


if __name__ == '__main__':
    data = SpectrometerData([450, 500, 550, 570, 600, 650])
    app = SaveTopLevel([450, 500, 550, 570, 600, 650], [1, 2, 3, 4, 5, 6])
    app.title("Spectrograph")
    app.geometry("900x650")
    app.mainloop()