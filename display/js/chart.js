/**
 * TODO SSD Load reaches 100% sometimes <- Not sure if I meant to adjust the max value or if it's a bug (Could have been a bug, fixed with latest dlls, check)
 *
 * TODO Add max decimals as option, then add decimal on internet, to have 0.01 MB/s instead of 0.0 MB/s
 * TODO SET METER VALUE COLOR (AND CHART) if min/max values set. If not -> white
 * TODO Still getting all of a sudden a really high download value, not sure if correct
 * TODO Add corners around chart bos, but not rounded, square. (4 L-shaped lines around each corner)
 * TODO Change the grandpapa blue background. Grid is ok, BG is a weird old blue. Maybe a AI-generated futuristic picture?
 * TODO Check what is the ram temperature, if higher than hotspot
 * TODO Make meters look better, maybe a single bar? A rotating meter like a speedometer? Or make into a single bar?
 * TODO Have a log function with a level, so I can leave log calls there and it does nothing in release mode
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
    getColor(value, alpha) {
        let hue = (1 - value) * 120;
        return `hsla(${hue}, 100%, 50%, ${typeof alpha !== 'undefined' ? alpha : CHART_BAR_OPACITY})`;
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
        this.minBarPx = 2;
        this.barAlpha = this.parseAlpha(CHART_BAR_OPACITY);
        this.barAlphaLeft = Math.max(0, Math.min(1, this.barAlpha * 0.05));

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
        label.textContent = options.get(Display.LABEL);
        this.legend.appendChild(label);
        this.legendValue = document.createElement('DIV');
        this.legendValue.classList = 'legend-value';
        this.legendValueText = document.createTextNode('');
        this.legendValue.appendChild(this.legendValueText);
        this.legend.appendChild(this.legendValue);
        this.element.appendChild(this.legend);

        this.barWidth = Math.floor(options.get(Display.WIDTH, CHART_WIDTH) / this.valueCount);
        this.canvas = document.createElement('canvas');
        this.canvas.className = 'chart-canvas';
        this.canvas.width = this.width;
        this.canvas.height = this.height;
        this.canvas.style.width = `${this.width}px`;
        this.canvas.style.height = `${this.height}px`;
        this.elementValues.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
        this.ctx.lineWidth = 1;
        this.ctx.imageSmoothingEnabled = false;

        document.getElementById('charts').appendChild(this.element);
        this.render();
    }

    render() {
        if (!this.ctx) {
            return;
        }

        this.ctx.clearRect(0, 0, this.width, this.height);

        let startIndex = this.valueCount - this.values.length;
        let baselineHeight = this.minBarPx;

        // Draw baseline bars where no data yet
        this.ctx.fillStyle = '#000';
        for (let i = 0; i < startIndex; ++i) {
            let x = i * this.barWidth;
            let y = this.height - baselineHeight;
            this.ctx.fillRect(x, y, this.barWidth, baselineHeight);
        }

        // Draw data bars aligned to the right
        for (let i = 0; i < this.values.length; ++i) {
            let value = this.values[i];
            let ratio = Math.min(1.0, Math.max((value - this.minValue) / this.deltaValues, 0.0));
            let barHeight = Math.max(this.minBarPx, ratio * this.height);
            let x = (startIndex + i) * this.barWidth;
            let y = this.height - barHeight;
            let gradient = this.ctx.createLinearGradient(x, 0, x + this.barWidth, 0);
            gradient.addColorStop(0, this.getColor(ratio, this.barAlphaLeft));
            gradient.addColorStop(1, this.getColor(ratio, this.barAlpha));
            this.ctx.fillStyle = gradient;
            this.ctx.fillRect(x, y, this.barWidth, barHeight);
            this.ctx.strokeStyle = '#000';
            if (barHeight > this.minBarPx) {
                this.ctx.strokeRect(x + 0.5, y + 0.5, this.barWidth - 1, barHeight - 1);
            } else {
                this.ctx.beginPath();
                this.ctx.moveTo(x + 0.5, y + 0.5);
                this.ctx.lineTo(x + 0.5, y + barHeight - 0.5);
                this.ctx.moveTo(x + this.barWidth - 0.5, y + 0.5);
                this.ctx.lineTo(x + this.barWidth - 0.5, y + barHeight - 0.5);
                this.ctx.stroke();
            }
        }
    }

    parseAlpha(alpha) {
        if (typeof alpha === 'number') {
            return Math.max(0, Math.min(1, alpha > 1 ? alpha / 100 : alpha));
        }

        if (typeof alpha !== 'string') {
            return 1;
        }

        let trimmed = alpha.trim();
        if (!trimmed) {
            return 1;
        }

        if (trimmed.endsWith('%')) {
            return Math.max(0, Math.min(1, parseFloat(trimmed) / 100));
        }

        let parsed = parseFloat(trimmed);
        if (!Number.isFinite(parsed)) {
            return 1;
        }

        return Math.max(0, Math.min(1, parsed > 1 ? parsed / 100 : parsed));
    }

    pushValue(sensorData) {
        // return;
        let value = this.multiplier ? this.multiplier * sensorData[Sensor.VALUE] : sensorData[Sensor.VALUE];
        this.values.push(value);
        if (this.values.length > this.valueCount) {
            this.values.shift();
        }
        this.legendValueText.nodeValue = `${value.toFixed(MAX_DECIMALS)} ${this.unit || sensorData[Sensor.UNIT]}`;

        this.render();
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
        label.textContent = options.get(Display.LABEL);
        this.legend.appendChild(label);
        this.fanValue = document.createElement('DIV');
        this.fanValue.classList = 'fan-value';
        this.fanValueText = document.createTextNode('');
        this.fanValue.appendChild(this.fanValueText);
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
        this.fanValueText.nodeValue = `${value.toFixed(0)} ${this.unit || sensorData[Sensor.UNIT]}`;

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
        // return;
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
        label.textContent = `${options.get(Display.LABEL)}:`;
        this.element.appendChild(label);
        this.meterValue = document.createElement('SPAN');
        this.meterValue.classList = 'meter-value';
        this.meterValueText = document.createTextNode('');
        this.meterValue.appendChild(this.meterValueText);
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
        // return;
        let value = this.multiplier ? this.multiplier * sensorData[Sensor.VALUE] : sensorData[Sensor.VALUE];
        this.meterValueText.nodeValue = `${value.toFixed(MAX_DECIMALS)} ${this.unit || sensorData[Sensor.UNIT]}`;

        let ratio = Math.min(1.0, Math.max((value - this.minValue) / this.deltaValues, 0.0));
        this.meterValue.style.color = this.getColor(ratio);
    }
}


function startGraphs() {
    if (typeof chartsSettings === 'undefined' || !Array.isArray(chartsSettings)) {
        return [];
    }
    if (typeof charts === 'undefined' || !charts) {
        return [];
    }

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
    if (typeof fansSettings === 'undefined' || !Array.isArray(fansSettings)) {
        return [];
    }
    if (typeof fans === 'undefined' || !fans) {
        return [];
    }

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
    if (typeof metersSettings === 'undefined' || !Array.isArray(metersSettings)) {
        return [];
    }
    if (typeof meters === 'undefined' || !meters) {
        return [];
    }

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
