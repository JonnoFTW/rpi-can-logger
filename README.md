# Raspberry PI CAN Bus Logger

This project provides code for logging CAN Bus data with a Raspberry Pi. It additionally also logs GPS data. All of this data is stored on an SD card and can then be easily uploaded to a server for easy viewing.

## Features

* Logs and interprets CAN bus data from:
  * OBD2
  * Tesla vehicles
  * Bus and Truck with FMS
  * Outlander PHEV
* Logs GPS
* Can operate in querying and sniffing mode
* Stores data on SD card. Can be configured to automatically upload via web API when connected to WiFi or 4G internet.
* Can be powered entirely from power provided by the OBD port in your vehicle!  You can also wire it into your fuse box or cigarette lighter to prevent it being powered permanently and draining your battery.
* Accompanying [Bluetooth App](https://github.com/JonnoFTW/OBD-Datalogger) to:
  * Visualise your data in realtime 
  * Fetch and upload stored data  
* [Web based data visualiser](https://github.com/JonnoFTW/webcan)

## Parts

The following parts are used:

* Raspberry Pi 3 Model B or Raspberry Pi Zero W
* [PiCAN CAN-Bus board](http://skpang.co.uk/catalog/pican2-duo-canbus-board-for-raspberry-pi-23-p-1480.html) or equivalent PiCAN product with 1 or 2 CAN buses. Any CAN receiver compatible with [python-can](https://python-can.readthedocs.io/en/latest/index.html) should work though.
* [GPS Receiver](https://www.dfrobot.com/product-1103.html)
* [DC-DC Converter](https://www.digikey.com.au/products/en?keywords=1597-1243-ND)


If you want WiFi to work with the PiCAN2 shield attached, you'll need to unsolder the GPIO pins and drop them to the bottom and reattach the shield.


If you are using the DC-DC converter, you will need to plug its outputs into the GPIO pins of the Raspberry Pi at pins 2 (5v power) and 6 (ground):

![Rpi Pins](https://www.element14.com/community/servlet/JiveServlet/previewBody/73950-102-11-339300/pi3_gpio.png)

To make your own OBD connector, you will need:

* [OBD Male connector](http://au.rs-online.com/web/p/automotive-connectors/8010991/)
* [Crimps](http://au.rs-online.com/web/p/automotive-connector-accessories/8010884/)

You'll only need to connect pins:

* 4 Chassis Ground
* 6 CAN High
* 14 CAN Low
* 16 12V Power

![OBD Pins](http://www.mbcluster.com/Old_Website/Media_Diagnostics/ODBII%20Master%20Pinout.jpg)


### Tesla

Please follow steps 1 and 2 from this instructable to access the Tesla CAN bus http://www.instructables.com/id/Exploring-the-Tesla-Model-S-CAN-Bus/: 
 
You will need the following parts:
 
 * [Tesla port](http://au.rs-online.com/web/p/pcb-connector-housings/7201162/)
 * [Crimps](http://au.rs-online.com/web/p/pcb-connector-contacts/7196555/)
 
## Full Setup

1. Download the latest raspbian  lite image from here: https://raspberrypi.org/downloads/raspbian
2. Insert your SD card into your computer
3. Use your preferred method to put the rasbpian image onto your machine. On linux:
````bash
wget https://downloads.raspberrypi.org/raspbian_lite_latest
tar -xvf  raspbian_lite_latest
# the if argument might be different
dd if=2017-09-07-raspbian_stretch-lite.img of=/dev/sdb bs=4M conv=fsync status=progress
````
4. Unmount your SD card, and plug it into your raspberry pi
5. Run the following commands after logging in (default username is `pi`, password is `raspberry`) and configuring 
wifi by putting your settings in `/etc/wpa_supplicant/wpa_supplicant.conf` (you will need to restart the wifi to have
 the settings take effect by 
running `sudo service networking restart`):
````bash
sudo apt update
sudo apt install git make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev xz-utils bluez python-bluez pi-bluetooth python3-yaml python-yaml
curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash
env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.6.2
git clone https://github.com/JonnoFTW/rpi-can-logger.git
````
### Install Rpi-Logger

1. Determine the configuration file you want to use or roll your own.
2. To install the dependencies and system services, run:
```bash
pip3 install -r requirements.txt
sudo python3 setup.py config_file.yaml
```
3. Enable UART on your RPI (for the GPS) and CAN (skip the second `dtoverlay` line if your CAN shield only has 1 input)
 for the CAN shield by adding these lines to `/boot/config.txt`:
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
5. Add these lines to your `/etc/network/interfaces` file (set it to 250000 if you are using FMS and skip `can1` if 
you only have 1 CAN port):
```
auto can0
iface can0 inet manual
    pre-up /sbin/ip link set can0 type can bitrate 500000 triple-sampling on restart-ms 100
    up /sbin/ifconfig can0 up
    down /sbin/ifconfig can0 down

auto can1
iface can1 inet manual
    pre-up /sbin/ip link set can1 type can bitrate 500000 triple-sampling on restart-ms 100
    up /sbin/ifconfig can1 up
    down /sbin/ifconfig can1 down

```

6. The logging and file upload service will now run on startup. By default it will use: [example_fms_logging.yaml](example_fms_logging.yaml).
7. To setup uploading of files, you will need to create a `mongo_conf.yaml` file in the project directory:
```yaml
log_dir: ~/log/can-log/
keys:
 - vid_key_1
 - vid_key_2
api_url: http://url.to/api/ # the api on the end is important
```
  
## Configuration
RPI-CAN-Logger is highly configurable and supports nearly all standard OBD-2 PIDs and the currently understood frames from Tesla as described in [this document](https://skie.net/uploads/TeslaCAN/Tesla%20Model%20S%20CAN%20Deciphering%20-%20v0.1%20-%20by%20wk057.pdf).
### Configuring CAN Logging

We currently support 4 forms of logging:

* [Sniffing OBD](example_obd_sniffing_conf.yaml)
* [Querying OBD](example_obd_querying_conf.yaml)
* [Sniffing Tesla](example_tesla_conf.yaml)
* [Sniffing FMS](example_fms_logging.yaml)

Here we will examine the various configuration options:

```yaml
interface: socketcan_native # can bus driver
channel: can1 # which can bus to use
log-messages: /home/pi/log/can-log/messages/ # location of debug messages
log-folder: /home/pi/log/can-log/ # location of log files
log-size: 32 # maximum size in MB before log file is rotated 
log-pids: # the pids we want to log, refer to rpi_can_logger/logger/obd_pids.py,  tesla_pids.py fms_pids.py outlander_pid
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
bluetooth-pass: super_secret_password # the password required to stream the bluetooth data
log-level: warning # log level (warning or debug)
fms: false # are we logging FMS? (Bus and Truck only)
verbose: true # give verbose message output on stdout
```

### Configuring Data Upload

In the root directory of this project create a file called: `mongo_conf.yaml`, it should look like this:

```yaml
log_dir: /home/pi/log/can-log/
pid-file: ~/log/can-log.pid
api_url: 'https://url.to.server.com/api/'
keys:
    - vid_key_1
    - vid_key_2
```
The keys are the API keys for each vehicle that this logger will log for.

## Cloning SD Cards

Because we're deploying to a lot of these devices, you'll need to make an image after setting everything up on your SD
card. Once you're done, plug your SD card into another computer and run:

`dd of=logger.img if=/dev/sdb bs=4M conv=fsync status=progress`

Once that's finished you'll have a file called `logger.img` on your machine, insert a new card and run:

`dd if=logger.img of=/dev/sdb bs=4M conv=fsync status=progress`

This should clone the SD card assuming they're exactly the same. If the cards are different sizes:
 
##### Larger Card
* Run `raspi-config` and resize the partition OR
* Remount the SD card and use your favourite partitioning tool to expand the 2nd partition

##### Smaller Card
Assuming the amount of data used on the image is less than the target SD card size, then you will need to shrink the 
data partition before you make the clone SD card. You can do this on Linux with the following (from this [tutorial](https://softwarebakery.com/shrinking-images-on-linux)):

```bash
sudo modprobe loop
sudo losetup -f
sudo losetup /dev/loop0 logger.img
sudo partprobe /dev/loop0
gksu gparted /dev/loop0
```
Use gparted to resize the 2nd partition so that it fits within the size of your target SD card. Then hit apply. Now we 
will truncate the image.

```bash
sudo losetup -d /dev/loop0
fdisk -l logger.img
```
You should get something like:

```
$ fdisk -l logger.img 

Disk fmslogger.img: 15.9 GB, 15931539456 bytes
255 heads, 63 sectors/track, 1936 cylinders, total 31116288 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk identifier: 0x96bbdd32

        Device Boot      Start         End      Blocks   Id  System
logger.img1            8192       93813       42811    c  W95 FAT32 (LBA)
logger.img2           94208    31116287    15511040   83  Linux
```
Record the sector size (on the 2nd line `"Units = ..."`, 512 bytes here) and end for the 2nd partition (31116287 here),
now you can run:

```bash
truncate --size=$[(31116287+1)*512] logger.img
```
You can now write the shrunken image.

#### Configuring Clones

After you've done all that set a new hostname (with no hyphens after `rpi-logger-`) for your device by running:

```bash
sudo python3 ./systemd/pariable.py rpi-logger-12345
sudo reboot
```

Where `12345` is the vehicle identifier. In order to connect via the bluetooth app, the device hostname must start with `rpi-logger-`
 
You'll also probably need to pair the bluetooth with your phone, run:

```bash
sudo bluetoothctl
discoverable on
pairable on
```
Initiate pairing on your phone. Then run:
```bash
discoverable off
pairable off
quit
```
Reboot your device and everything should be good to go.

## Testing

There's a bunch of different tests provided the `tests` folder:

* [`can_spam.py`](tests/can_spam.py) will transmit CAN frames with the last two of eight bytes as increasing integers from 0 to 0xff 
* [`gps_test.py`](tests/gps_test.py) will dump output of the GPS
* [`gps_sniff_test.py`](tests/gps_sniff_test.py) will dump raw CAN messages to display
* [`gpio_led_test.py`](tests/gpio_led_test.py) will test the LEDs
* [`can_dump.py`](tests/can_dump.py) will dump the CAN data to a CSV file
* [`query_single_pid.py`](tests/query_single_pid.py) will query every OBD PID and check for a response
* [`phev_query`](tests/phev_query.py) will query data from the battery control unit on a Mistubishi PHEV Outlander