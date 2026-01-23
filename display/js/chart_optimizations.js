/**
 * TODO SSD Load reaches 100% sometimes <- Not sure if I meant to adjust the max value or if it's a bug (Could have been a bug, fixed with latest dlls, check)
 *
 * TODO Add max decimals as option, then add decimal on internet, to have 0.01 MB/s instead of 0.0 MB/s
 * TODO SET METER VALUE COLOR (AND CHART) if min/max values set. If not -> white
 * TODO Still getting all of a sudden a really high download value, not sure if correct
 * TODO find a way to optimize interface, fans are glitchy
 */

Object.prototype.get = function (property, defaultValue) {
    if (this.hasOwnProperty(property)) {
        return this[property];
    }
    if (typeof defaultValue !== 'undefined') {
        return defaultValue;
    }
    return null;
}


class BaseUiElement {
    // getCalculatedHeight(value) {
    //     return Math.floor(value / this.maxValue * this.height);
    // }

    // Calculates green to red color with a value from 0 to 1
    getColor(value) {
        let hue = (1 - value) * 120;
        return `hsla(${hue}, 100%, 50%, ${CHART_BAR_OPACITY})`;
    }

    // round(value){
    //     return value.toLocaleString('en-US', {
    //         minimumFractionDigits: 2,
    //         maximumFractionDigits: 4
    //     });
    // }
}


class Chart extends BaseUiElement {
    constructor(options) {
        super()
        // return;
        this.values = [];
        this.width = options.get(Display.WIDTH, CHART_WIDTH);
        this.height = options.get(Display.HEIGHT, CHART_HEIGHT);
        this.valueCount = options.get(Display.VALUE_COUNT, CHART_VALUE_COUNT);
        this.minValue = options.get(Display.MIN_VALUE, DEFAULT_MIN_VALUE);
        this.maxValue = options.get(Display.MAX_VALUE, DEFAULT_MAX_VALUE);
        this.deltaValues = this.maxValue - this.minValue;
        this.multiplier = options.get(Display.MULTIPLIER);
        this.unit = options.get(Display.UNIT);

        // Create main graph node
        this.element = document.createElement('DIV');
        this.element.className = 'chart chart-histogram';
        this.element.id = options.get(Display.ID);
        this.element.style.height = `${this.height}px`;
        this.element.style.width = `${this.width}px`;

        // Create values container
        this.elementValues = document.createElement('DIV');
        this.elementValues.className = 'chart-values';
        this.element.appendChild(this.elementValues);

        // Create legend
        this.legend = document.createElement('DIV');
        this.legend.className = 'chart-legend';
        let label = document.createElement('DIV');
        label.classList = 'legend-label';
        label.innerHTML = options.get(Display.LABEL);
        this.legend.appendChild(label);
        this.legendValue = document.createElement('DIV');
        this.legendValue.classList = 'legend-value';
        this.legend.appendChild(this.legendValue);
        this.element.appendChild(this.legend);

        let createdValue;
        let chart_value_width = Math.floor(options.get(Display.WIDTH, CHART_WIDTH) / this.valueCount);
        for (let i = 0; i < this.valueCount; ++i) {
            createdValue = document.createElement('DIV');
            createdValue.className = 'chart-value chart-histogram-bar';
            createdValue.style.height = `0`;
            // createdValue.style.height = `${this.getCalculatedHeight(i)}px`;
            createdValue.style.width = `${chart_value_width}px`;
            createdValue.style.marginBottom = `-${this.height}px`;
            this.elementValues.appendChild(createdValue);
        }

        document.getElementById('charts').appendChild(this.element);
    }

    pushValue(sensorData) {
        // return;
        let value = this.multiplier ? this.multiplier * sensorData[Sensor.VALUE] : sensorData[Sensor.VALUE];
        this.values.push(value);
        if (this.values.length > this.valueCount) {
            this.values.shift();
        }
        this.legendValue.innerHTML = `${value.toFixed(MAX_DECIMALS)} ${this.unit || sensorData[Sensor.UNIT]}`;

        // console.log(this.values);
        let reverseCounter = this.valueCount - 1;

        // Loop in all chart bar divs and set their new length and colors as the bars get pushed left
        for (let i = this.values.length - 1; i >= 0; --i) {
            let ratio = Math.min(1.0, Math.max((this.values[i] - this.minValue) / this.deltaValues, 0.0));
            this.elementValues.children[reverseCounter].style.height = `${Math.max(0.05, ratio) * this.height}px`;
            this.elementValues.children[reverseCounter].style.backgroundColor = this.getColor(ratio);
            --reverseCounter;
        }
    }
}


