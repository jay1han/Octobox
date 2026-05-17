# Octobox

Box for OrangePi Zero 2W running Fluidd/Moonraker/Klipper

# Hardware

## Components

### Actuator TB6612

Controls the actuator that opens/closes door.

[Instructables](https://www.instructables.com/Driving-Small-Motors-With-the-TB6612FNG/)

### Temperature sensor MLX90614

Reads the bed temperature via I2C.

[Instructables](https://www.instructables.com/MLX90614-Non-Contact-Infrared-Temperature-Sensor-W/)

### Relays

4-channel 5V module from [AliExpress](https://fr.aliexpress.com/item/1005007538301230.html).
Usage:
[Instructables](https://www.instructables.com/5V-4-Channel-Relay-Module-With-Arduino/)

- Box fan (12V): 120mm fan at the rear of the cabinet
- Bed cooler (12V): 80mm fan cools the bed after a print
- Printer power (220V)

### 2N7000 Transistor

Pack from [AliExpress](https://fr.aliexpress.com/item/1005006203763174.html).
Usage:
[2N7000 as switch](https://electronzap.com/brief-n-channel-enhancement-mode-mosfet-switch-circuit-2n7000-transistor/)

- Camera light (5V)
- CPU fan (5V): small 40mm fan cooling the CPU

## OrangePi Zero 2W pinout

| Number | GPIO | Alt         | Value      |   | Number | GPIO | Alt         | Value      |
|--------|------|-------------|------------|---|--------|------|-------------|------------|
|        | 3.3V |             | I2C VCC    |   |        | 5V   |             |            |
| 264    | PI8  | SDA.1       | I2C SDA    |   |        | 5V   |             | Power 5V   |
| 263    | PI7  | SCL.1       | I2C SCL    |   |        | GND  |             | Power GND  |
| 269    | PI13 | PWM3 TXD.4  |            |   | 224    | PH0  | TXD.0       |            |
|        | GND  |             | I2C GND    |   | 225    | PH1  | RXD.0       |            |
| 226    | PH2  | TXD.5       |            |   | 257    | PI01 |             |            |
| 227    | PH3  | RXD.5       |            |   |        | GND  |             |            |
| 261    | PI5  | SCL.0 TXD.2 |            |   | 270    | PI14 | PWM4 RXD.4  | Pusher PWM |
|        | 3.3V |             | Pusher VCC |   | 228    | PH04 |             |            |
| 231    | PH7  | MOSI.1      |            |   |        | GND  |             | Pusher GND |
| 232    | PH8  | MISO.1      |            |   | 262    | PI6  | SDA.0 RXD.2 | Pusher 2   |
| 230    | PH6  | SCLK.1      |            |   | 229    | PH5  | CE.0        | Pusher 1   |
|        | GND  |             |            |   | 233    | PH9  | CE.1        |            |
| 266    | PI10 | SDA.2 RXD.3 |            |   | 265    | PI9  | SCL.2 TXD.2 | Light      |
| 256    | PI00 | Flash       |            |   |        | GND  |             | MOSFET GND |
| 271    | PI15 |             |            |   | 267    | PI11 | PWM1        | Fan40      |
| 268    | PI12 | PWM2        |            |   |        | GND  |             | Relay GND  |
| 258    | PI02 |             |            |   | 76     | PC12 |             | Fan120     |
| 272    | PI16 |             |            |   | 260    | PI04 |             | Printer    |
|        | GND  |             |            |   | 259    | PI03 |             | Fan80      |
	
# Software 

The software is a daemon started from systemd.
It listens on port `8080` and provides a basic HTTP server,
with a simple HTML page showing its current state.
The page contains minimal Javascript to update itself when needed.

The daemon also listens on port `8088` to serve [Moonraker's commands](#moonraker-interface).

## States

| State     | When                   | Look for              | Change to | Also do                                         |
|-----------|------------------------|-----------------------|-----------|-------------------------------------------------|
| (Initial) | booting                |                       | OFF       | retract Pusher, switch everything OFF           |
| OFF       | printer is off         | event `power`         | ON        | switch Relay ON                                 |
| ON        | printer is powering on | Moonraker is ready    | IDLE      |                                                 |
| IDLE      | ready for print        | event `power`         | OFF       | switch everything OFF                           |
|           |                        | Moonraker is printing | PRINTING  | switch Fan ON, Flash ON                         |
| PRINTING  | print job running      | Moonraker is stopped  | COOLING   | switch off Printer, start Cooler, extend Pusher |
|           |                        | event `cancel`        | PRINTING  | cancel job                                      |
| COOLING   | print job ended        | bed temp < 35C        | OFF       | retract Pusher, switch everything OFF           |
|           |                        | event `power`         | OFF       | retract Pusher, switch everything OFF           |
| (Any)     |                        | event `reboot`        | N/A       | switch everything OFF then reboot               |

## Moonraker API

Moonraker's
[HTTP API](https://moonraker.readthedocs.io/en/latest/external_api/introduction/#http-api-overview)
are used to update the daemon's internal state.

## Moonraker interface

The daemon provides an endpoint for Moonraker's
[HTTP devices](https://moonraker.readthedocs.io/en/latest/configuration/#generic-http-devices)
interface.

Moonraker must be configured

# Documents

- `Orange.pptx` shows the cabling of the Opi Zero 2W.
- `.FCStd` files for 3D models.
    - `CapL` : the filament guide at the top of the Z pole
    - `Fan8` : casing for the cooling fan
    - `KPS-CameraHD 2w` : the camera bracket
    - `Octobox 2W simple` : frame for the Opi and the board
    - `Wirecover` : to isolate the terminals of the power supply
    - `Touch` : housing for the touch sensor (ambient light)
    - `horiz2` : horizontal feeder for filament spool
