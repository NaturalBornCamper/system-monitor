###Create url shortcut on Desktop  
https://www.raspberrypi.org/forums/viewtopic.php?t=22235  
Create a text file in  
`/home/pi/Desktop - called <name>.desktop`  
Then put this content
```
[Desktop Entry]
Type=Link
Name=Raspberry Pi website
Comment=The infamous Raspberry Pi computer
Icon=/home/pi/raspberrypi.jpg
URL=http://www.raspberrypi.org
```


###To autostart Chromium in fullscreen on RPi with the monitor  
https://raspberrypi.stackexchange.com/a/76336/73608  
`sudo nano /etc/xdg/lxsession/LXDE-pi/autostart`

Then add at the end:  
```
@xset -dpms
@xset s noblank
@chromium-browser --kiosk file:///home/pi/path/to/file.html
```

###Set custom resolution on RPi (This specific example for 800x480)
https://learn.adafruit.com/adafruit-5-800x480-tft-hdmi-monitor-touchscreen-backpack/raspberry-pi-config
