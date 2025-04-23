#!/usr/bin/bash

apt install python3-smbus

mkdir -v /usr/share/octobox
cp -v octo*.py /usr/share/octobox/
cp -v ustreamer/ustreamer.bin /usr/share/octobox/ustreamer
touch /usr/share/octobox/socket

cp -v files/index.html /var/www/html
touch /var/www/html/json

cp -v octocgi.py /var/www/bin/
cp -v files/autossh.env /etc/
cp -v files/octobox.service /etc/systemd/system/
cp -v files/autossh.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable octobox
systemctl restart octobox
systemctl enable autossh
systemctl restart autossh
systemctl status octobox
systemctl status autossh

echo Please create a password file
echo sudo htpasswd /etc/apache2/.htpasswd guest
