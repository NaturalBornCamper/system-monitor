let connection;
const RETRY_DELAY = 1000;
let socket;

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
        setTimeout(tryConnection, RETRY_DELAY);
    });

    // Connection opened
    socket.addEventListener('open', function (event) {
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
        data = JSON.parse(event.data);

        data.forEach(function (sensor_data, index) {
            // console.log(sensor_data)

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
        setTimeout(tryConnection, RETRY_DELAY);
    });
}