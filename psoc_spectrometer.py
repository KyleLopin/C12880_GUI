# Copyright (c) 2017-2018 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

""" Classes to represent different color spectrometers, implimented so here: C12880"""

# standard libraries
import json
import logging
import os
import queue
import struct
import threading
import time
import tkinter as tk
from tkinter import messagebox

# local files
import main_gui  # for type hinting
import usb_comm
# import usb_arduino_hack as usb_comm

__author__ = 'Kyle Vitautas Lopin'


C12880_CLK_SPEED = 500000.
C12880_CLK_PERIOD = 1. / C12880_CLK_SPEED
MAX_NUM_READS = 25

# LED_POWER_OPTIONS = ["100 mA", "50 mA", "25 mA", "12.5 mA", "6.25 mA", "3.1 mA"]
values = [100/2**x for x in range(0, 6)]

LED_POWER_OPTIONS = ["80 mA", "50 mA", "25 mA", "12.5 mA", "6.25 mA", "3.1 mA"]
values.reverse()
LED_POWER_OPTIONS = ["{:.0f} mA".format(x) for x in values]


class PSoC(object):
    def __init__(self, master: main_gui.SpectrometerGUI):
        self.communication = USB()
        self.usb = self.communication.usb  # alias to make it easier to write to

        self.spectrometer = C12880(master, self.usb)
        self.light_sources = [CAT4004(self.usb, "LED", max_power=100),
                              CAT4004(self.usb, "Laser", max_power=100),
                              PWMDimmer(self.usb, "Light 1", max_power=100, pwm_period=32, pwm_compare=32)]

    def read_once(self, integration_time, integration_unit, num_reads):
        self.spectrometer.read_once(integration_time, integration_unit, num_reads)

    def send_read_message(self, integration_time_set):
        logging.info("reading with integration time: {0}".format(integration_time_set))
        if integration_time_set != self.integration_time:
            self.set_integration_time(integration_time_set)


class USB(object):
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


