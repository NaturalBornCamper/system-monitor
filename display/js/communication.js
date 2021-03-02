
let connection;
const RETRY_DELAY = 1000;
let socket;

// connection = setInterval(tryConnection, 500);

function tryConnection() {
    console.log("tryConnection")

    // Create WebSocket connection.
    //const socket = new WebSocket('ws://127.0.0.1:2346');
    //const socket = new WebSocket('ws://192.168.0.65:2346');
    // const socket = new WebSocket('ws://192.168.0.65:2346');
    socket = new WebSocket('ws://localhost:2346');

    socket.addEventListener('error', function (event) {
        console.log('error');
        setTimeout(tryConnection, RETRY_DELAY);
        // clearInterval(connection);
    });

    // Connection opened
    socket.addEventListener('open', function (event) {
        init(socket);

        // socket.send(JSON.stringify({
        //     'action': 'set_sensors',
        //     'requested_sensors': requested_sensors
        // }));
    });
}


// socket.addEventListener('error', function (event) {
//     console.log('error');
// });


function init(socket) {
    // Listen for messages
    socket.addEventListener('message', function (event) {
        console.log('Message from server ', event.data);
    });
    socket.addEventListener('close', function (event) {
        console.log('close');
        setTimeout(tryConnection, RETRY_DELAY);
    });
}


function sensors1(){
    socket.send(JSON.stringify({
        'action': Actions.SET_SENSORS,
        'requested_sensors': [{
            [Sensor.HARDWARE]: 1,
            [Sensor.SUB_HARDWARE]: null,
            [Sensor.SENSOR]: 4,
            [Sensor.DELAY]: 1
        }]
    }));
}
function sensors2(){
    socket.send(JSON.stringify({
        'action': Actions.SET_SENSORS,
        'requested_sensors': [{
            [Sensor.HARDWARE]: 1,
            [Sensor.SUB_HARDWARE]: null,
            [Sensor.SENSOR]: 9,
            [Sensor.DELAY]: 3
        }]
    }));
}