class Fan extends BaseUiElement {
    constructor(options) {
        super()
        this.multiplier = options.get(Display.MULTIPLIER);
        this.unit = options.get(Display.UNIT);
        this.minRPM = options.get(Display.MIN_VALUE, DEFAULT_MIN_VALUE);
        this.maxRPM = options.get(Display.MAX_VALUE, DEFAULT_MAX_VALUE);
        this.deltaRPM = this.maxRPM - this.minRPM;
        this.deltaFanSpeed = FAN_MAX_SPEED - FAN_MIN_SPEED;
        this.fanAngle = 0;
        this.fanLastTimestamp = 0;
        this.fanLastDuration = 0;

        // Create main meter node
        this.element = document.createElement('DIV');
        this.element.className = 'fan';
        this.element.id = options.get(Display.ID);

        this.fanBlades = document.createElement('IMG');
        this.fanBlades.classList = 'fan-blades';
        this.fanBlades.src = "images/fan_and_frame8.png";
        this.element.appendChild(this.fanBlades);

        // Create label and value
        this.legend = document.createElement('DIV');
        this.legend.className = 'fan-legend';
        let label = document.createElement('DIV');
        label.classList = 'fan-label';
        label.innerHTML = options.get(Display.LABEL);
        this.legend.appendChild(label);
        this.fanValue = document.createElement('DIV');
        this.fanValue.classList = 'fan-value';
        this.legend.appendChild(this.fanValue);
        this.element.appendChild(this.legend);

        document.getElementById('fans').appendChild(this.element);
    }

    // Calculates green to red color with a value from 0 to 1
    // TODO Chat GPT says to not calculate and change to string every time. Maybe round the value to one decimal and have them all pre-calculated?
    getColor(value) {
        let hue = (1 - value) * 120;
        return `hsl(${hue}, 100%, 50%)`;
    }

    pushValue(sensorData) {
        let value = this.multiplier ? this.multiplier * sensorData[Sensor.VALUE] : sensorData[Sensor.VALUE];
        // value = Math.floor(Math.random() * (this.maxRPM - this.minRPM + 1) + this.minRPM);
        this.fanValue.innerHTML = `${value.toFixed(0)} ${this.unit || sensorData[Sensor.UNIT]}`;

        let ratio = Math.min(1.0, Math.max((value - this.minRPM) / this.deltaRPM, 0.0));
        this.updateFanSpeed(this.deltaFanSpeed * ratio + FAN_MIN_SPEED);
        this.fanValue.style.color = this.getColor(ratio);
    }

    updateFanSpeed(newSpeed) {
        // If the speed doesn't change much (less than 0.1), don't update speed to avoid hiccups on RPi0
        let duration = parseFloat((50 / newSpeed).toFixed(1));
        if (this.fanLastDuration === duration) {
            return;
        }

        let currentTimestamp = new Date() / 1000;
        let timestampDifference = currentTimestamp - this.fanLastTimestamp;

        // Disable rotation and force update
        this.fanBlades.classList.remove("enable-rotate");
        this.fanBlades.offsetHeight;

        if (!this.fanLastDuration && duration) {
            this.fanBlades.style.transform = "";
        } else {
            this.fanAngle += (timestampDifference % this.fanLastDuration) / this.fanLastDuration;
        }

        if (duration) {
            this.fanBlades.style.animationDuration = `${duration}s`;
            this.fanBlades.style.animationDelay = `${-duration * this.fanAngle}s`;
            this.fanBlades.classList.add("enable-rotate");
        } else {
            this.fanBlades.style.transform = `rotate(${360 * this.fanAngle}deg)`;
        }

        this.fanAngle -= this.fanAngle | 0; //use fractional part only
        this.fanLastTimestamp = currentTimestamp;
        this.fanLastDuration = duration;
    }
}


