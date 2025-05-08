#!/usr/bin/python3

from time import sleep
from datetime import datetime, timedelta
from enum import Enum
import sys

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
        self.octo_state = ''
        self.timeout = None
        self.elapsed = 0

        self.p = Peripheral()
        self.c = Camera(self.p)
        self.o = Octoprint()
        self.d = Display()
        self.s = Socket()

        self.d.setState('Printer Off')

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
            print('Timeout', file=sys.stderr)
            return True
        else:
            return False

    def powerOff(self):
        print('Power Off', file=sys.stderr)
        self.p.relay(False)
        self.p.fan(False)
        self.c.stop()
        self.d.clearInfo()

    def powerOn(self):
        print('Power On', file=sys.stderr)
        self.p.relay(True)

    def reboot(self):
        print('Reboot', file=sys.stderr)
    
    def loop(self):
        octo_state = self.o.getState()
        event = self.s.read()
        tempExt, tempBed = self.o.getTemps()
        tempCpu = readCpuTemp()

        if event != '' or self.octo_state != octo_state:
            print(f'State {self.state}: State "{octo_state}", Event "{event}"', file=sys.stderr)
            self.octo_state = octo_state

        if self.state == State.Off:
            if octo_state.startswith('Operational'):
                self.setTimeout(0)
                self.state = State.Idle
            elif event == 'refresh':
                self.c.capture()
            elif event == 'power':
                self.powerOn()
                sleep(1)
                self.o.connect()
                self.setTimeout(15)
                self.c.start()
                self.state = State.On
            elif event == 'reboot':
                self.powerOff()
                self.reboot()

        elif self.state == State.On:
            if event == 'refresh':
                self.c.capture()
            elif octo_state.startswith('Operational'):
                self.setTimeout(0)
                self.state = State.Idle
            elif octo_state.startswith('Error') or octo_state.startswith('Offline'):
                print('Error', file=sys.stderr)
                self.o.disconnect()
                self.powerOff()
                self.state = State.Off
            elif self.isTimedout():
                self.o.disconnect()
                self.powerOff()
                self.state = State.Off

        elif self.state == State.Idle:
            if octo_state.startswith('Printing'):
                print('Print start', file=sys.stderr)
                self.state = State.Printing
                self.d.start()
            elif octo_state.startswith('Error') or octo_state.startswith('Offline'):
                print('Error', file=sys.stderr)
                self.o.disconnect()
                self.powerOff()
                self.state = State.Off
            elif event == 'power':
                print('Power Off', file=sys.stderr)
                self.o.disconnect()
                self.powerOff()
                self.state = State.Off
            elif event == 'reboot':
                self.powerOff()
                self.reboot()

        elif self.state == State.Printing:
            if not octo_state.startswith('Printing'):
                self.p.fan(True)
                self.state = State.Cooling
            elif event == 'cancel':
                self.o.cancel()
                self.c.stop()
                self.c.capture()
                self.p.fan(True)
                self.state = State.Cooling
            if self.state == State.Cooling:
                print('Print ended', file=sys.stderr)
                self.d.end()

        elif self.state == State.Cooling:
            if octo_state.startswith('Error') \
              or octo_state.startswith('Offline') \
              or tempBed < 35.0 \
              or event == 'power':
                print('Power Off', file=sys.stderr)
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
            self.d.setState(octo_state)
            jobInfo = self.o.getJobInfo()
            self.d.setJobInfo(jobInfo)
        elif self.state == State.Printing:
            self.d.setState(octo_state)
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

