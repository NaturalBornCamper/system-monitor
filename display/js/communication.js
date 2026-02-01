let socket;
let reconnectTimer;
let connectTimeoutTimer;
let watchdogTimer;

// Reconnect schedule:
// - First 5 minutes: retry every 1000ms
// - Next 1 hour:     retry every 10000ms
// - After that:      retry every 100000ms until reconnected
const FAST_RETRY_MS = 1000;
const FAST_RETRY_DURATION_MS = 5 * 60 * 1000;
const MID_RETRY_MS = 10000;
const MID_RETRY_DURATION_MS = 60 * 60 * 1000;
const SLOW_RETRY_MS = 100000;

const CONNECT_TIMEOUT_MS = 8000;
const STALE_CONNECTION_MS = 20000;
const WATCHDOG_INTERVAL_MS = 2000;

let disconnectStartedAt = 0;
let reconnectAttempt = 0;
let lastMessageAt = 0;
let statusEl;
let statusText;
let statusHideTimer;
let lastStatusClass;
let lastStatusText;
const lastSensorDataById = {};
const MAX_STATUS_LEN = 28;

/**
 * Close the current WebSocket (if any) and clear the global reference.
 * Safe to call multiple times.
 */
function safeCloseSocket() {
    if (!socket) {
        return;
    }
    try {
        socket.close();
    } catch (error) {
        // ignore
    }
    socket = null;
}

/**
 * Clear any timers tied to the current connection lifecycle.
 * (Connect timeout + stale-data watchdog).
 */
function clearConnectionTimers() {
    clearTimeout(connectTimeoutTimer);
    connectTimeoutTimer = null;

    clearInterval(watchdogTimer);
    watchdogTimer = null;
}

/**
 * Schedule the next reconnect attempt (only one pending at a time).
 * Uses the configured reconnect schedule based on how long we've been disconnected.
 */
function scheduleReconnect() {
    if (reconnectTimer) {
        return;
    }

    clearConnectionTimers();
    safeCloseSocket();

    const now = Date.now();
    if (!disconnectStartedAt) {
        disconnectStartedAt = now;
    }

    const elapsedMs = now - disconnectStartedAt;
    const phase2StartMs = FAST_RETRY_DURATION_MS;
    const phase3StartMs = FAST_RETRY_DURATION_MS + MID_RETRY_DURATION_MS;
    const delay =
        elapsedMs < phase2StartMs ? FAST_RETRY_MS :
            elapsedMs < phase3StartMs ? MID_RETRY_MS :
                SLOW_RETRY_MS;

    reconnectAttempt += 1;
    const attemptLabel = reconnectAttempt > 1 ? `DISCONNECTED #${reconnectAttempt}` : 'DISCONNECTED';
    setStatus('error', attemptLabel);

    reconnectTimer = setTimeout(function () {
        reconnectTimer = null;
        tryConnection();
    }, delay);
}

/**
 * Try to establish a WebSocket connection to SERVER_IP:SERVER_PORT.
 * On success, sends the sensor subscription and starts a watchdog to detect "stale" connections.
 */
function tryConnection() {
    console.log(`Trying to connect to hardware monitor server ${SERVER_IP}:${SERVER_PORT}`)

    // Create WebSocket connection.
    //const socket = new WebSocket('ws://127.0.0.1:2346');
    //const socket = new WebSocket('ws://192.168.0.65:2346');
    // const socket = new WebSocket('ws://192.168.0.65:2346');
    // socket = new WebSocket('ws://localhost:2346');

    clearTimeout(reconnectTimer);
    reconnectTimer = null;
    clearConnectionTimers();
    safeCloseSocket();

    let ws;
    try {
        ws = new WebSocket(`ws://${SERVER_IP}:${SERVER_PORT}`);
    } catch (error) {
        console.warn('WebSocket constructor failed, retrying later');
        scheduleReconnect();
        return;
    }
    socket = ws;

    connectTimeoutTimer = setTimeout(function () {
        if (ws !== socket) {
            return;
        }
        if (ws.readyState === WebSocket.CONNECTING) {
            console.warn('WebSocket connect timeout, retrying later');
            scheduleReconnect();
        }
    }, CONNECT_TIMEOUT_MS);

    ws.addEventListener('close', function (event) {
        console.log('close');
        scheduleReconnect();
    });

    ws.addEventListener('error', function (event) {
        console.log('Error connecting to server, probably because it\'s offline or the script is not running, retrying later');
        scheduleReconnect();
    });

    // Connection opened
    ws.addEventListener('open', function (event) {
        if (ws !== socket) {
            return;
        }
        clearConnectionTimers();
        disconnectStartedAt = 0;
        reconnectAttempt = 0;
        lastMessageAt = Date.now();

        setStatus('ok', '');
        init(ws);

        // Defensive: if one UI section fails to init (bad config / missing settings),
        // still subscribe to the other sensors instead of breaking the whole connection.
        let requested_sensors = [];
        try {
            if (typeof startGraphs === 'function') {
                requested_sensors = requested_sensors.concat(startGraphs() || []);
            }
        } catch (error) {
            console.warn('startGraphs() failed');
        }
        try {
            if (typeof startFans === 'function') {
                requested_sensors = requested_sensors.concat(startFans() || []);
            }
        } catch (error) {
            console.warn('startFans() failed');
        }
        try {
            if (typeof startMeters === 'function') {
                requested_sensors = requested_sensors.concat(startMeters() || []);
            }
        } catch (error) {
            console.warn('startMeters() failed');
        }

        try {
            ws.send(JSON.stringify({
                'action': Actions.SET_SENSORS,
                'requested_sensors': requested_sensors
            }));
        } catch (error) {
            console.warn('Failed sending sensor request, retrying later');
            scheduleReconnect();
            return;
        }

        watchdogTimer = setInterval(function () {
            if (ws !== socket) {
                return;
            }
            if (ws.readyState !== WebSocket.OPEN) {
                return;
            }
            const now = Date.now();
            if (lastMessageAt && (now - lastMessageAt) > STALE_CONNECTION_MS) {
                console.warn('WebSocket stale (no data), retrying later');
                scheduleReconnect();
            }
        }, WATCHDOG_INTERVAL_MS);
    });
}


// socket.addEventListener('error', function (event) {
//     console.log('error');
// });


/**
 * Attach message parsing + UI update handlers to a connected WebSocket.
 */
function init(socket) {
    // Listen for messages
    socket.addEventListener('message', function (event) {
        // console.log('Message from server ', event.data);
        lastMessageAt = Date.now();

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

            const sensorId2 = sensor_data[Display.ID];
            try {
                if (typeof charts !== 'undefined' && charts && Object.prototype.hasOwnProperty.call(charts, sensorId2)) {
                    charts[sensorId2].pushValue(sensor_data);
                } else if (typeof fans !== 'undefined' && fans && Object.prototype.hasOwnProperty.call(fans, sensorId2)) {
                    fans[sensorId2].pushValue(sensor_data);
                } else if (typeof meters !== 'undefined' && meters && Object.prototype.hasOwnProperty.call(meters, sensorId2)) {
                    meters[sensorId2].pushValue(sensor_data);
                }
            } catch (error) {
                console.warn('Error updating UI from sensor data');
            }
        });
    });
}

/**
 * Ensure the on-screen status badge exists in the DOM.
 */
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

/**
 * Update the on-screen status badge.
 * - level: 'ok' hides the badge
 * - level: 'warn' auto-hides after 10s
 * - level: 'error' stays visible until cleared
 */
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
