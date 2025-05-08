#!/usr/bin/bash

apt install autossh python3-periphery apache2 fswebcam

usermod -aG octoprint www-data
chmod -Rv g+r /home/octoprint/.octoprint/uploads

mkdir -v /usr/share/octobox
cp -pv octo*.py /usr/share/octobox/
cp -pv ustreamer/ustreamer.bin /usr/share/octobox/ustreamer
touch /usr/share/octobox/socket

cp -v files/index.html /var/www/html
cp -v files/localIP /var/www/html

cp -pv octo_cgi.py /var/www/bin/
cp -v files/octobox.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable octobox
systemctl restart octobox
systemctl status octobox

# cp -v files/autossh.env /etc/
# cp -v files/autossh.service /etc/systemd/system/
# systemctl enable autossh
# systemctl restart autossh
# systemctl status autossh
# iptables -t nat -A PREROUTING -p tcp -d 192.168.0.8 --dport 8080 -j DNAT --to-destination 127.0.0.1

cat files/localIP
echo "Please check IP address above"
echo "Please set up Octoprint API key in file /usr/share/octobox/api.key"
echo "Please create a password file"
echo "    sudo htpasswd /etc/apache2/.htpasswd guest"
