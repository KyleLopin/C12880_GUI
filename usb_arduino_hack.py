# standard libraries

import serial
import time
# local files
import main_gui


BAUDRATE = 115200
STOPBITS = serial.STOPBITS_ONE
PARITY = serial.PARITY_NONE
BYTESIZE = serial.EIGHTBITS


def find_available_ports():

    # taken from http://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python

    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i+1) for i in range(32)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    available_ports = []
    for port in ports:
        try:
            device = serial.Serial(port=port, write_timeout=0.5,
                                   inter_byte_timeout=1, baudrate=115200,
                                   parity=serial.PARITY_EVEN, stopbits=1)
            device.close()
            available_ports.append(device)
        except (OSError, serial.SerialException):
            pass
    return available_ports


class PSoC_USB(object):
    def __init__(self, master: main_gui.SpectrometerGUI):
        self.device = serial.Serial('COM6', baudrate=BAUDRATE, stopbits=STOPBITS,
                                    parity=PARITY, bytesize=BYTESIZE, timeout=1)

    def usb_write(self, message):
        self.device.write(message.encode('utf-8'))

    def read_all_data(self):
        try:
            self.device.write(b'R')
            time.sleep(0.5)
            data = self.device.readline().rstrip()
            print(data)
            data2 = data.split(b",")[:-1]
            print(data2)
            if data:
                # self.device.flushOutput()
                # self.device.flushInput()
                print("check1")
                sdata = [int(p) for p in data2]
                print("check2")
                print(sdata)
                print(len(sdata))
                time.sleep(0.5)
                if len(sdata) == 288:
                    return sdata
                # print(from_device)
            else:
                print("no data")

        except Exception as error:
            print(error)

    def flush(self):
        self.device.flushInput()
        self.device.flushOutput()