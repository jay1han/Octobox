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
        self._state = ''
        self._filename = ''
        self._completion = ''
        self._remaining = ''
        self._printtemp = ''
        
        self.jobInfo = JobInfo()
        self.started = None
        self.ended = None
        self.clearInfo()
        self.setState('Printer')

    def writeStatus(self):
        with open('/var/www/html/status.1', 'wt') as status:
            print(f'state={self._state}', file=status)
            print(f'filename={self._filename}', file=status)
            print(f'completion={self._completion}', file=status)
            print(f'remaining={self._remaining}', file=status)
            print(f'printtemp={self._printtemp}', file=status)
        os.rename('/var/www/html/status.1', '/var/www/html/status')

    def setupIP(self):
        list_if = subprocess.run(['/usr/bin/ip', 'addr'], capture_output=True, text=True).stdout
        match = re.search('inet 192\.168\.([.0-9]+)', list_if, flags=re.MULTILINE)
        if match is not None:
            my_ip = f'192.168.{match.group(1)}'
        else:
            my_ip = 'localhost'
        replaceText('/var/www/html/localIP', my_ip)
    
    def setState(self, statusText):
        self._state = statusText
        replaceText('/var/www/html/state', statusText)
        self.writeStatus()

    def setTemps(self, tempAmb, tempExt, tempBed, tempOut, tempCpu, tempCold):
        temps = '<tr>'
        
        if tempExt != 0.0:
            temps += f'<td>Extruder : {tempExt:.1f}&deg;</td>'
        if tempBed != 0.0:
            self._printtemp = f'{tempBed:.1f}'
            temps += f'<td>Bed : {tempBed:.1f}&deg;</td>'
        elif tempOut != 0.0:
            self._printtemp = f'{tempOut:.1f}'
            temps += f'<td>Out : {tempOut:.1f}&deg;'
            if tempCold != 0.0:
                temps += f' ({tempCold:.1f})'
            temps += '</td>'
        temps += f'<td>CPU : {tempCpu:.1f}&deg;</td>'
        if tempAmb != 0.0:
            temps += f'<td>Ambient: {tempAmb:.1f}&deg;</td>'
        temps += '</tr>'
        replaceText('/var/www/html/temps', temps)
        self.writeStatus()

    def setElapsed(self, actualTime):
        jobInfoText = f'<tr><td>File</td><td colspan=3>{self.jobInfo.filename}</td></tr>'
        jobInfoText += f'<tr><td>Actual</td><td>{printTime(actualTime)}</td>'
        jobInfoText += f'<td>Estimated</td><td>{printTime(self.jobInfo.fileTime)}</td></tr>'
        jobInfoText += f'<tr><td>Ended</td><td>{self.ended.strftime("%H:%M")}</td></tr>'
        replaceText('/var/www/html/jobInfo', jobInfoText)
        self.writeStatus()
        
    def setJobInfo(self, jobInfo:JobInfo = None):
        if jobInfo is None:
            jobInfo = self.jobInfo
        else:
            self.jobInfo = jobInfo

        jobInfoText = ''
        
        if jobInfo.filename != '':
            self._filename = jobInfo.filename
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
                    self._completion = f'{donePercent:.0f}'
                    self._remaining = f'{printTime(remainingTime)}'
                
                if self.ended is not None:
                    donePercent = 100.0
                    remainingTime = 0
                    self._completion = ''
                    self._remaining = ''

                jobInfoText = f'<tr><td>File</td><td colspan=5>{jobInfo.filename}</td></tr>'
                jobInfoText += f'<tr><td>Elapsed</td><td>{printTime(jobInfo.currentTime)} ({donePercent:.1f}%)</td>'
                jobInfoText += f'<td>Remaining</td><td>{printTime(remainingTime)}</td>'
                jobInfoText += f'<td>Total</td><td>{printTime(jobInfo.fileTime)}</td></tr>'
                jobInfoText += f'<tr><td>Started</td><td>{self.started.strftime("%H:%M")}</td>'
                jobInfoText += f'<td>Now</td><td>{self.lastNow}</td>'
                jobInfoText += f'<td>ETA</td><td>{eta}</td></tr>'
            
        replaceText('/var/www/html/jobInfo', jobInfoText)
        self.writeStatus()

    def clearInfo(self):
        self.setTemps(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        self.setJobInfo(JobInfo())
        self.started = None
        self.ended = None
        self.writeStatus()

    def start(self):
        self.started = datetime.now()
        
    def end(self):
        self.ended = datetime.now()
        self.setJobInfo()