class C12880(object):
    def __init__(self, master: main_gui.SpectrometerGUI, usb: USB):
        # BaseSpectrometer.__init__(self)
        self.master = master
        self.reading = None

        self.usb = usb

        self.integration_time = 40000

        self.st_clock_period = 24  # cycles / microsecond, make this variable to change
        self.st_clock_divider = 48  # initial divider value the PSoC is programmed with
        self.st_pwm_compare = self.calculate_pwm_compare()
        self.init_c12880()

    def init_c12880(self):
        self.set_integration_time(self.integration_time)
        # self.get_background_values()

    def get_background_values(self):
        self.read_once(40, 1000, 10, True)

    def set_integration_time(self, time):
        if time < 108:
            logging.error("Integration time out of bounds: {0}".format(time))
            messagebox.showerror("Error", "Integration time too low")
            return False
        elif time > 16250000:
            logging.error("Integration time out of bounds: {0}".format(time))
            messagebox.showerror("Error", "Integration time is too high")
            return False
        elif time < 60000:
            self.st_clock_divider = 48  # use lowest setting
        elif time < 260000:
            self.st_clock_divider = 96  # 4 usec period
        elif time < 3000000:
            self.st_clock_divider = 1200  # use lowest setting
        elif time < 16000000:
            self.st_clock_divider = 6000  # use lowest setting

        self.integration_time = time
        self.st_pwm_compare = self.calculate_pwm_compare()

        self.usb.usb_write("C12880|ST_DIVIDER|{0}".format(str(self.st_clock_divider).zfill(5)))
        self.usb.usb_write("C12880|ST_PERIOD|{0}".format(str(self.st_pwm_compare).zfill(5)))

        # self.usb.usb_write("C12880|INTEGRATION|{0}".format(str(time).zfill(3)))
        return True

    def calculate_pwm_compare(self):
        clock_period = self.st_clock_divider / self.st_clock_period  # microseconds clock period
        return int(self.integration_time / clock_period) - 48  # 48 because the C12880 integration time is
        # ST pin high plus 48 cycles, no extra 1 because PWM is set for less not less than or equal

    def read_once(self, integration_time_set, integration_time_unit, num_reads, background=False):

        integration_time = integration_time_set * integration_time_unit

        try:
            sent_read_flag = self.send_read_message(integration_time, num_reads, background)
        except:
            return "Failed sending read message"

        if not sent_read_flag:
            return

        try:
            logging.debug("sleeping for {0} seconds".format(num_reads * (integration_time/1000000.+0.1)))
            time.sleep(num_reads * (integration_time/1000000.+0.4))  # TODO: make this an after function somehow

            query_message = self.query_data_readiness()
            logging.info("query message: {0}".format(query_message))
        except Exception as expection:
            logging.error(expection)
            return "Failed getting query message"

        if query_message == "NOT DONE ":
            return "Data still being read"
        elif query_message == "NO DATA  ":
            return "Error with the C12880 device"
        elif not query_message:
            return "No message received"

        try:

            if num_reads == 1:
                logging.info("get a single read")
                data = self.usb.read_single_data()
            else:
                logging.info("read {0} times".format(num_reads))
                data = self.usb.read_multi_data()

            if background:
                self.master.set_background_values(data)

            if data:
                self.master.update_graph(data, num_reads)
        except:
            return "Problem getting data"

        try:
            self.get_C12880_state()
        except Exception as exception2:
            logging.error(exception2)
            return "Error getting C12880 state"
        return "Successful read"

    def send_read_message(self, integration_time_set, num_reads, is_background_measurement=False):
        logging.info("reading with integration time: {0}".format(integration_time_set))
        integration_set = True  # assume it has been set previously
        if integration_time_set != self.integration_time:
            integration_set = self.set_integration_time(integration_time_set)

        if is_background_measurement:
            self.usb.usb_write("C12880|BACKGROUND")
            return True

        if integration_set:
            if num_reads == 1:
                self.usb.usb_write("C12880|READ_SINGLE".format())
            elif 1 < num_reads <= MAX_NUM_READS:
                self.usb.usb_write("C12880|READ_MULTI|{0}".format(str(num_reads).zfill(3)))
            else:
                return False

            return True
        return False

    def query_data_readiness(self):
        self.usb.usb_write("C12880|QUERY_RUN")
        return self.usb.usb_read_data(num_usb_bytes=9, encoding="string")  # Query message is 9 chars long

    def get_C12880_state(self):
        self.usb.usb_write("C12880|DEBUG")
        time.sleep(0.2)
        data = self.usb.usb_read_data(11)
        data = self.convert_C12880_debug_values(data)
        data_struct = {}
        data_struct['TRG'] = data[0]
        data_struct['CLK'] = data[1]
        data_struct['ST'] = data[2]
        data_struct['ISR PWM'] = data[3]
        data_struct['dma count'] = data[4]
        data_struct['EoS status'] = data[5]

        if not os.path.exists('log/'):
            os.makedirs('log/')

        try:

            with open('log/C12880_state.log', 'a') as f:
                # f.write(data_struct)
                json.dump(data_struct, f)
                f.write("\nintegration time:{0}\n".format(self.integration_time))
        except:
            with open('log/C12880_state.log', 'w') as f:
                # f.write(data_struct)
                json.dump(data_struct, f)
                f.write("\nintegration time:{0}\n".format(self.integration_time))

        f.close()

    @staticmethod
    def convert_C12880_debug_values(data):

        return struct.unpack('<HHHHHB', data)

    # def LED_toggle(self):
    #     print("Led power: ", self.led_on)
    #     if self.led_on:  # LED is on so turn it off
    #         logging.info("turning off led")
    #         self.usb.usb_write("LED|OFF")
    #         self.led_on = False
    #     elif not self.led_on:
    #         logging.info("turn led on with power: {0}".format(self.led_power.get()))
    #         new_power_level = self.led_power_options.index(self.led_power.get())
    #         self.usb.usb_write("LED|ON|{0}".format(new_power_level))
    #         self.led_on = True
    #         self.led_power_set = new_power_level
    #
    # def change_led_power(self):
    #     logging.debug("changing led power to: {0}".format(self.led_power.get()))
    #     new_power_level = self.led_power_options.index(self.led_power.get())
    #     if new_power_level != self.led_power_set:
    #         self.usb.usb_write("LED|POWER|{0}".format(new_power_level))
    #         self.led_power_set = new_power_level
    #
    # def laser_toggle(self):
    #     print("Laser power: ", self.led_on)
    #     if self.laser_on:  # Laser is on so turn it off
    #         logging.info("turning off laser")
    #         self.usb.usb_write("LASER|OFF")
    #         self.laser_on = False
    #     elif not self.laser_on:
    #         logging.info("turn laser on with power: {0}".format(self.laser_power.get()))
    #         self.usb.usb_write("LASER|ON|{0}".format(self.laser_power_options.index(self.laser_power.get())))
    #         self.laser_on = True
    #
    # def change_laser_power(self):
    #     logging.debug("changing laser power to: {0}".format(self.laser_power.get()))
    #     new_power_level = self.laser_power_options.index(self.laser_power.get())
    #     if new_power_level != self.laser_power_set:
    #         self.usb.usb_write("LASER|POWER|{0}".format(new_power_level))
    #         self.laser_power_set = new_power_level


