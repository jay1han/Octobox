import json, re, sys
from urllib.request import urlopen, Request

APIKEY  = ''
UPLOADS = '/home/octoprint/.octoprint/uploads'

class JobInfo:
    def __init__(self,
                 filename= '',
                 currentTime = 0,
                 fileTime = 0):
        self.filename = filename
        self.currentTime = currentTime
        self.fileTime = fileTime

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
        global APIKEY
        with open('api.key') as key:
            APIKEY = key.readline().strip()

    @staticmethod
    def query(command):
        try:
            with urlopen(f'http://localhost:5000/api/{command}?apikey={APIKEY}') as jobapi:
                return json.loads(jobapi.read())
        except:
            return None

    @staticmethod
    def request(command, data):
        r = Request(f'http://localhost:5000/api/{command}',
                    headers = {
                        'X-Api-Key': APIKEY,
                        'Content-Type': 'application/json'
                        }
                    )
        try:
            urlopen(r, bytes(data, 'ascii'))
        except:
            pass

    def disconnect(self):
        print('Disconnect', file=sys.stderr)
        self.request('connection', '{ "command": "disconnect" }')

    def connect(self):
        print('Connect', file=sys.stderr)
        self.request('connection', '{ "command": "connect" }')

    def cancel(self):
        print('Cancel', file=sys.stderr)
        self.request('job', '{ "command": "cancel" }')

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

    def getTemp(self):
        printer = self.query('printer')
        if printer is None:
            return 0.0
        else:
            tempExt = 0
            if printer['temperature'].get('tool0') is not None \
              and printer['temperature']['tool0'].get('actual') is not None:
                tempExt = float(printer['temperature']['tool0']['actual'])
            return tempExt

    def getJobInfo(self):
        job = self.query('job')
        if job is None:
            return JobInfo()
        
        else:
            fileTime = 0
            filename = job['job']['file']['name']
            if filename is None:
                filename = ''
            else:
                lines = 0
                with open(f'{UPLOADS}/{filename}', 'r') as gcode:
                    for line in gcode:
                        lines += 1
                        if lines > 20: break
                        match = re.match(';TIME:([0-9]+)', line)
                        if match is not None:
                            fileTime = int(match.group(1))
                            break
                filename =  filename.removesuffix('.gcode')

            currentTime = job['progress']['printTime']
            if currentTime is None: currentTime = 0

            return JobInfo(filename, currentTime, fileTime)

    def __del__(self):
        pass
