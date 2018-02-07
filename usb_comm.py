# Copyright (c) 2017-2018 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

""" Classes to communication with a spectrophotometer"""

# standard libraries
import logging
import queue
import random
import struct
import threading
# installed libraries
import usb
import usb.core
import usb.util
import usb.backend

# local files
import psoc_spectrometer  # for type hinting

PSOC_ID_MESSAGE = b"PSoC-Spectrometer"
AS7262_ID_MESSAGE = b"C12880"

USB_DATA_BYTE_SIZE = 40
IN_ENDPOINT = 0x81
OUT_ENDPOINT = 0x02

__author__ = 'Kyle Vitautas Lopin'


class PSoC_USB(object):
    def __init__(self, master, queue: queue.Queue, event: threading.Event(),
                 termination_flag: bool,
                 vendor_id=0x04B4, product_id=0x8051):
        self.master_device = master
        self.found = False
        self.connected = False
        self.spectrometer = None
        self.device = self.connect_usb(vendor_id, product_id)
        self.connection_test()
        # data_processing_function([1])
        # make an extra thread to poll the usb as this thread will hang on the timeouts of the usb
        self.data_ready_event = event
        self.data_queue = queue
        self.data_aquire_thread = ThreadedUSBDataCollector(self, master, self.data_queue,
                                                           self.data_ready_event,
                                                           termination_flag)

    def connect_usb(self, vendor_id, product_id):
        """
        Use the pyUSB module to find and set the configuration of a USB device

        This method uses the pyUSB module, see the tutorial example at:
        https://github.com/walac/pyusb/blob/master/docs/tutorial.rst
        for more details

        :param vendor_id: the USB vendor id, used to identify the proper device connected to
        the computer
        :param product_id: the USB product id
        :return: USB device that can use the pyUSB API if found, else returns None if not found
        """
        device = usb.core.find(idVendor=vendor_id, idProduct=product_id)
        if device is None:
            logging.info("Device not found")
            return None
        else:  # device was found
            logging.info("PSoC found")
            self.found = True

        # set the active configuration. the pyUSB module deals with the details
        device.set_configuration()
        return device

    def connection_test(self):
        """ Test if the device response correctly.  The device should return a message when
        given and identification call of 'I', and return the Spectrometer the device is connect to
        after given the command of 'i'.
        :return: True or False if the device is communicating correctly
        """
        # needed to make usb_write work, will be updated if not connected correctly
        self.connected = True

        # first test if the PSoC is connected correctly
        self.usb_write("ID")  # device should identify itself; only the first I is important
        received_message = self.usb_read_data(encoding='string')
        logging.debug('Received identifying message: {0}'.format(received_message))
        if received_message != PSOC_ID_MESSAGE:
            # set the connected state to false if the device is not working properly
            logging.debug("PSoC send wrong message")
            self.connected = False
            return
        logging.debug("PSoC send correct message")
        # test for the spectrometer if the PSoC is connected
        self.usb_write('ID-Spectrometer')  # device will return string of the spectrometer it is connected to
        received_message = self.usb_read_data(encoding='string')
        logging.debug('Received identifying message: {0}'.format(received_message))
        if received_message == AS7262_ID_MESSAGE:
            self.spectrometer = "AS7262"
            logging.info("AS7262 attached")

    def usb_write(self, message, endpoint=OUT_ENDPOINT):
        if not endpoint:
            endpoint = self.master_device.OUT_ENDPOINT

        try:
            print("write to usb: ", message)
            self.device.write(endpoint, message)

        except Exception as error:
            logging.error("USB writing error: {0}".format(error))
            self.connected = False

    def usb_read_info(self, info_endpoint=None, num_usb_bytes=None):
        if not info_endpoint:
            info_endpoint = self.master_device.INFO_IN_ENDPOINT
        if not num_usb_bytes:
            num_usb_bytes = self.master_device.USB_INFO_BYTE_SIZE

    def usb_read_data(self, num_usb_bytes=USB_DATA_BYTE_SIZE,
                      endpoint=IN_ENDPOINT, encoding=None,
                      timeout=3000):
        """ Read data from the usb and return it, if the read fails, log the miss and return None
        :param num_usb_bytes: number of bytes to read
        :param endpoint: hexidecimal of endpoint to read, has to be formatted as 0x8n where
        n is the hex of the encpoint number
        :param encoding: string ['uint16', 'signed int16', or 'string] what data format to return
        the usb data in
        :return: array of the bytes read
        """
        if not self.connected:
            logging.info("not working")
            return None
        try:
            usb_input = self.device.read(endpoint, num_usb_bytes, timeout)  # TODO fix this
            print(usb_input)
        except Exception as error:
            logging.error("Failed data read")
            logging.error("No IN ENDPOINT: %s", error)
            return None
        if encoding == 'uint16':
            print("Not a confirmed encoding data type")
            num_elements = len(usb_input) / 2
            return struct.unpack('>'+'H'*num_elements, usb_input)
            # return convert_uint8_uint16(usb_input)
        elif encoding == "float32":
            if (len(usb_input) % 4) == 0:
                # return struct.iter_unpack('f', usb_input)
                return struct.unpack('>ffffff', usb_input)
            else:
                print("Error in reading")
        elif encoding == 'string':
            return usb_input.tostring()  # remove the 0x00 end of string
        else:  # no encoding so just return raw data
            return usb_input

    def read_all_data(self):
        try:

            logging.debug("reading all data")
            data_packet = []
            for i in range(12):
                data_packet.extend(self.usb_read_data(num_usb_bytes=48, encoding="uint6"))

            return data_packet
        except Exception as error:
            logging.error(error)

    def start_reading(self):
        pass


class ThreadedUSBDataCollector(threading.Thread):
    def __init__(self, device: PSoC_USB, master: 'psoc_spectrometer.BaseSpectrometer()',
                 data_queue: queue.Queue, data_event: threading.Event,
                 function_call=None, termination_flag=False):
        threading.Thread.__init__(self)
        self.device = device
        self.master = master
        self.data_queue = data_queue
        self.data_event = data_event
        # self.func_call = function_call
        self.running = True  # bool: Flag to know when the data read should stop
        self.termination_flag = termination_flag  # Flag to know when the thread should stop

    def run(self):
        """ Poll the USB for new data packets and pass it through the queue and set the event flag so the main
        program will update the graph.  Structure the program so if the termination flag is set, collect the last
        data point to clear the data from the sensor."""

        while not self.termination_flag:
            logging.debug("In data collection thread")
            if self.running:
                data = self.device.read_all_data()
                logging.debug("Got data: {0}".format(data))
                # make sure there is data and that the previous data has been processed
                # if data and self.data_queue.empty():
                #     self.data_queue.put(data)
                #     self.data_event.set()
                if data:
                    # self.func_call(data)
                    self.master.data_processing(data)
                elif not data:
                    self.termination_flag = True
                    logging.error("=================== Device not working =====================")
            else:  # the main program wants to stop the program
                self.termination_flag = True
        logging.debug("exiting data thread call: {0}".format(self.termination_flag, hex(id(self.termination_flag))))
        print(hex(id(self.termination_flag)))
        self.data_event.set()  # let the main program exit the data_read wait loop

    def stop_running(self):
        logging.debug("Stopping data stream")
        self.running = False

    def single_run(self):
        pass
