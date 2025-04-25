#!/usr/bin/python3

from time import sleep
from datetime import datetime, timedelta
from enum import Enum

from octo_periph import Peripheral, Camera
from octo_disp import Display
from octo_print import Octoprint
from octo_socket import Socket

def readCpuTemp():
    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as temp:
        cpuTemp = int(temp.read().strip()) / 1000.0
    return cpuTemp

class State(Enum):
    Off      = 0
    On       = 1
    Idle     = 2
    Printing = 3
    Cooling  = 4

class Octobox:
    def __init__(self):
        self.state = State.Off
        self.octo = ''
        self.timeout = None
        self.elapsed = 0

        self.p = Peripheral()
        self.c = Camera(self.p)
        self.o = Octoprint()
        self.d = Display()
        self.s = Socket()

    def __del__(self):
        pass

    def setTimeout(self, seconds):
        if seconds == 0:
            self.timeout = None
        else:
            self.timeout = datetime.now() + timedelta(seconds = seconds)

    def isTimedout(self):
        if self.timeout is not None and datetime.now() > self.timeout:
            self.timeout = None
            print('Timeout')
            return True
        else:
            return False

    def powerOff(self):
        self.p.relay(False)
        self.p.fan(False)
        self.c.stop()

    def powerOn(self):
        self.p.relay(True)

    def reboot(self):
        # TODO
        pass
    
    def loop(self):
        state = self.o.getState()
        event = self.s.read()
        tempExt, tempBed = self.o.getTemps()
        tempCpu = readCpuTemp()

        if event != '' or self.octo != state:
            print(f'State {self.state}: State "{state}", Event "{event}"')
            self.octo = state

        if self.state == State.Off:
            if event == 'refresh':
                self.c.capture()
            elif event == 'power':
                self.powerOn()
                sleep(1)
                self.o.connect()
                self.setTimeout(15)
                self.state = State.On
            elif event == 'reboot':
                self.powerOff()
                self.reboot()

        elif self.state == State.On:
            if event == 'refresh':
                self.c.capture()
            elif state.startswith('Operational'):
                self.setTimeout(0)
                self.state = State.Idle
            elif state.startswith('Error') or self.isTimedout():
                self.o.disconnect()
                self.powerOff()
                self.state = State.Off

        elif self.state == State.Idle:
            if event == 'refresh':
                self.c.capture()
            elif state.startswith('Printing'):
                self.c.start()
                self.state = State.Printing
            elif state.startswith('Error') or event == 'power':
                self.o.disconnect()
                self.powerOff()
                self.state = State.Off
            elif event == 'reboot':
                self.powerOff()
                self.reboot()

        elif self.state == State.Printing:
            if not state.startswith('Printing'):
                self.p.fan(True)
                self.state = State.Cooling
            elif event == 'cancel':
                self.o.cancel()
                self.p.fan(True)
                self.state = State.Cooling

        elif self.state == State.Cooling:
            if event == 'refresh':
                self.c.capture()
            elif state.startswith('Error') or tempBed < 35.0 or event == 'power':
                self.o.disconnect()
                self.powerOff()
                self.state = State.Off
                
        tempCold = 0.0
        if self.state == State.Cooling:
            tempCold = 35.0
        self.d.setTemps((tempExt, tempBed, tempCpu, tempCold))
        
        if self.state == State.Off:
            self.d.setState('Printer Off')
        elif self.state == State.Idle:
            self.d.setState(state)
        elif self.state == State.Printing:
            self.d.setState(state)
            jobInfo = self.o.getJobInfo()
            self.elapsed = jobInfo.currentTime
            self.d.setJobInfo(jobInfo)
        elif self.state == State.Cooling:
            self.d.setState('Cooling')
            self.d.setElapsed(self.elapsed)

octobox = Octobox()

while True:
    octobox.loop()
    sleep(1)