class LightSource(object):
    def __init__(self, usb: usb_comm.PSoC_USB, name: str,
                 power_var: tk.StringVar = None, power_options: list=None, power_set: int=0):
        self.usb = usb
        self.name = name
        if not power_var:
            power_var = tk.StringVar()
        self.power_var = power_var
        self.power_options = power_options
        self.power_set = power_set  # the current setting of the current to the light
        self.on = False  # type: Boolean to tell if the device has power to it
        self.use_flash = False  # flag to indicate if light source should be flashed

    def change_power_level(self, *args):
        logging.debug("changing {0} power to: {1}".format(self.name, self.power_var.get()))
        new_power_level = self.power_options.index(self.power_var.get())
        if new_power_level != self.power_set:
            self.usb.usb_write("{0}|POWER|{1}".format(self.name, new_power_level))
            self.power_set = new_power_level

    def toggle(self):
        logging.debug("{0} power: {1}".format(self.name, self.on))
        if self.on:
            logging.debug("Turning {0} off".format(self.name))
            self.usb.usb_write("{0}|OFF".format(self.name))
            self.on = False
        else:
            logging.debug("Turning {0} on with power {1}".format(self.name, self.power_set))
            self.usb.usb_write("{0}|ON|{1}".format(self.name, self.power_set))
            self.on = True

    def set_flash(self, use_flash=False):
        flash_flag = 0
        if use_flash:
            flash_flag = 1
        self.usb.usb_write("{0}|Flash|{1}".format(self.name, flash_flag))

class CAT4004(LightSource):
    def __init__(self, usb: usb_comm.PSoC_USB, name:str, max_power: int = 100):

        power_options = [max_power/2.**x for x in range(0, 6)]

        power_options_str = ["{:.0f} mA".format(x) for x in power_options]

        LightSource.__init__(self, usb, name, power_options=power_options_str)
        self.power_var.set(self.power_options[0])

class PWMDimmer(LightSource):
    def __init__(self, usb: usb_comm.PSoC_USB, name: str, max_power: int = 100,
                 pwm_period: int=255, pwm_compare=0):

        power_options = [max_power / 2. ** x for x in range(0, 5)]
        power_options_str = ["{:.0f} mA".format(x) for x in power_options]

        LightSource.__init__(self, usb, name, power_options=power_options_str)

        self.max_power = max_power
        self.power_set = self.power_options[0]
        self.power_var.set(self.power_set)
        self.pwm_period = pwm_period
        self.pwm_compare = pwm_compare

    def change_power_level(self, *args):
        logging.debug("changing {0} power to: {1}".format(self.name, self.power_var.get()))
        new_power_level = self.power_options.index(self.power_var.get())
        new_power_value = float(self.power_var.get().split()[0])
        new_pwm_setting = int((new_power_value / self.max_power) * self.pwm_period)
        if new_power_level != self.power_set:
            self.usb.usb_write("{0}|POWER|{1}".format(self.name, str(new_pwm_setting).zfill(3)))
            self.power_set = new_power_level

    def toggle(self):
        logging.debug("{0} power: {1}".format(self.name, self.on))
        if self.on:
            logging.debug("Turning {0} off".format(self.name))
            self.usb.usb_write("{0}|OFF".format(self.name))
            self.on = False
        else:
            logging.debug("Turning {0} on with power {1}".format(self.name, self.power_set))
            self.usb.usb_write("{0}|ON|{1}".format(self.name, str(self.pwm_compare).zfill(3)))
            self.on = True
