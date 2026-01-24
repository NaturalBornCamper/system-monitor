# System Monitor Display

This repo is the **display/UI** for the system monitor. It connects to the `system-reader` service over WebSockets and shows live charts, fan RPM, and meter values on a small (800×400) display, optimized for a Raspberry Pi running Chromium in kiosk mode.

## Raspberry Pi setup (kiosk)

1. Flash **Raspberry Pi OS Lite 64-bit (Trixie)** to the SD card.
2. Update packages, then install the kiosk stack:
   ```
   sudo apt update && sudo apt upgrade -y
   sudo apt install --no-install-recommends cage chromium triggerhappy git -y
   ```
3. Triggerhappy setup (Ctrl+C listener):
   1. Create the trigger file:
      ```
      sudo nano /etc/triggerhappy/triggers.d/kiosk.conf
      ```
   2. Paste this exact line:
      ```
      KEY_LEFTCTRL+KEY_C 1 /usr/bin/pkill -9 cage
      ```
   3. Restart the service:
      ```
      sudo systemctl restart triggerhappy
      ```
4. Create the kiosk scripts:
   1. Ensure the repo is cloned at `/home/pi/system-monitor/`.
   2. Create the start script:
      ```
      nano /home/pi/start_kiosk.sh
      ```
      ```
      #!/bin/bash
      /usr/lib/chromium/chromium \
          --kiosk \
          --no-first-run \
          --noerrdialogs \
          --disable-infobars \
          --autoplay-policy=no-user-gesture-required \
          --ozone-platform=wayland \
          --enable-features=OverlayScrollbar \
          --disable-features=InProductHelp \
          --disable-dev-shm-usage \
          --num-raster-threads=2 \
          --incognito \
          /home/pi/system-monitor/display/graphs_bunker1.html
      ```
   3. Make it executable:
      ```
      chmod +x /home/pi/start_kiosk.sh
      ```
   4. Create the stop script:
      ```
      nano /home/pi/stop_kiosk.sh
      ```
      ```
      #!/bin/bash
      # Kill the compositor (Cage) which automatically closes Chromium
      # We use pkill -9 to ensure it exits immediately, mimicking your Triggerhappy setup
      sudo pkill -9 cage

      echo "Kiosk process terminated. The Pi should now be sitting at the 5-second restart prompt."
      ```
   5. Make it executable:
      ```
      chmod +x /home/pi/stop_kiosk.sh
      ```
5. Autostart from console:
   1. Edit the profile:
      ```
      nano ~/.bash_profile
      ```
      ```
      if [ -z "$DISPLAY" ] && [ "$XDG_VTNR" -eq 1 ]; then
        while true; do
          clear
          echo "KIOSK STARTING IN 5 SECONDS..."
          echo "Press CTRL+C now to stay in terminal."
          sleep 5
          
          # Run Cage with the kiosk script
          cage -s -- /home/pi/start_kiosk.sh
          
          echo "Kiosk Halted. Restarting in 5s (CTRL+C to stay in terminal)..."
          sleep 5
        done
      fi
      ```

## Usage

- **Status badge (`setStatus`)**:
  - `setStatus(...)` is a browser-global helper. Use it from **DevTools on your desktop** while testing (it is not a shell command).
  - `setStatus('ok', '')` hides the badge
  - `setStatus('warn', '...')` shows a warning (auto-hides after 10s)
  - `setStatus('error', '...')` shows an error (stays until cleared)
  - Auto triggers:
    - **BAD JSON**: incoming message could not be parsed even after sanitizing
    - **BAD DATA <id>=<value>**: a sensor value is `NaN`/`Infinity` and the UI falls back to the last known good value
    - **DISCONNECTED**: websocket error or close
- **Start kiosk now**:
  ```
  cage -s -- /home/pi/start_kiosk.sh
  ```
- **Stop kiosk**:
  - Press **Ctrl+C** during the 5-second countdown to stay in terminal
  - Or run:
    ```
    /home/pi/stop_kiosk.sh
    ```
  - Or press **Ctrl+C** while kiosk is running (Triggerhappy kills Cage)
- **Logs / output**:
  - Start/stop script output prints to the active console (TTY1)
  - To view Chromium output, run `/home/pi/start_kiosk.sh` manually
