# Octobox

Box for OrangePi Zero 2W running Octoprint for KP3S

## Server

You need to obtain an API key from Octoprint and store it in api.key in plain text.

### States

| State    | When                   | Look for               | Change to | Also do                            |
|----------|------------------------|------------------------|-----------|------------------------------------|
| Off      | printer is off         | event `power`          | PowerOn   | switch Relay ON and wait 5 seconds |
| PowerOn  | printer is powering on | timeout 5 seconds      | On        |                                    |
| On       | printer is on          | Octo is `Operational`  | Idle      |                                    |
| Idle     | ready for print        | event `power`          | Off       | switch everything OFF              |
|          |                        | Octo is `Printing`     | Printing  | start Camera                       |
| Printing | print job running      | Octo has error         | Off       | switch everything OFF              |
|          |                        | Octo is not `Printing` | Cooling   | stop Camera                        |
|          |                        | event `power`          | Cooling   | cancel Octo print job              |
| Cooling  | print job ended        | Octo has error         | Off       | switch everything OFF              |
|          |                        | bed temp < 35C         | Off       | switch everything OFF              |

### Camera

### Peripheral

### Octo

### Display

### Socket library

### HTML/CGI
