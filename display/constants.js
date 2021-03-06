const MAX_DECIMALS = 1

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

class Display {
    static ID = 'id';
    static LABEL = 'label';
    static WIDTH = 'width';
    static HEIGHT = 'height';
    static VALUE_COUNT = 'value_count';
    static MIN_VALUE = 'min_value';
    static MAX_VALUE = 'max_value';
    static MULTIPLIER = 'multiplier';
    static UNIT = 'unit';
}

// requested_sensors = {}
// requested_sensors[Sensor.HARDWARE] = 4;
// requested_sensors[Sensor.DELAY] = 0.5;
//
// const requested_sensor = {
//     [Sensor.HARDWARE]: 4,
//     Sensor.DELAY: 0.5,
// }