class Meter extends BaseUiElement {
    constructor(options) {
        super()
        return;
        this.multiplier = options.get(Display.MULTIPLIER);
        this.unit = options.get(Display.UNIT);
        this.minValue = options.get(Display.MIN_VALUE, DEFAULT_MIN_VALUE);
        this.maxValue = options.get(Display.MAX_VALUE, DEFAULT_MAX_VALUE);
        this.deltaValues = this.maxValue - this.minValue;

        // Create main meter node
        this.element = document.createElement('DIV');
        this.element.className = 'meter';
        this.element.id = options.get(Display.ID);

        // Create label and value
        let label = document.createElement('SPAN');
        label.classList = 'meter-label';
        label.innerHTML = `${options.get(Display.LABEL)}:`;
        this.element.appendChild(label);
        this.meterValue = document.createElement('SPAN');
        this.meterValue.classList = 'meter-value';
        this.element.appendChild(this.meterValue);

        // document.getElementById('fans').appendChild(this.element);
        document.getElementById('meters').appendChild(this.element);
    }

    // Calculates green to red color with a value from 0 to 1
    getColor(value) {
        let hue = (1 - value) * 120;
        return `hsl(${hue}, 100%, 50%)`;
    }

    pushValue(sensorData) {
        return;
        let value = this.multiplier ? this.multiplier * sensorData[Sensor.VALUE] : sensorData[Sensor.VALUE];
        this.meterValue.innerHTML = `${value.toFixed(MAX_DECIMALS)} ${this.unit || sensorData[Sensor.UNIT]}`;

        let ratio = Math.min(1.0, Math.max((value - this.minValue) / this.deltaValues, 0.0));
        this.meterValue.style.color = this.getColor(ratio);
    }
}


function startGraphs() {
    let requested_sensors = [];

    chartsSettings.forEach(function (chartSettings, index) {
        // Checks if chart already exists, not sure if it should be cleared when it exists (computer restarts)
        if (!charts[chartSettings[Display.ID]])
            charts[chartSettings[Display.ID]] = new Chart(chartSettings);

        requested_sensors.push({
            [Display.ID]: chartSettings[Display.ID],
            [Display.LABEL]: chartSettings[Display.LABEL],
            [Sensor.HARDWARE]: chartSettings[Sensor.HARDWARE],
            [Sensor.SUB_HARDWARE]: chartSettings[Sensor.SUB_HARDWARE],
            [Sensor.SENSOR]: chartSettings[Sensor.SENSOR],
            [Sensor.DELAY]: chartSettings[Sensor.DELAY]
        });
    });

    console.log(requested_sensors);
    return requested_sensors;
}


function startFans() {
    let requested_sensors = [];

    fansSettings.forEach(function (fanSettings, index) {
        // Checks if fan already exists, not sure if it should be cleared when it exists (computer restarts)
        if (!fans[fanSettings[Display.ID]]) {
            fans[fanSettings[Display.ID]] = new Fan(fanSettings);
        }

        requested_sensors.push({
            [Display.ID]: fanSettings[Display.ID],
            [Display.LABEL]: fanSettings[Display.LABEL],
            [Sensor.HARDWARE]: fanSettings[Sensor.HARDWARE],
            [Sensor.SUB_HARDWARE]: fanSettings[Sensor.SUB_HARDWARE],
            [Sensor.SENSOR]: fanSettings[Sensor.SENSOR],
            [Sensor.DELAY]: fanSettings[Sensor.DELAY]
        });
    });

    console.log(requested_sensors);
    return requested_sensors;
}


function startMeters() {
    let requested_sensors = [];

    metersSettings.forEach(function (meterSettings, index) {
        // Checks if meter already exists, not sure if it should be cleared when it exists (computer restarts)
        if (!meters[meterSettings[Display.ID]])
            meters[meterSettings[Display.ID]] = new Meter(meterSettings);

        requested_sensors.push({
            [Display.ID]: meterSettings[Display.ID],
            [Display.LABEL]: meterSettings[Display.LABEL],
            [Sensor.HARDWARE]: meterSettings[Sensor.HARDWARE],
            [Sensor.SUB_HARDWARE]: meterSettings[Sensor.SUB_HARDWARE],
            [Sensor.SENSOR]: meterSettings[Sensor.SENSOR],
            [Sensor.DELAY]: meterSettings[Sensor.DELAY]
        });
    });

    console.log(requested_sensors);
    return requested_sensors;
}