class Chart {
    constructor(options) {
        this.values = [];
        // this.id = options.id;
        // this.width = options.width;
        this.height = options.height;
        this.valueCount = options.valueCount;
        this.minValue = options.minValue;
        this.maxValue = options.maxValue;
        this.multiplier = (typeof options.multiplier !== 'undefined') ? options.multiplier : null;
        this.unit = (typeof options.unit !== 'undefined') ? options.unit : null;

        // Create main graph node
        this.element = document.createElement('DIV');
        this.element.className = 'chart chart-histogram';
        this.element.id = options.id;
        this.element.style.height = `${options.height}px`;
        this.element.style.width = `${options.width}px`;

        // Create values container
        this.elementValues = document.createElement('DIV');
        this.elementValues.className = 'chart-values';
        this.element.appendChild(this.elementValues);

        // Create legend
        this.legend = document.createElement('DIV');
        this.legend.className = 'chart-legend';
        let node = document.createElement('DIV');
        node.classList = 'legend-label';
        node.innerHTML = options.label;
        this.legend.appendChild(node);
        this.legendValue = document.createElement('DIV');
        this.legendValue.classList = 'legend-value';
        this.legend.appendChild(this.legendValue);
        this.element.appendChild(this.legend);

        let createdValue;
        for (let i = 0; i < options.valueCount; ++i) {
            createdValue = document.createElement('DIV');
            createdValue.className = 'chart-value chart-histogram-bar';
            createdValue.style.height = `0`;
            // createdValue.style.height = `${this.getCalculatedHeight(i)}px`;
            createdValue.style.width = `${CHART_VALUE_WIDTH}px`;
            createdValue.style.marginBottom = `-${options.height}px`;
            this.elementValues.appendChild(createdValue);
        }

        document.getElementById('charts').appendChild(this.element);
    }

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
            let ratio = this.values[i] / this.maxValue;
            this.elementValues.children[x].style.height = `${ratio * this.height}px`;
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


function startGraphs() {
    chartsSettings.forEach(function (chartSettings, index) {
        let date = new Date();
        // let identifier = `${date.getTime()}${date.getMilliseconds()}`;
        charts[chartSettings[Display.ID]] = new Chart({
            id: chartSettings[Display.ID],
            label: chartSettings[Display.LABEL],
            width: chartSettings[Display.WIDTH],
            height: chartSettings[Display.HEIGHT],
            valueCount: chartSettings[Display.VALUE_COUNT],
            minValue: chartSettings[Display.MIN_VALUE],
            maxValue: chartSettings[Display.MAX_VALUE],
            multiplier: chartSettings.hasOwnProperty(Display.MULTIPLIER) ? chartSettings[Display.MULTIPLIER] : null,
            unit: chartSettings.hasOwnProperty(Display.UNIT) ? chartSettings[Display.UNIT] : null,
        });

        requested_sensors.push({
            [Display.ID]: chartSettings[Display.ID],
            [Display.LABEL]: chartSettings[Display.LABEL],
            [Sensor.HARDWARE]: chartSettings[Sensor.HARDWARE],
            [Sensor.SUB_HARDWARE]: chartSettings[Sensor.SUB_HARDWARE],
            [Sensor.SENSOR]: chartSettings[Sensor.SENSOR],
            [Sensor.DELAY]: chartSettings[Sensor.DELAY]
        });
        console.log(requested_sensors);

        socket.send(JSON.stringify({
            'action': Actions.SET_SENSORS,
            'requested_sensors': requested_sensors
        }));
    });
}