import subprocess, os, re, sys, shutil, threading, signal
from time import sleep
from datetime import datetime, timedelta
from periphery import GPIO, I2C, PWM

_GPIO_FLASH  = 76
_GPIO_COOLER = 259
_GPIO_POWER  = 260
_GPIO_CPU    = 258
_GPIO_FAN    = 272
_GPIO_PUSHER = 229     # low active
_GPIO_A1     = 233
_GPIO_A2     = 265

_PWM_PUSHER  = 1

_I2C_TEMP    = "/dev/i2c-0"
_TEMP_ADDR   = 0x5A
_REG_TOBJ1   = 0x07
_REG_TA      = 0x06

RESOLUTION   = '1280x800'
WWW          = '/var/www/html'
    
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
        
        self._pusherEn = GPIO("/dev/gpiochip0", _GPIO_PUSHER, "out")
        self._pusherEn.write(False)
        self._pusher1 = GPIO("/dev/gpiochip0", _GPIO_A1, "out")
        self._pusher1.write(False)
        self._pusher2 = GPIO("/dev/gpiochip0", _GPIO_A2, "out")
        self._pusher2.write(False)
        self._pusherPWM = PWM(0, _PWM_PUSHER)
        self._pusherPWM.frequency = 1000
        self._pusherPWM.duty_cycle = 0.5
        self._pushed = True
        self._thread = None
        self._pushEvent = threading.Event()
        self.pusher(False)

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

    def pushing(self, state: bool):
        print(f'Pusher({state}) started', file=sys.stderr)
        timeout = datetime.now() + timedelta(seconds = 30)
        self._pushed = state
        self._pusherPWM.enable()
        self._pusherEn.write(False)
        self._pusher1.write(state)
        self._pusher2.write(not state)
        self._pusherEn.write(True)
        while datetime.now() < timeout and not self._pushEvent.is_set():
            sleep(0.5)
        self._pusherEn.write(False)
        self._pusherPWM.disable()
        self._pusher1.write(False)
        self._pusher2.write(False)
        self._thread = None
        print(f'Pusher({state}) done', file=sys.stderr)

    def pusher(self, state: bool, wait: bool = False):
        if self._pushed != state:
            if self._thread is not None and self._thread.is_alive():
                self._pushEvent.set()
                self._thread.join(1.0)
                self._pushEvent.clear()

            if wait:
                self.pushing(state)
            else:
                print('Push async', file=sys.stderr)
                self._thread = threading.Thread(target=self.pushing, args=[state], daemon=True)
                self._thread.start()

    def temps(self) -> (float, float, float):
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as temp:
            tCpu = int(temp.read().strip()) / 1000.0

        tObject = 0.0
        tAmbient = 0.0
        dummy = bytearray(3)
        
        msgs = [I2C.Message([_REG_TOBJ1]), I2C.Message(dummy, True)]
        try:
            msg = self._tempI2C.transfer(_TEMP_ADDR, msgs)
        except Exception as e:
            print(e, file=sys.stderr)
        resp = msgs[1].data
        data = resp[0] | (resp[1] << 8)
        tObject = float(data) * 0.02 - 273.15

        msgs = [I2C.Message([_REG_TA]), I2C.Message(dummy, True)]
        try:
            msg = self._tempI2C.transfer(_TEMP_ADDR, msgs)
        except Exception as e:
            print(e, file=sys.stderr)
        resp = msgs[1].data
        data = resp[0] | (resp[1] << 8)
        tAmbient = float(data) * 0.02 - 273.15
        
        self._tAmbient = tAmbient
        
        if tCpu > 55.0 or (tAmbient > 35.0 and tCpu > tAmbient + 20.0):
            self._cpuGpio.write(True)
        elif tCpu < 35.0 or (tAmbient > 25.0 and tCpu < tAmbient + 10.0):
            self._cpuGpio.write(False)
            
        return tCpu, tObject, tAmbient

    def stop(self):
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
        self._pusherEn.close()
        self._pusher1.close()
        self._pusher2.close()
        self._pusherPWM.close()

        if self._tempI2C is not None:
            self._tempI2C.close()

    def __del__(self):
        self.stop()

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
        self._webcam = None
        self._dumper = None
        self._thread = None
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
            self._thread = threading.Thread(target = self.imager, daemon = True)
            self._thread.start()
        else:
            print('No camera', file=sys.stderr)
            shutil.copyfile('/usr/share/octobox/nocamera.jpg', '/var/www/html/image.jpg')

    def imager(self):
        print('Imager thread started', file=sys.stderr)
        while True:
            with os.scandir(WWW) as files:
                dumps = [dump.name[4:-4] for dump in files if dump.name.startswith('dump')]
                seq = sorted(list(map(int, dumps)))
                if len(seq) > 0:
                    os.rename(f'{WWW}/dump{seq[-1]}.jpg', f'{WWW}/image.jpg')
                    del seq[-1]
                    for image in seq:
                        os.remove(f'{WWW}/dump{image}.jpg')
            sleep(1)
        
    def start(self):
        if self._device is not None:
            self._peripheral.flash(True)
            self._webcam = subprocess.Popen(
                [
                    '/usr/share/octobox/ustreamer',
                    '-d',  self._device,
                    '-r', RESOLUTION,
                    '-m', 'MJPEG',
                    '--device-timeout', '10',
                    '--host=0.0.0.0',
                    '-l',
                    '--sink=octobox::jpeg'
                 ]
            )
            print(f'Started webcam process {self._webcam.pid}', file=sys.stderr)
            self._dumper = subprocess.Popen(
                '/usr/share/octobox/ustreamer-dump --sink=octobox::jpeg -o - | ffmpeg -y -i pipe: -r 1 /var/www/html/dump%d.jpg',
                shell=True
            )
            print(f'Started dumper process {self._dumper.pid}', file=sys.stderr)

    def stop(self):
        print('Stop streamer', file=sys.stderr)
        if self._dumper is not None:
            self._dumper.terminate()
            self._dumper.wait()
        if self._webcam is not None:
            self._webcam.terminate()
            self._webcam.wait()
        self.capture()

    def refresh(self):
        self.stop()
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
