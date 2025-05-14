from periphery import GPIO
import signal
import subprocess, os, re, sys
from time import sleep

_GPIO_FLASH = 76
_GPIO_FAN   = 259
_GPIO_POWER = 260

RESOLUTION  = '1280x800'
    
class Peripheral:
    def __init__(self):
        self._flash = 0
        self._flashGpio = GPIO("/dev/gpiochip0", _GPIO_FLASH, "out")
        self._flashGpio.write(False)
        self._fan = 0
        self._fanGpio = GPIO("/dev/gpiochip0", _GPIO_FAN, "out")
        self._fanGpio.write(False)
        self._relay = 0
        self._relayGpio = GPIO("/dev/gpiochip0", _GPIO_POWER, "out")
        self._relayGpio.write(False)
        
    def flash(self, state = None) -> int:
        if state is not None:
            if state == -1:
                self._flash = 1 - self._flash
            else:
                self._flash = state
            self._flashGpio.write(bool(self._flash))
        return self._flash
    
    def fan(self, state = None) -> int:
        if state is not None:
            if state == -1:
                self._fan = 1 - self._fan
            else:
                self._fan = state
            self._fanGpio.write(bool(self._fan))
        return self._fan

    def relay(self, state = None) -> int:
        if state is not None:
            if state == -1:
                self._relay = 1 - self._relay
            else:
                self._relay = state
            self._relayGpio.write(bool(self._relay))
        return self._relay

    def __del__(self):
        self.flash(0)
        self.fan(0)
        self.relay(0)

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

        self._device = list_devices[usb_device].strip()
        print(f'Camera found on {self._device}', file=sys.stderr)
        self.capture()
        
    def start(self):
        self._peripheral.flash(1)
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
        print('Capture image', file=sys.stderr)
        self._peripheral.flash(1)
        subprocess.run(
            [
                '/usr/bin/fswebcam',
                '-d', self._device,
                '-r', RESOLUTION,
                '-F', '3', '-S', '2', '--no-banner',
                '/var/www/html/image.jpg'
            ]
        )
        self._peripheral.flash(0)

    def __del__(self):
        self.stop()
