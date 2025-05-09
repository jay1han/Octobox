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
        temps = '<tr>'
        
        if tempExt != 0.0:
            temps += f'<td>Extruder : {tempExt:.1f}&deg;</td>'
            temps += f'<td>Bed : {tempBed:.1f}&deg;'
            if tempCold != 0.0:
                temps += f'({tempCold:.1f})'
        temps += '</td>'
        temps += f'<td>CPU : {tempCpu:.1f}&deg;</td></tr>'
        replaceText('/var/www/html/temps', temps)

    def setElapsed(self, actualTime):
        jobInfoText = f'<tr><td>File</td><td colspan=3>{self.jobInfo.filename}</td></tr>'
        jobInfoText += f'<tr><td>Actual</td><td>{printTime(actualTime)}</td>'
        jobInfoText += f'<td>Estimated</td><td>{printTime(self.jobInfo.fileTime)}</td></tr>'
        jobInfoText += f'<tr><td>Ended</td><td>{self.ended.strftime("%H:%M")}</td></tr>'
        replaceText('/var/www/html/jobInfo', jobInfoText)
        
    def setJobInfo(self, jobInfo:JobInfo = None):
        if jobInfo is None:
            jobInfo = self.jobInfo
        else:
            self.jobInfo = jobInfo

        jobInfoText = ''
        
        if jobInfo.filename != '':
            self.lastNow = datetime.now().strftime('%H:%M')

            if self.started is None:
                if jobInfo.fileTime == 0:
                    jobInfoText = f'<tr><td>File</td><td colspan=3>{jobInfo.filename}</td></tr>'
                else:
                    eta = (datetime.now() + timedelta(seconds = jobInfo.fileTime)).strftime('%H:%M')
                    jobInfoText = f'<tr><td>File</td><td colspan=3>{jobInfo.filename}</td></tr>'
                    jobInfoText += f'<tr><td>Estimated</td><td>{printTime(jobInfo.fileTime)}</td></tr>'
                    jobInfoText += f'<tr><td>Now</td><td>{datetime.now().strftime("%H:%M")}</td>'
                    jobInfoText += f'<td>ETA</td><td>{eta}</td></tr>'
                       
            else:
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
                    
                jobInfoText = f'<tr><td>File</td><td colspan=5>{jobInfo.filename}</td></tr>'
                jobInfoText += f'<tr><td>Elapsed</td><td>{printTime(jobInfo.currentTime)} ({donePercent:.1f}%)</td>'
                jobInfoText += f'<td>Remaining</td><td>{printTime(remainingTime)}</td>'
                jobInfoText += f'<td>Total</td><td>{printTime(jobInfo.fileTime)}</td></tr>'
                jobInfoText += f'<tr><td>Started</td><td>{self.started.strftime("%H:%M")}</td>'
                jobInfoText += f'<td>Now</td><td>{self.lastNow}</td>'
                jobInfoText += f'<td>ETA</td><td>{eta}</td></tr>'
            
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
        
