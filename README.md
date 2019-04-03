# Pycom_mapper

This code allows to plot on a map the power of the signal as receveid from a device conneted to LoRaWAN.

Two cloud servers are considered: TTN and Loriot


## The device ("pytrack" folder code):

We are suppposing that the devices are [LoPy](https://pycom.io/product/lopy4/) with a [Pytrack board](https://pycom.io/product/pytrack/) (https://pycom.io/)

ABP authentication is used. To this end, constants:
```
DEVADDR = '____'
NWKSKEY = '____'
APPSKEY = '____'
```

in file "pytrack/trackit.py" the must be configured



## The visualization part ("plotting"):

1) In file mapplot.py:
	- set the CLOUD_SERVER variable

2) In file webmapplot.html:
	- set the variables 'home_lat' and 'home_lng' to the home center of the map
	- add your own Mapbox 'accessToken:'
	- set refresh period at line: 	<meta http-equiv="refresh" content="5">

3) Delete  files: "datatoplot.js" and "rssival.csv"