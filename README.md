# Octobox

Box for OrangePi Zero 2W running Octoprint for KP3S

## Server

You need to obtain an API key from Octoprint and store it in `api.key` in plain text.

### States

Modified for remote temperature sensor.

| State     | When                   | Look for               | Change to | Also do                                                      |
|-----------|------------------------|------------------------|-----------|--------------------------------------------------------------|
| (Initial) | starting Octobox       |                        | Off       | retract Pusher, capture Camera, switch everything OFF        |
| Off       | printer is off         | event `power`          | On        | switch Relay ON, start Camera, start timeout                 |
|           |                        | event `reboot`         | N/A       | reboot                                                       |
|           |                        | event `refresh`        |           | capture image                                                |
| On        | printer is powering on | Octo is `Operational`  | Idle      |                                                              |
|           |                        | Octo has error         | Off       | switch everything OFF                                        |
|           |                        | Timeout elapsed        | Off       | switch everything OFF                                        |
|           |                        | event `refresh`        |           | capture image                                                |
| Idle      | ready for print        | event `power`          | Off       | switch everything OFF                                        |
|           |                        | event `reboot`         | N/A       | reboot                                                       |
|           |                        | Octo has error         | Off       | switch everything OFF                                        |
|           |                        | Octo is `Printing`     | Printing  |                                                              |
|           |                        | event `refresh`        |           | restart video                                                |
| Printing  | print job running      | Octo has error         | Cooling   | switch off Printer, start Cooler, extend Pusher              |
|           |                        | Octo is not `Printing` | Cooling   | switch off Printer, start Cooler, extend Pusher              |
|           |                        | event `cancel`         | Cooling   | cancel Octo job, switch off Printer, start Cooler and Pusher |
| Cooling   | print job ended        | Octo has error         | Off       | retract Pusher, switch everything OFF                        |
|           |                        | bed temp < 35C         | Off       | retract Pusher, switch everything OFF                        |
|           |                        | event `power`          | Off       | retract Pusher, switch everything OFF                        |

## Peripherals

All methods take an optional argument to set the value,
or return the current value if no argument is given.
This module requires the module `python3-periphery`
and to be given access. See `install.sh`.

- `flash()` to switch the LED illuminating the camera.
This is used exclusively by the Camera module

- `fan()` to switch the cooling fan.

- `relay()` to switch the printer.

### Sensor

The MLX90614 allows monitoring ambient and bed temperatures at all times.
CPU sensor is now in this module.

### Camera

Upon initialization, kills current ustreamer if one is running.
When active, ustreamer is available at the URL
`http://localhost:8080`.

- `start()` starts ustreamer.

- `stop()` stops it. Calls `capture()`.

- `capture()` captures a still image into `/var/www/html/image.jpg`.

### Pusher

The motor is controlled by a TB6612FNG module.

## Display

This actually just updates the data files that are used by the HTML to display the page.

- `localIP` contains the local IP address.

- `state` contains the title of the document, which is the state returned by Octoprint.

- `temps` contains HTML snippet showing temperatures.

- `jobInfo` contains HTML snippet showing Job information (if any).

## Octoprint

This uses Octoprint's REST API to interact with it.
You need to obtain an API key from Octoprint and store it in `api.key` in plain text.

- Queries : `job` or `printer` queries.

- Requests : `connection` request to connect or disconnect the printer.

## Socket library

The file `/usr/share/octobox/socket` is used to pass events.
A user must first `lock()` it, then `read()` to or `write()` from it, 
then `free()` it.

## CGI

The GPI module uses the Socket library to send events to the running Octobox process.

- `power` to switch the printer.

- `reboot` to reboot Octobox.

- `cancel` cancels the print.

- `refresh` captures a new image.

## Documents

- `Orange.pptx` shows the cabling of the Opi Zero 2W.

- `.FCStd` files for 3D models.

    - `CapL` : the filament guide at the top of the Z pole
    
    - `Fan8` : casing for the cooling fan
    
    - `KPS-CameraHD 2w` : the camera bracket
    
    - `Octobox 2W simple` : frame for the Opi and the board
    
    - `Wirecover` : to isolate the terminals of the power supply
    
    - `Touch` : housing for the touch sensor (ambient light)

    - `horiz2` : horizontal feeder for filament spool
	
### OrangePi pinout

| Number | GPIO | Alt         | Value      | Color  |
|--------|------|-------------|------------|--------|
|        | 3.3V |             | Pusher VCC | Orange |
| 264    | PI8  | SDA.1       |            |        |
| 263    | PI7  | SCL.1       |            |        |
| 269    | PI13 | PWM3 TXD.4  | Pusher PWM | Green  |
|        | GND  |             | Pusher GND | Black  |
| 226    | PH2  | TXD.5       |            |        |
| 227    | PH3  | RXD.5       |            |        |
| 261    | PI5  | SCL.0 TXD.2 | I2C SCL    | Yellow |
|        | 3.3V |             | I2C VCC    | Orange |
| 231    | PH7  | MOSI.1      |            |        |
| 232    | PH8  | MISO.1      |            |        |
| 230    | PH6  | SCLK.1      |            |        |
|        | GND  |             |            |        |
| 266    | PI10 | SDA.2 RXD.3 |            |        |
| 256    | PI00 |             | Pusher EN  | Maroon |
| 271    | PI15 |             |            |        |
| 268    | PI12 | PWM2        | CPU Fan    | Green  |
| 258    | PI02 |             |            |        |
| 272    | PI16 |             |            |        |
|        | GND  |             |            |        |

| Number | GPIO | Alt         | Value     |        |
|--------|------|-------------|-----------|--------|
|        | 5V   |             |           |        |
|        | 5V   |             | Power 5V  | Red    |
|        | GND  |             | Power GND | Black  |
| 224    | PH0  | TXD.0       |           |        |
| 225    | PH1  | RXD.0       |           |        |
| 257    | PI01 |             |           |        |
|        | GND  |             |           |        |
| 270    | PI14 | PWM4 RXD.4  |           |        |
| 228    | PH04 |             |           |        |
|        | GND  |             | I2C GND   | Violet |
| 262    | PI6  | SDA.0 RXD.2 | I2C SDA   | Cream  |
| 229    | PH5  | CE.0        |           |        |
| 233    | PH9  | CE.1        | Pusher 1  | Blue   |
| 265    | PI9  | SCL.2 TXD.2 | Pusher 2  | Violet |
|        | GND  |             |           |        |
| 267    | PI11 | PWM1        | Flash     | Grey   |
|        | GND  |             |           |        |
| 76     | PC12 |             | Relay     | Cream  |
| 260    | PI04 |             | Fan120    | Blue   |
| 259    | PI03 |             | Fan80     | Violet |

## TODO

### Hardware

- Actuator

- Temperature sensor(s): MLX90614

	- Turn off printer at job's end and turn on cooling fan
	
	- Use sensor to monitor bed temperature and turn off cooling fan
	
- Recheck install script

- Better lighting for camera

### Software

HTTP GETtable file `http://octo2w.local/info` returns the following information
in INI format (`key=value`):

| Field       | Type   | Example        |
|-------------|--------|----------------|
| filename    | string | `octobox-part` |
| completion  | float  | `15.6`         |
| remaining   | HH:MM  | `01:32`        |

