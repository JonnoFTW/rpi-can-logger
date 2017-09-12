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

If you want WiFi to work with the PiCAN2 shield attached, you'll need to unsolder the GPIO pins and drop them to the bottom and reattach the shield.

Better description of all necessary parts (coming soon).

## Installation

1. Assemble the parts from the part list.
2. Copy this repo to your Raspberry Pi:
````
git clone https://github.com/JonnoFTW/rpi-can-logger.git
````  
4. Run 
```
sudo pip3 install -r requirements.txt
sudo python3 setup.py install
```
 to install everything. You'll need root access if you want it to be installed a service that runs on startup.
3. Enable UART on your RPI (for the GPS) and CAN for the CAN shield by adding these lines to `/boot/config.txt`:
```
enable_uart=1
dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25
dtoverlay=mcp2515-can1,oscillator=16000000,interrupt=24
dtoverlay=spi-bcm2835
```
4. In order to stop the RPI from asking your serial ports `/ttyS0` to log on, change `/boot/cmdline.txt` and remove:
```
console=serial0,baudrate=115200
```
5. Add these lines to your `/etc/network/interfaces` file (set it to 250000 if you are using FMS):
```angular
auto can0
iface can0 inet manual
    pre-up /sbin/ip link set can0 type can bitrate 500000 triple-sampling on
    up /sbin/ifconfig can0 up
    down /sbin/ifconfig can0 down

auto can1
iface can1 inet manual
    pre-up /sbin/ip link set can1 type can bitrate 500000 triple-sampling on
    up /sbin/ifconfig can1 up
    down /sbin/ifconfig can1 down

```

5. The logging and file upload service will now run on startup. By default it will use: [example_obd_querying_conf.yaml](https://github.com/JonnoFTW/rpi-can-logger/blob/master/example_obd_querying_conf.yaml).
6. To setup uploading of files, you will need to create a `mongo_conf.yaml` file in the project directory.
  
## Configuration
RPI-CAN-Logger is highly configurable and supports nearly all standard OBD-2 PIDs and the currently understood frames from Tesla as described in [this document].
### Configuring CAN Logging

We currently support 3 forms of logging  (with CAN FMS and CAN FD to come soon):

* [Sniffing OBD](https://github.com/JonnoFTW/rpi-can-logger/blob/master/example_obd_sniffing_conf.yaml)
* [Querying OBD](https://github.com/JonnoFTW/rpi-can-logger/blob/master/example_obd_querying_conf.yaml)
* [Sniffing Tesla](https://github.com/JonnoFTW/rpi-can-logger/blob/master/example_tesla_conf.yaml)

Here we will examine the various configuration options:

```yaml
interface: socketcan_native # can bus driver
channel: can1 # which can bus to use
log-messages: /home/pi/log/can-log/messages/ # location of debug messages
log-folder: /home/pi/log/can-log/ # location of log files
log-size: 32 # maximum size in MB before log file is rotated 
log-pids: # the pids we want to log, refer to rpi_can_logger/logger/obd_pids.py or tesla_pids.py
  - PID_ENGINE_LOAD
  - PID_THROTTLE
  - PID_INTAKE_MAP
  - PID_RPM
  - PID_SPEED
  - PID_MAF_FLOW
log-trigger: PID_MAF_FLOW # when this PID is seen, return the buffer in current state (only works in sniffing mode)
disable-gps: false # enable/disable GPS logging
gps-port: /dev/ttyS0 # serial port for GPS device
tesla: false # indicates whether or not we are logging a tesla vehicle
sniffing: false # indicates that we are sniffing
log-bluetooth: true # whether or not we log to bluetooth
log-level: warning # log level (warning or debug)
```

### Configuring Data Upload

In the root directory of this project create a file called: `mongo_conf.yaml`, it should look like this:

```yaml

```