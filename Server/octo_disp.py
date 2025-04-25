import os
import re
import subprocess
from datetime import datetime, timedelta

from octo_print import JobInfo

def printTime0(seconds):
    if seconds == 0:
        return ''
    return (datetime.now().replace(hour=0, minute=0, second=0) + timedelta(seconds=int(seconds))).strftime('%H:%M')

def printTime(seconds):
    text = printTime0(seconds)
    if text == '':
        return '..:..'
    return text

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
        jobInfoText = '<tr><td>File</td><td></td></tr>'
        jobInfoText += f'<tr><td>Elapsed</td><td>{printTime0(currentTime)}</td></tr>'
        jobInfoText += '<tr><td>ETA</td><td></td></tr>'
        jobInfoText += f'<tr><td>Now</td><td>{self.lastNow}</td></tr>'
        
    def setJobInfo(self, jobInfo:JobInfo):
        filename, currentTime, remainingTime, fileEstimate, donePercent = jobInfo.get()
        if filename != '':
            jobInfoText = f'<tr><td>File</td><td>{filename}</td></tr>'
        else:
            jobInfoText = f'<tr><td>File</td><td>{self.jobInfo.filename}</td></tr>'

        if currentTime > 0:
            jobInfoText += f'<tr><td>Elapsed</td><td>{printTime0(currentTime)} ({donePercent:.1f}%)</td></tr>'

            eta2 = eta1 = datetime.now()
            if remainingTime != 0:
                eta1 = (datetime.now() + timedelta(seconds = (remainingTime + 60))).replace(second=0)
            if fileEstimate != 0:
                eta2 = (datetime.now() - timedelta(seconds = currentTime) + timedelta(seconds = (fileEstimate + 60))).replace(second=0)
            if eta2 < eta1:
                eta = eta1
                eta1 = eta2
                eta2 = eta

            etas = '(No estimate)'
            if eta1 > datetime.now():
                etas = f'{eta1.strftime("%H:%M")} ~ {eta2.strftime("%H:%M")}'
            elif eta2 > datetime.now():
                etas = eta2.strftime("%H:%M")

            jobInfoText += f'<tr><td>ETA</td><td>{etas}</td></tr>'
            self.lastNow = datetime.now().strftime("%H:%M")
            jobInfoText += f'<tr><td>Now</td><td>{self.lastNow}</td></tr>'
            
        else:
            jobInfoText += f'<tr><td>Elapsed</td><td>{printTime0(currentTime)}</td></tr>'
            jobInfoText += f'<tr><td>ETA</td><td> </td></tr>'
            if self.jobInfo.filename != '':
                jobInfoText += f'<tr><td>Ended</td><td>{self.lastNow}</td></tr>'
            else:
                jobInfoText += f'<tr><td>Ended</td><td> </td></tr>'

        self.jobInfo = jobInfo
        replaceText('/var/www/html/jobInfo', jobInfoText)

    def clearInfo(self):
        self.setTemps([0.0, 0.0, 0.0, 0.0])
        self.setJobInfo(JobInfo('', 0.0, 0.0, 0.0, 0.0))
