# Raspberry PI CAN Bus Logger

This project provides code for logging CAN Bus data with a Raspberry Pi. It additionally also logs GPS data. All of this data is stored on an SD card and intended to be used in a running .

## Features

* Logs CAN bus from either OBD2 or Tesla vehicles
* Logs GPS
* Can operate in polling and sniffing mode
* Stores data on SD card. Can be configured to automatically upload to FTP or web service when connected to WiFi or 4G internet.
* Can be powered entirely from power provided by the OBD port in your vehicle!  You can also wire it into your fuse box or cigarette lighter to prevent it being powered permanently and draining your battery.
* Accompanying Bluetooth App to visualise your data while you drive (coming soon)
* Web based data visualiser (coming soon)

## Parts

The following parts are used:

* Raspberry PI 3 Model B
* [PiCAN CAN-Bus board](http://skpang.co.uk/catalog/pican2-duo-canbus-board-for-raspberry-pi-23-p-1480.html) or equivalent PiCAN product with 1 or 2 CAN buses
* [GPS Receiver](https://www.dfrobot.com/product-1103.html)
* [DC-DC Converter](https://www.digikey.com.au/products/en?keywords=1597-1243-ND)


You'll need to do some soldering to make the connector from your OBD port or [Tesla port](http://au.rs-online.com/web/p/pcb-connector-housings/7201162/?searchTerm=720-1162&relevancy-data=636F3D3126696E3D4931384E525353746F636B4E756D626572266C753D656E266D6D3D6D61746368616C6C26706D3D5E285C647B362C377D5B4161426250705D297C285C647B337D5B5C732D2F255C2E2C5D5C647B332C347D5B4161426250705D3F292426706F3D3126736E3D592673743D52535F53544F434B5F4E554D4245522677633D4E4F4E45267573743D3732302D31313632267374613D3732303131363226)to your PiCAN.

Better description of all necessary parts (coming soon).

## Installation

1. Assemble the parts from the part list.
2. Copy this repo to your Raspberry Pi:
````
git clone https://github.com/JonnoFTW/rpi-can-logger.git
````  
4. Run `python setup.py install` to install everything. You'll need root access if you want it to be installed a service that runs on startup.
3. Enable UART on your RPI (for the GPS) and CAN for the CAN shield by adding these lines to `/boot/config.txt`:
```
enable_uart=1
dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25
dtoverlay=mcp2515-can1,oscillator=16000000,interrupt=24
dtoverlay=spi-bcm2835
```
4. In order to stop the RPI from asking your serial ports /ttyS0 from logging on, change `/boot/cmdline.txt` and remove:
```
console=serial0,baudrate=115200
```

  
## Configuration

RPI-CAN Logger is highly configurable. Some example configuration files are provided and look like:

