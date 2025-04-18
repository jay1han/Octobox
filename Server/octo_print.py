
import json
from urllib.request import urlopen, Request

APIKEY = "E8D71F8A9B9947C49A2740591E833101"

class JobInfo:
    def __init__(self,
                 file='',
                 currentTime = 0,
                 remainingTime = 0,
                 fileEstimate = 0,
                 donePercent = 0):
        self.filename = file
        self.currentTime = currentTime
        self.remainingTime = remainingTime
        self.fileEstimate = fileEstimate
        self.donePercent = donePercent

    def get(self):
        return self.filename, self.currentTime, self.remainingTime, self.fileEstimate, self.donePercent

def query(command):
    try:
        with urlopen(f'http://localhost:5000/api/{command}?apikey={APIKEY}') as jobapi:
            return json.loads(jobapi.read())
    except OSError:
        return None

def request(command, data):
    r = Request(f'http://localhost:5000/api/{command}',
                headers={
                    'X-Api-Key': APIKEY,
                    'Content-Type': 'application/json'
                    }
                )
    try:
        urlopen(r, bytes(data, 'ascii'))
    except OSError:
        pass

class Octoprint:
    def __init__(self):
        pass

    @staticmethod
    def query(command):
        try:
            with urlopen(f'http://localhost:5000/api/{command}?apikey={APIKEY}') as jobapi:
                return json.loads(jobapi.read())
        except OSError:
            return None

    @staticmethod
    def request(command, data):
        r = Request(f'http://localhost:5000/api/{command}',
                    headers =
                        {
                         'X-Api-Key': APIKEY,
                        'Content-Type': 'application/json'
                        }
                    )
        try:
            urlopen(r, bytes(data, 'ascii'))
        except OSError:
            pass

    def disconnect(self):
        self.request('connection', '{ "command": "disconnect" }')

    def connect(self):
        self.request('connection', '{ "command": "connect" }')

    def getState(self):
        # Offline
        # Operational
        # Printing
        # Cancelling
        job = self.query('job')
        if job is None:
            return 'Disconnected'
        else:
            return job['state']

    def getTemps(self):
        printer = self.query('printer')
        if printer is None:
            return 0, 0
        else:
            tempExt = 0
            if printer['temperature'].get('tool0') is not None:
                tempExt = float(printer['temperature']['tool0']['actual'])
            tempBed = 0
            if printer['temperature'].get('bed') is not None:
                tempBed = float(printer['temperature']['bed']['actual'])
            return tempExt, tempBed

    def getJobInfo(self):
        job = self.query('job')
        if job is None:
            return JobInfo()
        else:
            file = job['job']['file']['name']
            if file is None:
                file = ''
            else:
                file =  file.removesuffix('.gcode')

            fileEstimate = job['job']['estimatedPrintTime']
            donePercent = job['progress']['completion']
            currentTime = job['progress']['printTime']
            remainingTime = job['progress']['printTimeLeft']

            if fileEstimate is None: fileEstimate = 0
            if donePercent is None: donePercent = 0
            if remainingTime is None: remainingTime = 0
            if currentTime is None: currentTime = 0

            return JobInfo(file, currentTime, remainingTime, fileEstimate, donePercent)

    def __del__(self):
        pass
