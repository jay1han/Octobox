#!/usr/bin/python3

from time import sleep
from datetime import datetime, timedelta
from enum import Enum
import sys, subprocess

from octo_periph import Peripheral, Camera
from octo_disp import Display
from octo_print import Octoprint
from octo_socket import Socket

tempCold = 35.0

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
        self.c.stop()
        self.p.fan(False)
        self.p.cooler(False)
        self.p.pusher(False)
        self.p.power(False)

    def powerOn(self):
        print('Power On', file=sys.stderr)
        self.d.clearInfo()
        self.p.power(True)
        self.p.fan(True)

    def reboot(self):
        print('Reboot', file=sys.stderr)
        self.powerOff()
        self.p.stop()
        ps = subprocess.run(['/usr/sbin/systemctl', 'reboot'])
        sys.exit(0)
    
    def loop(self):
        octo_state = self.o.getState()
        event = self.s.read()
        tempExt, tempBed = self.o.getTemp()
        tempCpu, tempOut, tempAmb = self.p.temps()

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
                self.c.start()
                sleep(1)
                self.o.connect()
                self.setTimeout(15)
                self.state = State.On
            elif event == 'reboot':
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
            elif event == 'refresh':
                self.c.refresh()
            elif event == 'power':
                print('Power Off', file=sys.stderr)
                self.o.disconnect()
                self.powerOff()
                self.state = State.Off
            elif event == 'reboot':
                self.reboot()

        elif self.state == State.Printing:
            if not octo_state.startswith('Printing'):
                self.state = State.Cooling
            elif event == 'refresh':
                self.c.refresh()
            elif event == 'cancel':
                self.o.cancel()
                self.state = State.Cooling
                
            if self.state == State.Cooling:
                print('Print ended', file=sys.stderr)
                self.o.disconnect()
                self.p.pusher(True)
                self.p.cooler(True)
                self.d.end()
                self.p.power(False)

        elif self.state == State.Cooling:
            if octo_state.startswith('Error'):
                print('Error', file=sys.stderr)
                self.state = State.Off
            elif tempOut < tempCold or tempOut < (tempAmb + 3.0):
                print('Cold', file=sys.stderr)
                self.state = State.Off
            elif event == 'power':
                print('Power Off', file=sys.stderr)
                self.state = State.Off
            elif event == 'refresh':
                self.c.refresh()
                
            if self.state == State.Off:
                self.o.disconnect()
                self.powerOff()
                
        self.d.setTemps(tempAmb, tempExt, tempBed, tempOut, tempCpu,
                        tempCold if self.state == State.Cooling else 0.0)
        
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

    sleep(0.1)
            
octobox = Octobox()

while True:
    octobox.loop()
    sleep(1)

