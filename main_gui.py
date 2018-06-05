# Copyright (c) 2018 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

""" File to start for a Graphical User interface for the C12880 spectrometer breakout board connected
to a PSoC controller.  The data is saved in the data_class file, pyplot_embed has a
matplotlib graph embedded into a tk.Frame to display the data and psoc_spectrometer simulates the device. """

# standard libraries
from collections import OrderedDict
import logging
import tkinter as tk
# installed libraries
# local files
import frameworks
import psoc_spectrometer
import pyplot_embed

__author__ = 'Kyle Vitautas Lopin'


class SpectrometerGUI(tk.Tk):
    """ Class to display the controls and data of a C12880 spectrometer.  Currently displays the
     last acquired data spectrum.

     TODO: add a time course notebook and move the current spectrum to a separate notebook. """

    def __init__(self, parent=None):
        """
        Initialize the graphical user interface by:
        1) Start the logging module
        2) Attach the device using the psoc_spectrometer call.
        3) Make the graph area using pyplot_embed that will display the intensity versus wavelength data.
        4) Make a frame that contains all the buttons used to control the device.
        5) Make a frame to display the status

        :param parent:  any parent program that could call this GUI
        """
        tk.Tk.__init__(self, parent)
        logging.basicConfig(format='%(asctime)s %(module)s %(lineno)d: %(levelname)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

        # make the main frame with the graph and button area
        main_frame = tk.Frame(self)
        main_frame.pack(side='top', fill=tk.BOTH, expand=1)

        # attach the actual device and make an easier to use alias for the
        # self.device = psoc_spectrometer.C12880(self)
        self.device = psoc_spectrometer.PSoC(self)

        # make the graph frame, the parent class is a tk.Frame
        self.graph = pyplot_embed.SpectroPlotter(main_frame, None)
        self.graph.pack(side='left', fill=tk.BOTH, expand=True)

        # make command buttons
        self.buttons_frame = ButtonFrame(main_frame, self.graph, self.device)
        self.buttons_frame.pack(side='left', padx=2, expand=True, fill=tk.Y)

        # make the status frame with the connect button and status information
        self.status_frame = StatusFrame(self, self.device)
        self.status_frame.pack(side='top', fill=tk.X)

    def update_graph(self, data: list, num_data_reads: int):
        """
        Allow user to call the master class to update the graph for any widget that does not
        have direct access to the graph

        :param data:  data to display on y-axis of graph
        """
        logging.debug("updating graph")
        self.graph.update_data(data, num_data_reads)

    def set_background_values(self, data: list):
        logging.debug('setting background data values')
        # self.graph.data.background_data = [x/10. for x in data]
        self.graph.data.background_count = int(sum(data) / len(data) / 10.0)  # PSoC uses to 10 runs to calculate background
        logging.debug('set background data value: {0}'.format(self.graph.data.background_count))


BUTTON_PADY = 7


class ButtonFrame(tk.Frame):
    """ Frame to contain all the buttons the user can use to control the settings and use of the device """

    def __init__(self, parent: tk.Frame, graph: pyplot_embed.SpectroPlotter, device):
        """
        Class to make all the buttons needed to control a C12880 spectrometer that is controlled by a PSoC.

        :param parent:  tkinter Frame or Tk this frame is embedded in.
        :param graph:  graph area, this is needed because it also contains the data class to be saved also
        :param device:  PSoC device that interfaces with the C12880
        """
        tk.Frame.__init__(self, parent)

        self.master = parent
        self.graph = graph
        self.device = device  # type: psoc_spectrometer.PSoC

        # make all the buttons and parameters
        # make a separate frame to isolate the integration time frame
        integration_frame = tk.Frame(self, bd=5, relief=tk.RIDGE)
        tk.Label(integration_frame, text="Integration time:").pack(side=tk.TOP, pady=BUTTON_PADY)
        self.integration_time_var = tk.IntVar()

        tk.Spinbox(integration_frame, from_=1, to=1000,
                   textvariable=self.integration_time_var).pack(side=tk.TOP, pady=BUTTON_PADY)
        self.integration_time_var.set(40)

        self.integration_time_unit = tk.IntVar()
        units = OrderedDict([(u"\u00B5sec", 1), ("msec", 1000), ("sec", 1000000)])

        unit_frame = tk.Frame(integration_frame)
        for key, value in units.items():
            tk.Radiobutton(unit_frame, text=key, variable=self.integration_time_unit, value=value).pack(side=tk.LEFT)
        unit_frame.pack(side=tk.TOP)
        self.integration_time_unit.set(1000)

        tk.Label(integration_frame, text="Number of samples to average").pack(side=tk.TOP, pady=BUTTON_PADY)
        self.num_reads_to_average = tk.IntVar()
        tk.Spinbox(integration_frame, from_=1, to=20,
                   textvariable=self.num_reads_to_average).pack(side=tk.TOP, pady=BUTTON_PADY)

        # let the user normalize the data to integration time
        # normalized_flag = tk.IntVar()
        # tk.Checkbutton(integration_frame,
        #                text="Normalize to integration time",
        #                variable=normalized_flag).pack(side=tk.TOP)
        #
        # self.subtraction_flag = tk.IntVar()
        # tk.Checkbutton(integration_frame, text="Subtract background",
        #                variable=self.subtraction_flag,
        #                command=self.set_background).pack(side=tk.TOP, fill=tk.X)

        integration_frame.pack(side='top', expand=True, fill=tk.X)

        # make LED control widgets
        lighting_frame = tk.Frame(self, bd=5, relief=tk.RIDGE)
        # ===============
        buttons = {}
        for light_source in self.device.light_sources:
            buttons[light_source.name] = frameworks.LightButtons(lighting_frame, light_source).pack(side='top')

        # tk.Label(lighting_frame, text="LED power (mA):").pack(side='top', pady=BUTTON_PADY)
        # self.LED_power_options = self.device.led_power_options
        #
        # tk.OptionMenu(lighting_frame, self.device.led_power, *self.LED_power_options,
        #               command=self.LED_set_power).pack(side='top', pady=BUTTON_PADY)
        # self.device.led_power.set("100 mA")
        #
        # self.LED_button = tk.Button(lighting_frame, text="Turn LED On", command=self.LED_toggle)
        # self.LED_button.pack(side='top', pady=BUTTON_PADY)
        #
        # # make a check box for if the LED should be flashed
        # self.use_led_flash = tk.IntVar()
        # self.flash_led_button = tk.Checkbutton(lighting_frame, text="Use flash", variable=self.use_led_flash)
        # self.flash_led_button.pack(side="top", pady=BUTTON_PADY)
        # ===============

        # make Laser control widgets: not DRY
        # tk.Label(lighting_frame, text="Laser power (mA):").pack(side='top', pady=BUTTON_PADY)
        # self.laser_power_options = self.device.laser_power_options
        #
        # tk.OptionMenu(lighting_frame, self.device.laser_power, *self.laser_power_options,
        #               command=self.laser_set_power).pack(side='top', pady=BUTTON_PADY)
        # self.device.laser_power.set("100 mA")
        #
        # self.laser_button = tk.Button(lighting_frame, text="Turn Laser On", command=self.laser_toggle)
        # self.laser_button.pack(side='top', pady=BUTTON_PADY)
        #
        # # make a check box for if the LED should be flashed
        # self.use_laser_flash = tk.IntVar()
        # self.flash_laser_button = tk.Checkbutton(lighting_frame, text="Use flash", variable=self.use_laser_flash)
        # self.flash_laser_button.pack(side="top", pady=BUTTON_PADY)

        lighting_frame.pack(side='top', expand=True, fill=tk.X)

        # make the run button
        self.read_button = tk.Button(self, text="Read", command=self.read_once)
        self.read_button.pack(side="top", expand=True)

        # self.flush_button = tk.Button(self, text="flush", command=self.device.usb.flush)
        # self.flush_button.pack(side="top", pady=BUTTON_PADY)

        # button to save the data, this will open a toplevel with the data printed out, and an option to save to file
        tk.Button(self, text="Save Data", command=self.save_data).pack(side="top", expand=True)

        tk.Button(self, text="Log Error", command=self.debug_comment).pack(side="top", pady=BUTTON_PADY)

        # tk.Button(self, text="Read USB", command=self.read_usb).pack(side="top", pady=BUTTON_PADY)

    def read_once(self):
        self.read_button.config(state=tk.DISABLED)

        read_message = self.device.read_once(self.integration_time_var.get(),
                                             self.integration_time_unit.get(),
                                             self.num_reads_to_average.get())
        logging.info("Read message: {0}".format(read_message))
        self.read_button.config(state=tk.ACTIVE)

    def read_usb(self):
        print(self.device.usb.usb_read_data(encoding='string'))

    def set_background(self):
        self.read_button.config(state=tk.DISABLED)
        if not self.graph.data.background_count:
            self.device.spectrometer.get_background_values()
        self.read_button.config(state=tk.ACTIVE)
        self.graph.data.use_background = self.subtraction_flag.get()

    def LED_toggle(self):
        # led_power_index = self.LED_power_options.index(self)
        self.device.LED_toggle()
        if self.device.led_on:  # LED is on, it has already been changed
            self.LED_button.config(text="Turn LED Off")
        else:  # LED is turned off so change text
            self.LED_button.config(text="Turn LED On")

    def LED_set_power(self, *args):
        # if self.device.led_on:
        self.device.change_led_power()

    def laser_toggle(self):
        # led_power_index = self.LED_power_options.index(self)
        self.device.laser_toggle()
        if self.device.laser_on:  # Laser is on, it has already been changed
            self.laser_button.config(text="Turn Laser Off")
        else:  # Laser is turned off so change text
            self.laser_button.config(text="Turn Laser On")

    def laser_set_power(self, *args):
        # if self.device.laser_on:
        self.device.change_laser_power()

    def save_data(self):
        """
        Save the set of data that is being displayed
        """
        logging.debug("save the data: ")
        self.graph.data.save_data()

    def debug_comment(self):
        error_message = GetMessage()
        # print(error_message.get("1.0", 'end-1c'))


def GetMessage():
    toplevel = tk.Toplevel()
    toplevel.geometry("300x300")
    toplevel.title("Enter message")
    tk.Label(toplevel, text="Enter message to put with log file:").pack(side='top')
    message = tk.StringVar()
    entry = tk.Text(toplevel, width=30, height=6, wrap=tk.WORD)
    entry.pack(side='top')

    tk.Button(toplevel, text="Save", command=lambda: save_message(entry, toplevel)).pack(side='top')


def save_message(message, toplevel):

    error_message = message.get(1.0, tk.END)
    with open('log/C12880_state.log', 'a') as f:
        f.write(error_message)
    f.close()
    toplevel.destroy()


class StatusFrame(tk.Frame):
    """ Frame to display information about the sensors and device attached """

    def __init__(self, parent: tk.Tk, device):  # psoc_spectrometerd.AS7262()):
        """
        Make all the information the user should know about device available to them.

        :param parent:
        :param device:
        """
        tk.Frame.__init__(self, parent)



if __name__ == '__main__':
    app = SpectrometerGUI()
    app.title("C12880 Spectrometer")
    app.geometry("900x750")
    app.mainloop()
