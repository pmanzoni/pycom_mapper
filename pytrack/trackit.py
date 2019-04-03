# PM: 2 april 2019
# based on trackit_base.py
# added: 
# - soft led color when inter-measurement delay.... well almost
# - using https://github.com/gregcope/L76micropyGPS
# - read values reading Pytrack button

import array
import gc
import json
import machine
import math
import network
import os
import pycom
import socket
import struct
import sys
import time
import ubinascii
import utime

from network import LoRa
from network import WLAN

from machine import SD
from machine import WDT
from machine import Pin


from pytrack import Pytrack
from L76micropyGPS import L76micropyGPS
from micropyGPS import MicropyGPS


MFREQ = 15 # seconds between periodic measurements


# Device LORAWAN parameters
DEVADDR = '____'
NWKSKEY = '____'
APPSKEY = '____'



class pyLED:
    color = {'off': 0x000000, 'red':0xff0000, 'orange': 0xff8000, 'yellow': 0xffff00, 'green': 0x00ff00, 'lightlite' : 0xe0e0e0, 'blue' : 0x00bfff, 'purple' : 0x8000ff, 'pink': 0xff00ff}
    debug = False

    def setLED(self, value):
        if (not self.debug):
            pycom.rgbled(self.color[value])

    def flashLED(self, value, d=2):
        if (not self.debug):
            pycom.rgbled(self.color[value])
            time.sleep(d)
            pycom.rgbled(self.color['off'])



def button_handler(arg):
    print("Button (%s) pushed!!" % (arg.id()))
    led.flashLED('blue')

    gc.collect()
    wdt.feed()

    fLat = my_gps.latitude[0]
    fLon = my_gps.longitude[0]
    fAlt = 0.00

    print("got coordinates values: " + str(fLat) + "  " + str(fLon))

    if my_gps.time_since_fix() > 0:
        led.flashLED('green')           # color green (got gps position)
    else: 
        led.flashLED('orange')             # color red (no gps position)

    # packing coordinates; setting incremental counter to 0 
    msg = coord_conversion(fLat, fLon, fAlt, 0)

    gc.collect()
    wdt.feed()
    lorawan_send_msg(msg)
    print("sent: ", msg)



def coord_conversion(n_latitude, n_longitude, n_altitude, n_hdop):
    """Encode current position, altitude and hdop and send it using LoRaWAN"""

    data = array.array('B', [0, 0, 0, 0, 0, 0, 0, 0, 0])

    lat = int(((n_latitude + 90) / 180) * 16777215)
    data[0] = (lat >> 16) & 0xff
    data[1] = (lat >> 8) & 0xff
    data[2] = lat & 0xff

    lon = int(((n_longitude + 180) / 360) * 16777215)
    data[3] = (lon >> 16) & 0xff
    data[4] = (lon >> 8) & 0xff
    data[5] = lon &0xff

    alt = int(n_altitude)
    data[6] = (alt >> 8) & 0xff
    data[7] = alt & 0xff

    hdop = int(n_hdop)
    data[8] = hdop & 0xff

    return bytes(data)




def lorawan_connect_ABP(lora, str_dev = '', str_nwk = '', str_app = ''):

    led = pyLED()
    print('LoRa start connection')

    # ABP (Activation By Personalization) authentication params
    dev_addr = struct.unpack(">l", ubinascii.unhexlify(str_dev))[0]
    nwk_swkey = ubinascii.unhexlify(str_nwk)
    app_swkey = ubinascii.unhexlify(str_app)

    # connection starts
    led.setLED('red')

    while not lora.has_joined():

        try:
            # join a network using ABP (Activation By Personalization)
            lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))
        except Exception as e:
            sys.print_exception(e)
            
        # wait until the module has joined the network
        print('Lorawan not joined yet....')
        # Not joined yet...
        time.sleep(2.5)

    # saving the state
    lora.nvram_save()
    
    # returning whether the join was successful
    if lora.has_joined():
        # Network joined!
        print('LoRa Joined')
        led.flashLED('green')
    else:
        # Network not joined!
        print('LoRa Not Joined')
        led.flashLED('red')
    return lora


def lorawan_send_msg(msg):
    lorasocket.setblocking(True)
    sdone = False
    while not sdone:
        try:
            count = lorasocket.send(msg)
            sdone = True
        except Exception as e:
            led.flashLED('red')
            sys.print_exception(e)
            print("Cannot send. Rebooting machine")
            time.sleep(2)
            machine.reset()				# a little brute force... but
    lorasocket.setblocking(False)


def send_simple_sync_msg(m=1):
    print('Sending sync: ', m)
    lorasocket.setblocking(True)
    lorasocket.send(struct.pack(">B", m))
    lorasocket.setblocking(False)
    tmp_data = lorasocket.recv(64)
    print('Sending sync; got: ' + str(tmp_data, 'utf-8'))


# ----------------------------------------------------

print('Starting pytrack LOGGER')

# disable heartbeat
pycom.heartbeat(False)
led = pyLED()

# disable WiFi
wlan = WLAN()
wlan.deinit()

py  = Pytrack()

my_gps = MicropyGPS(location_formatting='dd')
L76micropyGPS = L76micropyGPS(my_gps, py)
gpsThread = L76micropyGPS.startGPSThread()

print("startGPSThread thread id is: {}".format(gpsThread))

# configuring Pytrack button to activate message sending
p_in = Pin('P14')
p_in.callback(Pin.IRQ_FALLING | Pin.IRQ_RISING, button_handler)


gc.enable()                     # enable garbage collection
wdt = WDT(timeout=120000)       # enable watchdog with a timeout of 120 seconds


lora = LoRa(mode=LoRa.LORAWAN, tx_power= 14, region=LoRa.EU868)

lorawan_connect_ABP(lora, str_dev = DEVADDR, str_nwk = NWKSKEY, str_app = APPSKEY)

lorasocket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
lorasocket.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

# send_simple_sync_msg(1)
# time.sleep(1)

# send_simple_sync_msg(2)
# time.sleep(1)


scount = 1      # sequencial counter of read coordinates
while True:
    gc.collect()
    wdt.feed()

    print(my_gps.latitude)
    print(my_gps.longitude)

    if (my_gps.latitude[1]=='N'):
        fLat = my_gps.latitude[0]
    else:
        fLat = -my_gps.latitude[0]
    if (my_gps.longitude[1]=='E'):
        fLon = my_gps.longitude[0]
    else:
        fLon = -my_gps.longitude[0]
    fAlt = my_gps.altitude

    print("got coordinates values: " + str(fLat) + "  " + str(fLon))

    if my_gps.fix_type == 1:
        led.flashLED('orange')          # no gps position
    else: 
        led.flashLED('green')           # got gps position

    # packing coordinates; using hdop as sequential counter
    msg = coord_conversion(fLat, fLon, fAlt, scount)

    gc.collect()
    wdt.feed()
    lorawan_send_msg(msg)
    print("sent: ", msg)

    scount = scount + 1

    led.setLED('lightlite')
    time.sleep(MFREQ)
    led.setLED('off')










