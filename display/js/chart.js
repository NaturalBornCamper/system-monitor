/**
 * TODO SSD Load reaches 100% sometimes <- Not sure if I meant to adjust the max value or if it's a bug (Could have been a bug, fixed with latest dlls, check)
 *
 * TODO Add max decimals as option, then add decimal on internet, to have 0.01 MB/s instead of 0.0 MB/s
 * TODO SET METER VALUE COLOR (AND CHART) if min/max values set. If not -> white
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
        let hue = ((1 - value) * 120).toString(10);
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
        this.values = [];
        this.height = options.get(Display.HEIGHT, CHART_HEIGHT);
        this.valueCount = options.get(Display.VALUE_COUNT, CHART_VALUE_COUNT);
        this.minValue = options.get(Display.MIN_VALUE);
        this.maxValue = options.get(Display.MAX_VALUE);
        this.multiplier = options.get(Display.MULTIPLIER);
        this.unit = options.get(Display.UNIT);

        // Create main graph node
        this.element = document.createElement('DIV');
        this.element.className = 'chart chart-histogram';
        this.element.id = options.get(Display.ID);
        this.element.style.height = `${this.height}px`;
        this.element.style.width = `${options.get(Display.WIDTH, CHART_WIDTH)}px`;

        // Create values container
        this.elementValues = document.createElement('DIV');
        this.elementValues.className = 'chart-values';
        this.element.appendChild(this.elementValues);

        // Create legend
        this.legend = document.createElement('DIV');
        this.legend.className = 'chart-legend';
        let node = document.createElement('DIV');
        node.classList = 'legend-label';
        node.innerHTML = options.get(Display.LABEL);
        this.legend.appendChild(node);
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
        let value = this.multiplier ? this.multiplier * sensorData[Sensor.VALUE] : sensorData[Sensor.VALUE];
        this.values.push(value);
        if (this.values.length > this.valueCount) {
            this.values.shift();
        }
        this.legendValue.innerHTML = `${value.toFixed(MAX_DECIMALS)} ${this.unit || sensorData[Sensor.UNIT]}`;

        // console.log(this.values);
        let x = this.valueCount - 1;

        for (let i = this.values.length - 1; i >= 0; --i) {
            let ratio = Math.min(1.0, Math.max(this.values[i] / this.maxValue, 0.0));
            this.elementValues.children[x].style.height = `${Math.max(0.05, ratio) * this.height}px`;
            this.elementValues.children[x].style.backgroundColor = this.getColor(ratio);
            --x;
        }

        // let chart = this;
        // this.values.forEach(function (value, index) {
        //     if (typeof chart.elementValues.children[x] === 'undefined') {
        //         return console.error(`Chart child doesn't exist: ${x}`)
        //     }
        //     let ratio = value / chart.maxValue;
        //     chart.elementValues.children[x].style.height = `${ratio * chart.height}px`;
        //     chart.elementValues.children[x].style.backgroundColor = chart.getColor(ratio);
        //     --x;
        // });
    }
}


class Meter extends BaseUiElement {
    constructor(options) {
        super()
        this.multiplier = options.get(Display.MULTIPLIER);
        this.unit = options.get(Display.UNIT);

        // Create main meter node
        this.element = document.createElement('DIV');
        this.element.className = 'meter';
        this.element.id = options.get(Display.ID);

        // Create labeyl and value
        let node = document.createElement('SPAN');
        node.classList = 'meter-label';
        node.innerHTML = `${options.get(Display.LABEL)}:`;
        this.element.appendChild(node);
        this.meterValue = document.createElement('SPAN');
        this.meterValue.classList = 'meter-value';
        this.element.appendChild(this.meterValue);

        document.getElementById('meters').appendChild(this.element);
    }

    // Calculates green to red color with a value from 0 to 1
    getColor(value) {
        let hue = ((1 - value) * 120).toString(10);
        return `hsl(${hue}, 100%, 50%)`;
    }

    pushValue(sensorData) {
        let value = this.multiplier ? this.multiplier * sensorData[Sensor.VALUE] : sensorData[Sensor.VALUE];
        this.meterValue.innerHTML = `${value.toFixed(MAX_DECIMALS)} ${this.unit || sensorData[Sensor.UNIT]}`;

        // NOT SET YET
        // let ratio = value / this.maxValue;
        // this.meterValue.style.color = this.getColor(ratio);
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