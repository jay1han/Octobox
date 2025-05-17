# Octobox

Box for OrangePi Zero 2W running Octoprint for KP3S

## Server

You need to obtain an API key from Octoprint and store it in `api.key` in plain text.

### States

| State    | When                   | Look for               | Change to | Also do                                      |
|----------|------------------------|------------------------|-----------|----------------------------------------------|
| Off      | printer is off         | event `power`          | On        | switch Relay ON, start Camera, start timeout |
|          |                        | event `reboot`         | N/A       | reboot                                       |
| On       | printer is powering on | Octo is `Operational`  | Idle      |                                              |
|          |                        | Octo has error         | Off       | switch everything OFF                        |
|          |                        | Timeout elapsed        | Off       | switch everything OFF                        |
| Idle     | ready for print        | event `power`          | Off       | switch everything OFF                        |
|          |                        | event `reboot`         | N/A       | reboot                                       |
|          |                        | Octo has error         | Off       | switch everything OFF                        |
|          |                        | Octo is `Printing`     | Printing  |                                              |
| Printing | print job running      | Octo has error         | Cooling   | start Fan                                    |
|          |                        | Octo is not `Printing` | Cooling   | start Fan                                    |
|          |                        | event `cancel`         | Cooling   | cancel Octo job, start Fan                   |
| Cooling  | print job ended        | Octo has error         | Off       | switch everything OFF                        |
|          |                        | bed temp < 35C         | Off       | switch everything OFF                        |

### Peripherals

All methods take an optional argument to set the value,
or return the current value if no argument is given.
This module requires the module `python3-periphery`
and to be given access. See `install.sh`.

- `flash()` to switch the LED illuminating the camera.
This is used exclusively by the Camera module

- `fan()` to switch the cooling fan.

- `relay()` to switch the printer.

### Camera

Upon initialization, kills current ustreamer if one is running.
When active, ustreamer is available at the URL
`http://localhost:8080`.

- `start()` starts ustreamer.

- `stop()` stops it. Calls `capture()`.

- `capture()` captures a still image into `/var/www/html/image.jpg`.

### Display

This actually just updates the data files that are used by the HTML to display the page.

- `localIP` contains the local IP address.

- `state` contains the title of the document, which is the state returned by Octoprint.

- `temps` contains HTML snippet showing temperatures.

- `jobInfo` contains HTML snippet showing Job information (if any).

### Octo

This uses Octoprint's REST API to interact with it.
You need to obtain an API key from Octoprint and store it in `api.key` in plain text.

- Queries : `job` or `printer` queries.

- Requests : `connection` request to connect or disconnect the printer.

### Socket library

The file `/usr/share/octobox/socket` is used to pass events.
A user must first `lock()` it, then `read()` to or `write()` from it, 
then `free()` it.

### CGI

The GPI module uses the Socket library to send events to the running Octobox process.

- `power` to switch the printer.

- `reboot` to reboot Octobox.

- `cancel` cancels the print.

- `refresh` captures a new image.

## Document

- `Orange.pptx` shows the cabling of the Opi Zero 2W.

- `.FCStd` files for 3D models.

    - `CapL` : the filament guide at the top of the Z pole
    
    - `Fan8` : casing for the cooling fan
    
    - `KPS-CameraHD 2w` : the camera bracket
    
    - `Octobox 2W simple` : frame for the Opi and the board
    
    - `Wirecover` : to isolate the terminals of the power supply
    
    - `Touch` : housing for the touch sensor (ambient light)

    - `horiz2` : horizontal feeder for filament spool

## TODO

### Hardware

- Actuator

- Temperature sensor(s): MLX90614

- Separate big fan control from power

- Better lighting for camera

### Software

HTTP GETtable file `http://octo2w.local/info` returns the following information
in INI format (`key=value`):

| Field       | Type   | Example        |
|-------------|--------|----------------|
| filename    | string | `octobox-part` |
| completion  | float  | `15.6`         |
| remaining   | HH:MM  | `01:32`        |
