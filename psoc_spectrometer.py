# Copyright (c) 2017-2018 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

""" Classes to represent different color spectrometers, implimented so here: C12880"""

# standard libraries
import json
import logging
import os
import queue
import struct
import threading
import tkinter as tk

# local files
import main_gui  # for type hinting
import usb_comm
# import usb_arduino_hack as usb_comm

__author__ = 'Kyle Vitautas Lopin'


C12880_CLK_SPEED = 500000.
C12880_CLK_PERIOD = 1. / C12880_CLK_SPEED

# LED_POWER_OPTIONS = ["100 mA", "50 mA", "25 mA", "12.5 mA", "6.25 mA", "3.1 mA"]
values = [80*x/31 for x in range(0, 32)]
print(values)
LED_POWER_OPTIONS = ["80 mA", "50 mA", "25 mA", "12.5 mA", "6.25 mA", "3.1 mA"]
values.reverse()
LED_POWER_OPTIONS = ["{:.0f} mA".format(x) for x in values]
print("LED Options")
print(LED_POWER_OPTIONS)


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
        # self.usb = usb_comm.PSoC_USB(self)


class C12880(BaseSpectrometer):
    def __init__(self, master: main_gui.SpectrometerGUI):
        BaseSpectrometer.__init__(self)
        self.master = master
        self.reading = None
        self.laser_on = False
        self.laser_power = tk.StringVar()
        self.laser_power_set = 0
        self.laser_power_options = LED_POWER_OPTIONS  # no need to copy, its just for reference
        self.led_on = False
        self.led_power = tk.StringVar()
        self.led_power_set = 0
        self.led_power_options = LED_POWER_OPTIONS

        self.integration_time = 40
        self.init_C12880()

    def init_C12880(self):
        self.set_integration_time(self.integration_time)

    def set_integration_time(self, time):
        if self.integration_time < 1 or self.integration_time > 131:
            logging.error("Integration time out of bounds: {0}".format(time))
        else:
            self.usb.usb_write("C12880|INTEGRATION|{0}".format(str(time).zfill(3)))
            self.integration_time = time

    def read_once(self, integration_time_set, led_flash, laser_flash):
        logging.info("reading with integration time: {0}".format(integration_time_set))
        logging.info("reading with led flash: {0} and laser flash".format(led_flash, laser_flash))
        if integration_time_set != self.integration_time:
            self.set_integration_time(integration_time_set)

        self.usb.usb_write("C12880|READ_SINGLE|{0}|{1}".format(led_flash, laser_flash))

        data = self.usb.read_all_data()
        print(data)
        print("integration time: {0}".format(integration_time_set))
        if data:
            self.master.update_graph(data)

        self.get_C12880_state()

    def get_C12880_state(self):
        self.usb.usb_write("C12880|Debug")
        data = self.usb.usb_read_data(24)
        data = self.convert_C12880_debug_values(data)
        data_struct = {}
        data_struct['TRG'] = data[0]
        data_struct['CLK'] = data[1]
        data_struct['ST'] = data[2]
        data_struct['ISR PWM'] = data[3]
        data_struct['dma count'] = data[4]
        data_struct['EoS status'] = data[5]

        print(data_struct)
        if not os.path.exists('log/'):
            os.makedirs('log/')
        with open('log/C12880_state.log', 'a') as f:
            # f.write(data_struct)
            json.dump(data_struct, f)
            f.write('\n')
        f.close()

    @staticmethod
    def convert_C12880_debug_values(data):


        return struct.unpack('<HHHHHB', data)

    def LED_toggle(self):
        print("Led power: ", self.led_on)
        if self.led_on:  # LED is on so turn it off
            logging.info("turning off led")
            self.usb.usb_write("LED|OFF")
            self.led_on = False
        elif not self.led_on:
            logging.info("turn led on with power: {0}".format(self.led_power.get()))
            new_power_level = self.led_power_options.index(self.led_power.get())
            self.usb.usb_write("LED|ON|{0}".format(new_power_level))
            self.led_on = True
            self.led_power_set = new_power_level

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
