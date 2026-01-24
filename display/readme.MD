# System Monitor Display

## `setStatus` (visual status badge)

The UI shows a small status badge in the top‑right. It’s used for quick on‑screen diagnostics when you don’t have the console open.

### What it does
- `setStatus('ok', '')` hides the badge
- `setStatus('warn', '...')` shows a **warning** badge (auto‑hides after 10s)
- `setStatus('error', '...')` shows an **error** badge (stays until cleared)

### How to use it (from DevTools console on your desktop)
```js
setStatus('warn', 'BAD DATA cpu-load=NaN');
setStatus('error', 'DISCONNECTED');
setStatus('ok', '');
```

### When it’s triggered automatically
- **BAD JSON**: incoming message could not be parsed even after sanitizing
- **BAD DATA <id>=<value>**: a sensor value is `NaN`/`Infinity` and the UI falls back to the last known good value
- **DISCONNECTED**: websocket error or close

## Raspberry Pi setup (kiosk)

1. Flash **Raspberry Pi OS Lite 64‑bit (Trixie)** to the SD card.
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
  - `setStatus('ok', '')` hides the badge
  - `setStatus('warn', '...')` shows a warning (auto-hides after 10s)
  - `setStatus('error', '...')` shows an error (stays until cleared)
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
