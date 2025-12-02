class NoiseGenerator {
    constructor() {
        this.audioContext = null;
        this.isPlaying = false;
        this.masterFilter = null;

        this.soundTypes = [
            'white', 'pink', 'brown',
            'sine', 'triangle', 'square', 'sawtooth'
        ];

        this.nodes = {};
        this.volumes = {};

        this.soundTypes.forEach(type => {
            this.nodes[type] = { gain: null, source: null };
            this.volumes[type] = 0;
        });

        this.filterSettings = {
            frequency: 20000,
            q: 0
        };

        this.initUI();
    }

    initUI() {
        this.playBtn = document.getElementById('play-btn');
        this.iconPlay = this.playBtn.querySelector('.icon-play');
        this.iconPause = this.playBtn.querySelector('.icon-pause');

        this.playBtn.addEventListener('click', () => this.togglePlay());

        // Volume sliders
        this.soundTypes.forEach(type => {
            const id = type.includes('noise') ? type : `${type}-wave`;
            // Handle legacy IDs for noise vs new IDs for waves
            const elementId = ['white', 'pink', 'brown'].includes(type) ? `${type}-noise` : `${type}-wave`;

            const slider = document.getElementById(elementId);
            if (slider) {
                slider.addEventListener('input', (e) => {
                    this.setVolume(type, parseFloat(e.target.value));
                });
            }
        });

        // Filter controls
        const freqSlider = document.getElementById('filter-freq');
        const qSlider = document.getElementById('filter-q');

        if (freqSlider) {
            freqSlider.addEventListener('input', (e) => {
                this.setFilterFrequency(parseFloat(e.target.value));
            });
        }

        if (qSlider) {
            qSlider.addEventListener('input', (e) => {
                this.setFilterQ(parseFloat(e.target.value));
            });
        }
    }

    async initAudio() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }

        if (this.audioContext.state === 'suspended') {
            await this.audioContext.resume();
        }
    }

    createWhiteNoiseBuffer() {
        const bufferSize = 2 * this.audioContext.sampleRate;
        const buffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate);
        const output = buffer.getChannelData(0);

        for (let i = 0; i < bufferSize; i++) {
            output[i] = Math.random() * 2 - 1;
        }
        return buffer;
    }

    createPinkNoiseBuffer() {
        const bufferSize = 2 * this.audioContext.sampleRate;
        const buffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate);
        const output = buffer.getChannelData(0);
        let b0, b1, b2, b3, b4, b5, b6;
        b0 = b1 = b2 = b3 = b4 = b5 = b6 = 0.0;

        for (let i = 0; i < bufferSize; i++) {
            const white = Math.random() * 2 - 1;
            b0 = 0.99886 * b0 + white * 0.0555179;
            b1 = 0.99332 * b1 + white * 0.0750759;
            b2 = 0.96900 * b2 + white * 0.1538520;
            b3 = 0.86650 * b3 + white * 0.3104856;
            b4 = 0.55000 * b4 + white * 0.5329522;
            b5 = -0.7616 * b5 - white * 0.0168980;
            output[i] = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362;
            output[i] *= 0.11; // (roughly) compensate for gain
            b6 = white * 0.115926;
        }
        return buffer;
    }

    createBrownNoiseBuffer() {
        const bufferSize = 2 * this.audioContext.sampleRate;
        const buffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate);
        const output = buffer.getChannelData(0);
        let lastOut = 0.0;

        for (let i = 0; i < bufferSize; i++) {
            const white = Math.random() * 2 - 1;
            output[i] = (lastOut + (0.02 * white)) / 1.02;
            lastOut = output[i];
            output[i] *= 3.5; // (roughly) compensate for gain
        }
        return buffer;
    }

    setupSource(type) {
        const gainNode = this.audioContext.createGain();
        gainNode.gain.value = this.volumes[type];
        gainNode.connect(this.masterFilter);
        this.nodes[type].gain = gainNode;

        let source;
        if (['sine', 'triangle', 'square', 'sawtooth'].includes(type)) {
            source = this.audioContext.createOscillator();
            source.type = type;
            // Set a default low frequency for ambient drone textures
            // Different octaves for different waves to make it interesting
            if (type === 'sine') source.frequency.value = 110;
            if (type === 'triangle') source.frequency.value = 110;
            if (type === 'square') source.frequency.value = 55;
            if (type === 'sawtooth') source.frequency.value = 55;
        } else {
            source = this.audioContext.createBufferSource();
            if (type === 'white') source.buffer = this.createWhiteNoiseBuffer();
            if (type === 'pink') source.buffer = this.createPinkNoiseBuffer();
            if (type === 'brown') source.buffer = this.createBrownNoiseBuffer();
            source.loop = true;
        }

        source.connect(gainNode);
        source.start();
        this.nodes[type].source = source;
    }

    start() {
        this.initAudio().then(() => {
            // Create Master Filter
            this.masterFilter = this.audioContext.createBiquadFilter();
            this.masterFilter.type = 'lowpass';
            this.masterFilter.frequency.value = this.filterSettings.frequency;
            this.masterFilter.Q.value = this.filterSettings.q;
            this.masterFilter.connect(this.audioContext.destination);

            this.soundTypes.forEach(type => {
                this.setupSource(type);
            });

            this.isPlaying = true;
            this.updatePlayButton();
        });
    }

    stop() {
        this.soundTypes.forEach(type => {
            if (this.nodes[type].source) {
                this.nodes[type].source.stop();
                this.nodes[type].source.disconnect();
                this.nodes[type].source = null;
            }
            if (this.nodes[type].gain) {
                this.nodes[type].gain.disconnect();
                this.nodes[type].gain = null;
            }
        });

        if (this.masterFilter) {
            this.masterFilter.disconnect();
            this.masterFilter = null;
        }

        this.isPlaying = false;
        this.updatePlayButton();
    }

    togglePlay() {
        if (this.isPlaying) {
            this.stop();
        } else {
            this.start();
        }
    }

    setVolume(type, value) {
        this.volumes[type] = value;
        if (this.nodes[type].gain) {
            this.nodes[type].gain.gain.setTargetAtTime(value, this.audioContext.currentTime, 0.01);
        }
    }

    setFilterFrequency(val) {
        this.filterSettings.frequency = val;
        if (this.masterFilter) {
            this.masterFilter.frequency.setTargetAtTime(val, this.audioContext.currentTime, 0.1);
        }
    }

    setFilterQ(val) {
        this.filterSettings.q = val;
        if (this.masterFilter) {
            this.masterFilter.Q.setTargetAtTime(val, this.audioContext.currentTime, 0.1);
        }
    }

    updatePlayButton() {
        if (this.isPlaying) {
            this.iconPlay.style.display = 'none';
            this.iconPause.style.display = 'block';
        } else {
            this.iconPlay.style.display = 'block';
            this.iconPause.style.display = 'none';
        }
    }
}

// Initialize
window.addEventListener('DOMContentLoaded', () => {
    new NoiseGenerator();
});
