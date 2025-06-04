from periphery import GPIO, I2C, PWM
import signal
import subprocess, os, re, sys, shutil
from time import sleep

_GPIO_FLASH  = 267
_GPIO_COOLER = 259
_GPIO_POWER  = 76
_GPIO_CPU    = 268
_GPIO_FAN    = 260
_GPIO_PUSHER = 256     # low active
_GPIO_A1     = 233
_GPIO_A2     = 265

_PWM_PUSHER  = 3

_I2C_TEMP    = "/dev/i2c-0"
_TEMP_ADDR   = 0x5A
_REG_TOBJ1   = 0x07
_REG_TA      = 0x06

RESOLUTION   = '1280x800'
    
class Peripheral:
    def __init__(self):
        self._flashGpio = GPIO("/dev/gpiochip0", _GPIO_FLASH, "out")
        self._flashGpio.write(False)
        self._coolerGpio = GPIO("/dev/gpiochip0", _GPIO_COOLER, "out")
        self._coolerGpio.write(False)
        self._fanGpio = GPIO("/dev/gpiochip0", _GPIO_FAN, "out")
        self._fanGpio.write(False)
        self._powerGpio = GPIO("/dev/gpiochip0", _GPIO_POWER, "out")
        self._powerGpio.write(False)
        
        self._cpuGpio = GPIO("/dev/gpiochip0", _GPIO_CPU, "out")
        self._cpuGpio.write(False)
        
        self._pusherEnx = GPIO("/dev/gpiochip0", _GPIO_PUSHER, "out")
        self._pusherEnx.write(True)
        self._pusher1 = GPIO("/dev/gpiochip0", _GPIO_A1, "out")
        self._pusher1.write(False)
        self._pusher2 = GPIO("/dev/gpiochip0", _GPIO_A2, "out")
        self._pusher2.write(False)
        self._pusherPWM = PWM(0, _PWM_PUSHER)
        self._pusherPWM.frequency = 1000
        self._pusherPWM.duty_cycle = 0.5
        self.pusher(False, wait=True)

        self._tempI2C = I2C(_I2C_TEMP)
        
        self._tAmbient = 0.0
        
    def flash(self, state: bool):
        self._flashGpio.write(state)
    
    def fan(self, state: bool):
        self._fanGpio.write(state)

    def power(self, state:bool):
        self._powerGpio.write(state)

    def cooler(self, state: bool):
        self._coolerGpio.write(state)

    # TODO pusher extend and retract
    def pusher(self, state: bool, wait: bool = False):
        pass

    def temps(self) -> (float, float, float):
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as temp:
            tCpu = int(temp.read().strip()) / 1000.0

        tObject = 0.0
        tAmbient = 0.0
        raw = bytearray(3)
        try:
            msg = self._tempI2C.transfer(_TEMP_ADDR, [I2C.Message([_REG_TOBJ1]), I2C.Message(raw, True)])
        except:
            pass
        data = raw[0] | (raw[1] >> 8)
        tObject = float(data) * 0.02 - 273.15

        try:
            msg = self._tempI2C.transfer(_TEMP_ADDR, [I2C.Message([_REG_TA]), I2C.Message(raw, True)])
        except:
            pass
        data = raw[0] | (raw[1] >> 8)
        tAmbient = float(data) * 0.02 - 273.15
        
        self._tAmbient = tAmbient
        
        if tCpu > 55.0 or (tAmbient > 0.0 and tCpu > tAmbient + 20.0):
            self._cpuGpio.write(True)
        elif tCpu < 40.0 or (tAmbient > 0.0 and tCpu < tAmbient + 10.0):
            self._cpuGpio.write(False)
            
        return tCpu, tObject, tAmbient

    def __del__(self):
        self._flashGpio.write(False)
        self._flashGpio.close()
        self._coolerGpio.write(False)
        self._coolerGpio.close()
        self._fanGpio.write(False)
        self._fanGpio.close()
        self._powerGpio.write(False)
        self._powerGpio.close()
        
        self._cpuGpio.write(False)
        self._cpuGpio.close()
        
        self.pusher(False, wait=True)
        self._pusherEnx.close()
        self._pusher1.close()
        self._pusher2.close()
        self._pusherPWM.close()

        if self._tempI2C is not None:
            self._tempI2C.close()

# ps H -o pid -C stream --no-headers
class Camera:
    def __init__(self, peripheral: Peripheral):
        self._peripheral = peripheral
        ps = subprocess.run(['/usr/bin/ps', 'H', '-C', 'stream', '--no-headers', '-o', 'pid'],
                            capture_output=True, text=True)\
                            .stdout.strip()
        if ps != '':
            print(f'Kill streamer PID={ps}', file=sys.stderr)
            os.kill(int(ps), signal.SIGTERM)
        self._Popen = None
        list_devices = subprocess.run(['/usr/bin/v4l2-ctl', '--list-devices'],
                                      capture_output=True, text=True)\
                                 .stdout.splitlines()
        line_no = 0
        usb_device = 0
        for line in list_devices:
            line_no += 1
            if re.search('Camera', line):
                usb_device = line_no

        self._device = None
        if usb_device > 0:
            self._device = list_devices[usb_device].strip()
            print(f'Camera found on {self._device}', file=sys.stderr)
            self.capture()
        else:
            print('No camera', file=sys.stderr)
            shutil.copyfile('/usr/share/octobox/nocamera.jpg', '/var/www/html/image.jpg')
        
    def start(self):
        if self._device is not None:
            self._peripheral.flash(True)
            self._Popen = subprocess.Popen(
                [
                 '/usr/share/octobox/ustreamer',
                 '-d',  self._device,
                 '-r', RESOLUTION,
                 '-m', 'MJPEG',
                 '--device-timeout', '10',
                 '--host=0.0.0.0',
                 '-l'
                 ]
            )
            print(f'Started webcam process {self._Popen.pid}', file=sys.stderr)

    def stop(self):
        if self._Popen is not None:
            print('Stop streamer', file=sys.stderr)
            self._Popen.terminate()
            self._Popen.wait()
        self.capture()

    def refresh(self):
        if self._Popen is not None:
            print('Stop streamer', file=sys.stderr)
            self._Popen.terminate()
            self._Popen.wait()
            sleep(1)
        self.start()

    def capture(self):
        if self._device is not None:
            print('Capture image', file=sys.stderr)
            self._peripheral.flash(True)
            subprocess.run(
                [
                    '/usr/bin/fswebcam',
                    '-d', self._device,
                    '-r', RESOLUTION,
                    '-F', '3', '-S', '2', '--no-banner',
                    '/var/www/html/image.jpg'
                ]
            )
            self._peripheral.flash(False)

    def __del__(self):
        self.stop()
