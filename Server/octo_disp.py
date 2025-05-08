import os
import re
import subprocess
from datetime import datetime, timedelta

from octo_print import JobInfo

def printTime(seconds):
    if seconds == 0: return ''
    else:
        return (datetime.now().replace(hour=0, minute=0, second=0) + timedelta(seconds=int(seconds))).strftime('%H:%M')

def replaceText(filename, text):
    with open(f"{filename}.1", "w") as newfile:
        print(text, file=newfile)
    os.replace(f"{filename}.1", filename)

class Display:
    def __init__(self):
        self.jobInfo = JobInfo()
        self.started = None
        self.ended = None
        self.clearInfo()
        self.setState('Printer')

    def setupIP(self):
        list_if = subprocess.run(['/usr/bin/ip', 'addr'], capture_output=True, text=True).stdout
        match = re.search('inet 192\.168\.([.0-9]+)', list_if, flags=re.MULTILINE)
        if match is not None:
            my_ip = f'192.168.{match.group(1)}'
        else:
            my_ip = 'localhost'
        replaceText('/var/www/html/localIP', my_ip)
    
    def setState(self, statusText):
        replaceText('/var/www/html/state', statusText)

    def setTemps(self, temps):
        tempExt, tempBed, tempCpu, tempCold = temps
        if tempExt == 0.0:
            temps = f'<tr><td>Extruder</td><td></td></tr><tr><td>Bed</td><td></td></tr>'
        else:
            temps = f'<tr><td>Extruder</td><td>{tempExt:.1f}&deg;</td></tr>'
            if tempCold == 0.0:
                temps += f'<tr><td>Bed</td><td>{tempBed:.1f}&deg;</td></tr>'
            else:
                temps += f'<tr><td>Bed</td><td>{tempBed:.1f}&deg;({tempCold:.1f})</td></tr>'
        temps += f'<tr><td>CPU</td><td>{tempCpu:.1f}&deg;</td></tr>'
        replaceText('/var/www/html/temps', temps)

    def setElapsed(self, actualTime):
        jobInfoText = f'<tr><td>File</td><td>{self.jobInfo.filename}</td></tr>'
        jobInfoText += f'<tr><td>Actual/Estimated</td><td>{printTime(actualTime)}/{printTime(self.jobInfo.fileTime)}</td></tr>'
        jobInfoText += f'<tr><td>Ended</td><td>{self.ended.strftime("%H:%M")}</td></tr>'
        replaceText('/var/www/html/jobInfo', jobInfoText)
        
    def setJobInfo(self, jobInfo:JobInfo = None):
        if jobInfo is None:
            jobInfo = self.jobInfo
        else:
            self.jobInfo = jobInfo

        jobInfoText = ''
        
        if jobInfo.filename != '':
            jobInfoText = f'<tr><td>File</td><td>{jobInfo.filename}</td></tr>'
            self.lastNow = datetime.now().strftime('%H:%M')

            if self.started is not None:
                remainingTime = 0
                donePercent = 0.0
                eta = ''
                
                if jobInfo.fileTime > 0:
                    remainingTime = jobInfo.fileTime - jobInfo.currentTime
                    eta = (self.started + timedelta(seconds = jobInfo.fileTime)).strftime('%H:%M')
                    donePercent = 100.0 * jobInfo.currentTime / jobInfo.fileTime
                    
                if self.ended is not None:
                    donePercent = 100.0
                    remainingTime = 0
                    
                jobInfoText += f'<tr><td>Elapsed/Remaining/Total</td>'
                jobInfoText += f'<td>{printTime(jobInfo.currentTime)}/{printTime(remainingTime)}/{printTime(jobInfo.fileTime)} ({donePercent:.1f}%)</td></tr>'
                jobInfoText += f'<tr><td>Started/Now/ETA</td>'
                jobInfoText += f'<td>{self.started.strftime("%H:%H")}/{self.lastNow}/{eta}</td></tr>'
            
        replaceText('/var/www/html/jobInfo', jobInfoText)

    def clearInfo(self):
        self.setTemps([0.0, 0.0, 0.0, 0.0])
        self.setJobInfo(JobInfo())
        self.started = None
        self.ended = None

    def start(self):
        self.started = datetime.now()
        
    def end(self):
        self.ended = datetime.now()
        self.setJobInfo()
        
