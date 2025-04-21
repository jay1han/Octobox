#!/usr/bin/python3

from datetime import datetime, timedelta
from enum import Enum

from octo_cam import Camera
from octo_disp import Display
from octo_periph import Peripheral
from octo_print import Octoprint
from octo_socket import Socket

def readCpuTemp():
    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as temp:
        cpuTemp = int(temp.read().strip()) / 1000.0
    return cpuTemp

class State(Enum):
    OFF      = 0
    IDLE     = 1
    PRINTING = 2
    COOLING  = 3
    COLD     = 4

class Octobox:
    def __init__(self):
        self.state = State.OFF
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
    
    def processPower(self):
        if self.state == State.OFF:
            self.p.relay(True)
            self.d.setState('Printer On')
            self.state = State.IDLE
        elif self.state == State.IDLE:
            self.o.disconnect()
            self.d.setState('Printer Off')
            self.p.relay(False)
            self.state = State.OFF

    def displayJob(self, jobInfo):
        self.d.setJobInfo(jobInfo)
        self.elapsed = jobInfo.currentTime
                
    def loop(self):
        state = self.o.getState()
        event = self.s.read()

        print(f'{self.state} -> "{state}", "{event}"')

        if state.startswith('Offline'):
            self.state = State.OFF
        elif state == 'Operational':
            self.state = State.IDLE
        elif state == 'Printing':
            self.state = State.PRINTING
        elif state == 'Cancelling':
            self.state = State.COOLING

        if event == 'power':
            self.processPower()
        elif event == 'reboot':
            pass

        tempExt, tempBed = self.o.getTemps()
        tempCpu = readCpuTemp()
        tempCold = 0.0
        if self.state == State.COOLING:
            tempCold = 35.0
        self.d.setTemps((tempExt, tempBed, tempCpu, tempCold))
        
        if self.state == State.OFF:
            self.d.setState('Printer Off')
        elif self.state == State.IDLE:
            self.d.setState(state)
        elif self.state == State.PRINTING:
            self.displayJob(self.o.getJobInfo())
        elif self.state == State.COOLING:
            self.d.setElapsed(self.elapsed)
            self.d.setState('Cooling')
        elif self.state == State.COLD:
            self.d.setState('Cold')

octobox = Octobox()

while True:
    octobox.loop()
    sleep(1)

