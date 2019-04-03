#!/usr/bin/python


import json
import sys
import time
import base64
import struct
import binascii
import array

import paho.mqtt.client as mqtt

###
###		SET CLOUD SERVER
###
CLOUD_SERVER = "TTN"
# CLOUD_SERVER = "LORIOT"

LORIOT_BROKER = "_BROKER_ADDRESS_"          # for example: "mqtt.flespi.io"
# if using https://flespi.com/ as MQTT broker
#FLESPI_TOKEN  = "r2aoqVPOKJXKfAFrN55q05bm3GpdxTPOLP3ZyGB7foHlMcAp5vDTqF3ibjlw2YbB"

TTN_BROKER  = "eu.thethings.network"        # probably continent "eu" part should be changed
TTN_APP_ID  = "______"              # Application EUI
TTN_ACC_KEY = "______"              # Application ACCESS KEY


LOGFILE = "rssival.csv"             # can be changed to whatever you like
PLOTFILE = "datatoplot.js"          # DO NOT CHANGE

def add_point_ascircle(lat, lon, rssi, color):
    f = open(PLOTFILE, "a+")
    f.write('L.circle(['+str(lat)+', '+str(lon)+'], 5, {')
    f.write('color: "' + color + '", fillColor: "' + color + '", fillOpacity: 0.5\n')
    f.write('}).addTo(mymap).bindPopup("RSSI '+str(rssi)+'").openPopup();\n')
    f.write('\n')

def add_point_asmarker(lat, lon, rssi):
    f = open(PLOTFILE, "a+")
    f.write('L.marker(['+str(lat)+', '+str(lon)+']).addTo(mymap)\n')
    f.write('    .bindPopup("RSSI '+str(rssi)+'").openPopup();\n')
    f.write('\n')

def add_to_logfile(ctime, device, rssi, clr, hdop, isgps):   
    f = open(LOGFILE, "a+")
    f.write(ctime +','+ str(hdop)+','+device+','+str(rssi)+','+clr+','+str(isgps)+'\n')


def coord_conversion(s_curpos):
    """Decode from string current position, altitude and hdop received via MQTT broker"""

    data = array.array('B', [0, 0, 0, 0, 0, 0, 0, 0, 0])
    data = binascii.unhexlify(s_curpos)

    # because of python2
    tmp = (int(binascii.hexlify(data[0]), 16)*2**16)+(int(binascii.hexlify(data[1]), 16)*2**8)+int(binascii.hexlify(data[2]), 16)
    lat = float(tmp)*180.0/16777215.0-90.0

    tmp1 = (int(binascii.hexlify(data[3]), 16)*2**16)+(int(binascii.hexlify(data[4]), 16)*2**8)+int(binascii.hexlify(data[5]), 16)
    lng = float(tmp1)*360.0/16777215.0-180.0

    # alt = int(n_altitude)
    # data[6] = (alt >> 8) & 0xff
    # data[7] = alt & 0xff

    hdop = int(binascii.hexlify(data[8]), 16)

    return ([lat,lng,hdop])


def on_connect(client, userdata, flags, rc):
    print("Connected to: {} port: {}.".format(client._host, client._port))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(THE_TOPIC)
    print("Subscribed to: {}.".format(THE_TOPIC))


def on_message(client, userdata, msg):
    global CLOUD_SERVER

    themsg = json.loads(str(msg.payload))

    if CLOUD_SERVER is "LORIOT" :
        # discarding messages related to gateway
        if "gw" in themsg["cmd"]:
          return

        data_raw = themsg["data"]

        [tlat, tlong, hdop] = coord_conversion(data_raw)

        device = themsg["EUI"]
        if "rx" in themsg["cmd"]:
          rssi = themsg["rssi"]
          if rssi < -110:
            clr = 'red'
          elif -90 > rssi >= -110:
            clr = 'yellow'
          else:
            clr = 'green'

    elif CLOUD_SERVER is "TTN":

        data_raw = binascii.hexlify(base64.b64decode(themsg['payload_raw']))

        [tlat, tlong, hdop] = coord_conversion(data_raw)

        device = themsg["hardware_serial"]
        rssi = themsg["metadata"]["gateways"][0]["rssi"]

        if rssi < -110:
            clr = 'red'
        elif -90 > rssi >= -110:
            clr = 'yellow'
        else:
            clr = 'green'


    ctime = time.strftime('%X_%x')
    if "7fffff7fffff" in data_raw:
        add_to_logfile(ctime, device, rssi, clr, hdop, False)
        print('{} got invalid coordinates from: {} with RSSI: {} ({} - {}) - NOT PLOTTED.'.format(ctime, device, rssi, clr, hdop))
    else: 
        add_to_logfile(ctime, device, rssi, clr, hdop, True)
        add_point_ascircle(tlat, tlong, rssi, clr)
        print('{} got lat: {} long: {} from: {} with RSSI: {} ({} - {}).'.format(ctime, tlat, tlong, device, rssi, clr, hdop))

# 
#   Here we go...
#
if __name__ == '__main__':

    client = mqtt.Client()

    if CLOUD_SERVER is "LORIOT" :

        THE_TOPIC = "lopy_mapper/+/data"

        client.on_connect = on_connect
        client.on_message = on_message

        client.username_pw_set(FLESPI_TOKEN, password="None")
        client.connect(FLESPI_BROKER, 1883, 60)

        client.loop_forever()
        
    elif CLOUD_SERVER is "TTN": 

        THE_TOPIC = "+/devices/+/up"

        client.on_connect = on_connect
        client.on_message = on_message

        client.username_pw_set(TTN_APP_ID, password=TTN_ACC_KEY)
        client.connect(TTN_BROKER, 1883, 60)

        client.loop_forever()

    else:
        print("SELECT CLOUD SERVER")



