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

###Set resolution on RPi by editing `/boot/config.txt`:
```
max_usb_current=1
hdmi_group=2 (means computer screen group (not TV))
hdmi_mode=87 (means custom mode)
hdmi_cvt 800 480 60 6 0 0 0 (Sets custom resolution for mode 87)
hdmi_drive=1 (Transmit video over HDMI, but not audio. With sound: 2)
```
In case more info needed, this specific example is for 800x380
https://learn.adafruit.com/adafruit-5-800x480-tft-hdmi-monitor-touchscreen-backpack/raspberry-pi-config
