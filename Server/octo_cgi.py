#!/usr/bin/python3
from urllib.parse import parse_qs
from os import environ
from octo_socket import Socket

socket = Socket()

cgi_args = parse_qs(environ['QUERY_STRING'], keep_blank_values=True)
action = cgi_args['action'][0]

if action == 'power':
    socket.write('POWER')
elif action == 'reboot':
    socket.write('REBOOT')
elif action == 'flash':
    socket.write('FLASH')
elif action == 'camera':
    socket.write('CAMERA')

print("Status: 205\n\n")
