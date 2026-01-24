let connection;
const RETRY_DELAY = 1000;
let socket;
let statusEl;
let statusText;
let statusHideTimer;
let lastStatusClass;
let lastStatusText;
const lastSensorDataById = {};
const MAX_STATUS_LEN = 28;

// connection = setInterval(tryConnection, 500);

function tryConnection() {
    console.log(`Trying to connect to hardware monitor server ${SERVER_IP}:${SERVER_PORT}`)

    // Create WebSocket connection.
    //const socket = new WebSocket('ws://127.0.0.1:2346');
    //const socket = new WebSocket('ws://192.168.0.65:2346');
    // const socket = new WebSocket('ws://192.168.0.65:2346');
    // socket = new WebSocket('ws://localhost:2346');
    socket = new WebSocket(`ws://${SERVER_IP}:${SERVER_PORT}`);

    socket.addEventListener('error', function (event) {
        console.log('Error connecting to server, probably because it\'s offline or the script is not running, retrying later');
        setStatus('error', 'DISCONNECTED');
        setTimeout(tryConnection, RETRY_DELAY);
    });

    // Connection opened
    socket.addEventListener('open', function (event) {
        setStatus('ok', '');
        init(socket);
        let requested_sensors = startGraphs();
        requested_sensors = requested_sensors.concat(startFans());
        requested_sensors = requested_sensors.concat(startMeters());

        socket.send(JSON.stringify({
            'action': Actions.SET_SENSORS,
            'requested_sensors': requested_sensors
        }));
    });
}


// socket.addEventListener('error', function (event) {
//     console.log('error');
// });


function init(socket) {
    // Listen for messages
    socket.addEventListener('message', function (event) {
        // console.log('Message from server ', event.data);
        let data;
        try {
            data = JSON.parse(event.data);
        } catch (error) {
            const raw = String(event.data);
            const sanitized = raw
                .replace(/:\s*NaN\b/g, ': null')
                .replace(/:\s*Infinity\b/g, ': null')
                .replace(/:\s*-Infinity\b/g, ': null')
                .replace(/,\s*NaN\b/g, ', null')
                .replace(/,\s*Infinity\b/g, ', null')
                .replace(/,\s*-Infinity\b/g, ', null')
                .replace(/\[\s*NaN\b/g, '[null')
                .replace(/\[\s*Infinity\b/g, '[null')
                .replace(/\[\s*-Infinity\b/g, '[null');
            try {
                data = JSON.parse(sanitized);
            } catch (error2) {
                console.warn('Invalid JSON from server, dropping message');
                setStatus('warn', 'BAD JSON');
                return;
            }
        }

        if (!Array.isArray(data)) {
            return;
        }

        data.forEach(function (sensor_data, index) {
            // console.log(sensor_data)
            if (!sensor_data) {
                return;
            }

            const sensorId = sensor_data[Display.ID];
            const sensorLabel = (sensorId === undefined || sensorId === null) ? 'VALUE' : sensorId;
            const value = sensor_data[Sensor.VALUE];
            if (!Number.isFinite(value)) {
                const fallback = lastSensorDataById[sensorId];
                if (fallback) {
                    sensor_data = fallback;
                    setStatus('warn', `BAD DATA ${sensorLabel}=${String(value)}`);
                } else {
                    setStatus('warn', `BAD DATA ${sensorLabel}=${String(value)}`);
                    return;
                }
            } else if (sensorId !== undefined && sensorId !== null) {
                lastSensorDataById[sensorId] = sensor_data;
            }

            if (charts.hasOwnProperty(sensor_data[Display.ID])) {
                charts[sensor_data[Display.ID]].pushValue(sensor_data);
            } else if (fans.hasOwnProperty(sensor_data[Display.ID])) {
                fans[sensor_data[Display.ID]].pushValue(sensor_data);
            } else if (meters.hasOwnProperty(sensor_data[Display.ID])) {
                meters[sensor_data[Display.ID]].pushValue(sensor_data);
            }
        });
    });
    socket.addEventListener('close', function (event) {
        console.log('close');
        setStatus('error', 'DISCONNECTED');
        setTimeout(tryConnection, RETRY_DELAY);
    });
}

function ensureStatus() {
    if (statusEl) {
        return;
    }
    statusEl = document.createElement('div');
    statusEl.id = 'status';
    statusText = document.createTextNode('');
    statusEl.appendChild(statusText);
    document.body.appendChild(statusEl);
}

function setStatus(level, message) {
    ensureStatus();

    if (lastStatusClass !== level) {
        statusEl.className = level;
        lastStatusClass = level;
    }
    let text = message || '';
    if (text.length > MAX_STATUS_LEN) {
        text = `${text.slice(0, MAX_STATUS_LEN - 3)}...`;
    }
    if (lastStatusText !== text) {
        statusText.nodeValue = text;
        lastStatusText = text;
    }

    if (level === 'ok') {
        statusEl.style.display = 'none';
        return;
    }

    statusEl.style.display = 'block';
    clearTimeout(statusHideTimer);
    if (level === 'warn') {
        statusHideTimer = setTimeout(function () {
            statusEl.style.display = 'none';
        }, 10000);
    }
}
