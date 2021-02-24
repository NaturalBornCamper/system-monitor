class Actions {
    static SET_SENSORS = 0;
    static STOP_BROADCAST = 1;
    static CHANGE_DELAY = 2;
}

class Sensor {
    static HARDWARE = 'hardware';
    static SUB_HARDWARE = 'sub_hardware';
    static SENSOR = 'sensor';
    static DELAY = 'delay';
    static VALUE = 'value';
    static UNIT = "unit";
}

// requested_sensors = {}
// requested_sensors[Sensor.HARDWARE] = 4;
// requested_sensors[Sensor.DELAY] = 0.5;
//
// const requested_sensor = {
//     [Sensor.HARDWARE]: 4,
//     Sensor.DELAY: 0.5,
// }
