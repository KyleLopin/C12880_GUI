# Copyright (c) 2017-2018 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

""" Classes to represent different color spectrometers, implimented so here: C12880"""

# standard libraries
import logging
import queue
import threading
import tkinter as tk

# local files
import main_gui  # for type hinting
import usb_comm

__author__ = 'Kyle Vitautas Lopin'


C12880_CLK_SPEED = 500000.
C12880_CLK_PERIOD = 1. / C12880_CLK_SPEED

LED_POWER_OPTIONS = ["100 mA", "50 mA", "25 mA", "12.5 mA", "6.25 mA", "3.1 mA"]


class BaseSpectrometer(object):
    """ But the basic info all the Base PSoC Base color sensors / spectrometers should use """

    def __init__(self):
        self.OUT_ENDPOINT = 2
        self.DATA_IN_ENDPOINT = 1
        self.USB_INFO_BYTE_SIZE = 48
        self.NUMBER_DATA_PACKETS = 12

        # the data reading from the USB will be on a separate thread so that polling
        # the USB will not make the program hang.
        self.data_queue = queue.Queue()
        self.data_acquired_event = threading.Event()
        self.termination_flag = False  # flag to set when streaming data should be stopped

        self.usb = usb_comm.PSoC_USB(self, self.data_queue, self.data_acquired_event,
                                     self.termination_flag)


class C12880(BaseSpectrometer):
    def __init__(self, master: main_gui.SpectrometerGUI):
        BaseSpectrometer.__init__(self)
        self.reading = None
        self.laser_on = False
        self.laser_power = tk.StringVar()
        self.laser_power_set = 0
        self.laser_power_options = LED_POWER_OPTIONS  # no need to copy, its just for reference
        self.led_on = False
        self.led_power = tk.StringVar()
        self.led_power_set = 0
        self.led_power_options = LED_POWER_OPTIONS

        self.integration_time = 25
        self.init_C12880()

    def init_C12880(self):
        self.set_integration_time(self.integration_time)

    def set_integration_time(self, time):
        if self.integration_time < 25 or self.integration_time > 1000:
            logging.error("Integration time out of bounds: {0}".format(time))
        else:
            self.usb.usb_write("C12880|INEGRATION|{0}".format(str(time).zfill(4)))
            self.integration_time = time

    def read_once(self, integration_time_set):
        print(self.integration_time)
        if integration_time_set != self.integration_time:
            self.set_integration_time(integration_time_set)

        self.usb.usb_write("C12880|READ_SINGLE")

        data = self.usb.read_all_data()

    def LED_toggle(self):
        print("Led power: ", self.led_on)
        if self.led_on:  # LED is on so turn it off
            logging.info("turning off led")
            self.usb.usb_write("LED|OFF")
            self.led_on = False
        elif not self.led_on:
            logging.info("turn led on with power: {0}".format(self.led_power.get()))
            self.usb.usb_write("LED|ON|{0}".format(self.led_power_options.index(self.led_power.get())))
            self.led_on = True

    def change_led_power(self):
        logging.debug("changing led power to: {0}".format(self.led_power.get()))
        new_power_level = self.led_power_options.index(self.led_power.get())
        if new_power_level != self.led_power_set:
            self.usb.usb_write("LED|POWER|{0}".format(new_power_level))
            self.led_power_set = new_power_level

    def laser_toggle(self):
        print("Laser power: ", self.led_on)
        if self.laser_on:  # Laser is on so turn it off
            logging.info("turning off laser")
            self.usb.usb_write("LASER|OFF")
            self.laser_on = False
        elif not self.laser_on:
            logging.info("turn laser on with power: {0}".format(self.laser_power.get()))
            self.usb.usb_write("LASER|ON|{0}".format(self.laser_power_options.index(self.laser_power.get())))
            self.laser_on = True

    def change_laser_power(self):
        logging.debug("changing laser power to: {0}".format(self.laser_power.get()))
        new_power_level = self.laser_power_options.index(self.laser_power.get())
        if new_power_level != self.laser_power_set:
            self.usb.usb_write("LASER|POWER|{0}".format(new_power_level))
            self.laser_power_set = new_power_level
