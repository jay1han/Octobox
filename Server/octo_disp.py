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
        self.lastNow = ''
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

    def setElapsed(self, currentTime):
        jobInfoText = f'<tr><td>File</td><td>{self.jobInfo.filename}</td></tr>'
        jobInfoText += f'<tr><td>Elapsed</td><td>{printTime(currentTime)}</td></tr>'
        jobInfoText += f'<tr><td>Ended</td><td>{self.lastNow}</td></tr>'
        replaceText('/var/www/html/jobInfo', jobInfoText)
        
    def setJobInfo(self, jobInfo:JobInfo):
        if jobInfo.filename == '':
            jobInfoText = ''
            
        else:
            jobInfoText = f'<tr><td>File</td><td>{jobInfo.filename}</td></tr>'

            if jobInfo.fileTime > 0:
                remainingTime = jobInfo.fileTime - jobInfo.currentTime
                eta = (datetime.now() + timedelta(seconds = (remainingTime + 60))).replace(second=0)
                etas = eta.strftime("%H:%M")
                donePercent = 100.0 * jobInfo.currentTime / jobInfo.fileTime
            else:
                remainingTime = 0
                donePercent = 0.0
                etas = ''
            
            self.lastNow = datetime.now().strftime('%H:%M')
        
            jobInfoText += f'<tr><td>Elapsed</td><td>{printTime(jobInfo.currentTime)} ({donePercent:.1f}%)</td></tr>'
            jobInfoText += f'<tr><td>ETA</td><td>{etas}</td></tr>'
            jobInfoText += f'<tr><td>Now</td><td>{self.lastNow}</td></tr>'

        self.jobInfo = jobInfo
        replaceText('/var/www/html/jobInfo', jobInfoText)

    def clearInfo(self):
        self.setTemps([0.0, 0.0, 0.0, 0.0])
        self.setJobInfo(JobInfo())
