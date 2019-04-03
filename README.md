# Pycom_mapper

This code allows to plot on a map the power of the signal as receveid from a device conneted to LoRaWAN.

Two cloud servers are considered: TTN and Loriot


## The data generation part ("pytrack" folder code):

We are suppposing that the devices are [LoPy](https://pycom.io/product/lopy4/) with a [Pytrack board](https://pycom.io/product/pytrack/).

ABP authentication is used. To this end, constants:
```
DEVADDR = '____'
NWKSKEY = '____'
APPSKEY = '____'
```

in file `pytrack/trackit.py`  must be configured.



## The visualization part ("plotting" folder code):

Executing:
```
python mapplot.py
```

two files are generated:
* `rssival.csv` that stores the RSSI values of all the messages received by the cloud server;
* `datatoplot.js` that contains the data to be plotted. This is done automatically loading in a browser either file `webmapplot.html` or `webmapplot_norefresh.html` 

Before starting:

1) In file `mapplot.py`:
	- set the CLOUD_SERVER variable
	- then, accordingly to the cloud server used, fill in the other related variables below

2) In file `webmapplot.html` or `webmapplot_norefresh.html`:
	- set the variables `home_lat` and `home_lng` to the home center of the map
	- add your own Mapbox `accessToken:`
	- set refresh period at line: 	`<meta http-equiv="refresh" content="5">`

3) Before starting, delete or store somewhere else files: "datatoplot.js" and "rssival.csv".
Not deleting these files while cause new points to be added to them.